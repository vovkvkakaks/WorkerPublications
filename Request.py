import requests
from bs4 import BeautifulSoup
import pandas as pd


url = 'https://pers.uz.zgora.pl/publikacje-instytuty/095028'
response = requests.get(url)
html_content = response.content


soup = BeautifulSoup(html_content, 'html.parser')

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

def extract_publications(urls):
    publication_list = []
    for url in urls:
        try:
            response = requests.get(url)
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
            
                b_tags = soup.find_all('b')
            
                # Initialize an empty list to store the extracted data
                extracted_data = []
            
                # Loop through each <b> tag and extract its text content
                for b_tag in b_tags:
                    extracted_data.append(b_tag.text.strip())

                publication_list.append(extracted_data)
            else:
                # If the request was not successful, append None to indicate failure
                publication_list.append(None)
                print(f"Error: Unable to fetch data from {url}")
        except Exception as e:
            # If an exception occurs, append None and print the error
            publication_list.append(None)
            print(f"Error: {e}")
    return publication_list 
    
first_names, surnames, profile_urls  = extract_names_and_surnames()

publication_urls = []
for url in profile_urls:
    publication_urls.append(url + '?from=1960&to=2025') #getting url for each worker with publications from 2017 to 2024

pub_list = extract_publications(publication_urls)


#Storing info about publications inside of txt doc

with open('publication_list.txt', 'w', encoding='utf-8', errors='ignore') as file:
    # Initialize a counter
    index = 1
    
    # Iterate over each item in pub_list
    for extracted_data_list in pub_list:
        # Write the index and increment it for the next iteration
        file.write(f"{index})\n")
        index += 1
        
        # Write each element of the extracted_data list on a new line
        for data in extracted_data_list:
            file.write(f"{data}\n")
        
        # Add a newline character to separate the extracted_data lists by paragraphs
        file.write('\n')



