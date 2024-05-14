# Predicting Housing Prices using Apache Airflow and Docker

This project aims to predict housing prices using machine learning techniques. Apache Airflow orchestrates the data pipeline, while Docker ensures reproducibility and easy deployment across different environments. 

# Getting Started

1. Clone this repository to your local machine.
2. Install Docker if you haven't already.
3. Configure the Dockerfile and docker-compose.yml files according to your needs.
4. Build the Docker image using ```docker-compose build```.
5. Start the Docker containers using ```docker-compose up```.
6. Access the Airflow web interface at http://localhost:8080 in your browser.
7. Explore the DAGs (Directed Acyclic Graphs) provided in the dags directory.
8. Run or schedule the DAGs to execute the housing price prediction pipeline.

# Project Structure
The project directory is organized as follows:

```
housing
├── dags                    
│   └── pipeline.py         # DAG 1 definition
├── data
│   └── properties.csv
├── dockerfiles              
│   └── Dockerfile          # Configuration file for building the Docker image
├── logs
│   ├── dag_id
│   │   └── task_id         # Tasks
│   │       └── aquire_data 
│   │       └── ...
│   │       └── store_data
│   ├── dag_proc
│   │   └── ...
│   └── scheduler
│       └── ...
└── docker-compose.yml      # Configuration file for defining Docker services
```

# Visualization
https://public.tableau.com/authoring/LosAngelesCountyHousingVisualization/AvgPricePerHouse#3
