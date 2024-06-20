from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, PrimaryKeyConstraint, UniqueConstraint, exc, text
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import re
import requests
from bs4 import BeautifulSoup

# Define the database connection URL (replace with your actual database details)
DATABASE_URL = 'mysql+pymysql://root@localhost/worker_publication'

#Taking url for web-site
url = 'https://pers.uz.zgora.pl/publikacje-instytuty/095028'
response = requests.get(url)
html_content = response.content


soup = BeautifulSoup(html_content, 'html.parser')

# Create an engine and sessionmaker
engine = create_engine(DATABASE_URL, echo=True)  # Set echo=True for debug output
Session = sessionmaker(bind=engine)
session = Session()

# Create a base class for declarative table definitions
Base = declarative_base()
#Defining workers table

class Worker(Base):
    __tablename__ = 'Workers'

    worker_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)

# Define the Publications table
class Publication(Base):
    __tablename__ = 'Publications'

    pub_id = Column(Integer, primary_key=True)
    pub_name = Column(String(255), unique=True, nullable=False)

workers_publication = Table('workers_publication', Base.metadata,
    Column('worker_id', Integer, ForeignKey('Workers.worker_id')),
    Column('pub_id', Integer, ForeignKey('Publications.pub_id')),
    PrimaryKeyConstraint('worker_id', 'pub_id')
)
# Create tables if they do not exist
Base.metadata.create_all(engine)

def extract_names_and_surnames():
# Find the table with Names and surnames of workers
    table = soup.find('div', class_='table-responsive').find('table')
    profile_urls = []

    if table is None:
        print("Table not found. Please check the class name and HTML structure.")
    else:
    # Initialize lists to store full name
        first_names = []
        surnames = []

        for row in table.find_all('tr')[1:]:  # Skip the header row
        # Find all columns in the row
            cols = row.find_all('td')
            profile_urls.append(row.find('a')['href'])
        
        # Check if there are enough columns to extract name and surname
            if len(cols) >= 1:

                full_name = cols[0].get_text(strip=True)
            
            # Split the full name by spaces and filter out titles
                name_parts = full_name.split()
                name_surname = ' '.join(part for part in name_parts if not part.lower() in ["dr", "hab.", "inż.", "prof.", "zw.", "hab", "hab.", "inz.", "inz"])
            
            # Split the name_surname into first name and surname
                parts = name_surname.split()
                if len(parts) >= 2:
                    first_name = parts[0]
                    surname = ' '.join(parts[1:])
                
                    # Append to respective lists
                    first_names.append(first_name)
                    surnames.append(surname)
    
    return first_names, surnames, profile_urls      

# Function to add publications from a text file
def add_publications_from_text_file(filename):
    # Read the file and process each line
    with open(filename, 'r', encoding='utf-8') as file:
        index = 1
        for line in file:
            # Remove leading and trailing whitespace
            line = line.strip()
            
            # Skip empty lines
            if line == '':
                continue
            
            # Check if the line starts with an index pattern like '1)', '2)', etc.
            match = re.match(r'^\d+\)', line)
            if match:
                # If there's an index pattern, skip it and continue to the next line
                continue
            
            # Check if the publication already exists in the database
            publication = session.query(Publication).filter_by(pub_name=line).first()
            if publication:
                continue
            
            # Create a new Publication object and add it to the session
            new_publication = Publication(pub_name=line)
            session.add(new_publication)
            
            index += 1
    
    # Commit changes to the database
    session.commit()

def add_workers_to_database(names, surnames):
    # Iterate over the lists of names and surnames
    for name, surname in zip(names, surnames):
        # Create a Worker object
        worker = Worker(name=name, surname=surname)
        
        # Add the worker object to the session
        session.add(worker)
    
    # Commit the session to save changes to the database
    session.commit()
 
def read_text_document(filename):
    # Read the text document
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Initialize variables
    entries = []
    current_entry = None

    # Iterate through each line
    for line in lines:
        line = line.strip()
        if line.endswith(')'):
            if current_entry:
                entries.append(current_entry)
                process_entries(current_entry)
            # Found a new index entry
            index_str = line[:-1].strip()
            try:
                index = int(index_str)  # Extract the index number
            except ValueError:
                # Handle cases where the index is not a valid integer
                continue  # Skip this line if index extraction fails
            
            current_entry = {
                'id': index,
                'names': []
            }
        elif line:
            # Add line to current entry's names list
            if current_entry:
                current_entry['names'].append(line)
    
    if current_entry:
        entries.append(current_entry)
        process_entries(current_entry)

def process_entries(entry):
    worker_id = entry['id']
    names = entry['names']
    
    try:
        for name in names:
            publication = session.query(Publication).filter_by(pub_name=name).first()
            if publication:
                pub_id = publication.pub_id
            else:
                # If publication does not exist, create it
                new_publication = Publication(pub_name=name)
                session.add(new_publication)
                session.commit()  # Commit to get pub_id
                pub_id = new_publication.pub_id
            
            # Create workers_publication entry
            session.execute(workers_publication.insert().values(worker_id=worker_id, pub_id=pub_id))
        
        # Commit changes to the database
        session.commit()
    
    except exc.SQLAlchemyError as e:
        session.rollback()  # Rollback changes on error
        print(f"SQLAlchemy error occurred: {e}")
    
    except Exception as e:
        session.rollback()  # Rollback changes on error
        print(f"Unexpected error occurred: {e}")

def generate_sql_query(worker_id):
    sql_query = text("""
        SELECT p.pub_name, w.worker_id
        FROM publications p
        JOIN workers_publication w ON p.pub_id = w.pub_id
        WHERE w.worker_id = :worker_id
    """)
    return sql_query.bindparams(worker_id=worker_id)

first_names, surnames, profile_urls = extract_names_and_surnames()

filename = 'publication_list.txt'

add_workers_to_database(first_names, surnames)

add_publications_from_text_file(filename) 

read_text_document(filename)

worker_id = 1  # ID of worker to get his listof publications
sql_query = generate_sql_query(worker_id)

# Execute the SQL query and fetch results
result = session.execute(sql_query)
for row in result:
    print(f"Publication Name: {row[0]}, Worker ID: {row[1]}")
# Close the session
session.close()
