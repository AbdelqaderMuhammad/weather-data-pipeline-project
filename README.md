# Data Engineering Pipeline

## Overview

This project is a data engineering pipeline designed to fetch weather data from
the [OpenWeather API](https://openweathermap.org/api), validate and process the data, and store it in a PostgreSQL
database. The pipeline also performs data transformations and validations using dbt (data build tool) and is
orchestrated with Prefect for scheduling and monitoring.

---

## Features

- **Data Ingestion**: Fetch real-time weather data from the OpenWeather API using Python.
- **Validation**: Perform assertions and validations to ensure data quality and integrity.
- **Data Storage**: Load the validated data into a PostgreSQL database.
- **Data Transformation**: Use dbt to transform raw data into an analytics-ready format.
- **Pipeline Orchestration**: Prefect handles scheduling, orchestrating, and monitoring the pipeline.

---

## Architecture

1. **Data Ingestion**: A Python script fetches weather data from the OpenWeather API.
2. **Validation**: The data is validated with assertions to check for missing values, correct data types, and valid
   ranges.
3. **Data Storage**: The validated data is loaded into a PostgreSQL database.
4. **Data Transformation**: dbt performs transformations, cleaning, and creates models for downstream analytics.
5. **Orchestration**: Prefect orchestrates the entire workflow, ensuring tasks run as scheduled and providing monitoring
   capabilities.

---

## Installation

### Clone the Repository

```bash
$ git clone https://github.com/AbdelqaderMuhammad/weather-data-pipeline-project
$ cd weather-data-pipeline-project
```

### Install Dependencies

```bash
$ pip install docker
```

### Secrets Setup

Create the following secret files in the secrets/ directory to store sensitive data:

postgres_password.txt: Contains the PostgreSQL password.

dbt_password.txt: Contains the dbt connection password.

prefect_api_url.txt: Contains the Prefect API URL.

prefect_api_key.txt: Contains the Prefect API key.

### Set Up Environment Variables

Create a `.env` file in the root directory to store sensitive data (e.g., API keys and database credentials):

```env
OPENWEATHER_API_KEY=your_api_key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=weather_data
DB_USER=your_username
DB_PASSWORD=your_password
```

## Usage

### Running the Pipeline

Start the pipeline using Docker Compose:

```bash'
$ docker-compose up -d --build
```

---

## Data Flow

1. **Fetch**: Pull data from the OpenWeather API.
2. **Validate**: Verify data integrity (e.g., missing values, data types).
3. **Store**: Insert data into PostgreSQL.
4. **Transform**: Use dbt to:
    - Clean and standardize raw data.
    - Build transformed models.
    - Perform final validations.

---

## Docker Compose Configuration

The `docker-compose.yml` file defines the services required for the pipeline. Below is an example configuration:

```yaml
services:
  postgres:
    image: postgres:13
    container_name: postgres
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_DB: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    secrets:
      - postgres_password

  dbt:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: dbt
    environment:
      DBT_USER: admin
      DBT_PASSWORD_FILE: /run/secrets/dbt_password
      DBT_HOST: postgres
      DBT_PORT: 5432
      DBT_DATABASE: postgres
      DBT_SCHEMA: public
      PREFECT_API_URL_FILE: /run/secrets/prefect_api_url
      PREFECT_API_KEY_FILE: /run/secrets/prefect_api_key
      PREFECT_LOGGING_LEVEL: INFO
    volumes:
      - ./dbt:/usr/app/dbt
      - ./app:/usr/app
    depends_on:
      - postgres
    command: >
      sh -c "
      cd /usr/app &&
      export PREFECT_API_URL=$(cat /run/secrets/prefect_api_url) &&
      export PREFECT_API_KEY=$(cat /run/secrets/prefect_api_key) &&
      python run_dbt_flow.py &
      sleep infinity
      "
    secrets:
      - dbt_password
      - prefect_api_url
      - prefect_api_key

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  dbt_password:
    file: ./secrets/dbt_password.txt
  prefect_api_url:
    file: ./secrets/prefect_api_url.txt
  prefect_api_key:
    file: ./secrets/prefect_api_key.txt

volumes:
  postgres_data:

```

## Project Structure

```plaintext
.
├── dbt
│   ├── models
│   │   ├── staging
│   │   └── analytics
├── src
│   ├── fetch_data.py
│   ├── validate_data.py
│   ├── load_to_postgres.py
├── prefect_flows
│   └── main_pipeline.py
├── .env
├── README.md
```

