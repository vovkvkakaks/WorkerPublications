
CREATE TABLE Workers (
    worker_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    surname VARCHAR(255) NOT NULL
);


CREATE TABLE Publications (
    pub_id INT AUTO_INCREMENT PRIMARY KEY,
    pub_name VARCHAR(255) UNIQUE
);


CREATE or replace TABLE workers_publication (
    worker_id INT,
    pub_id INT,
    FOREIGN KEY (worker_id) REFERENCES Workers(worker_id),
    FOREIGN KEY (pub_id) REFERENCES Publications(pub_id)
);

