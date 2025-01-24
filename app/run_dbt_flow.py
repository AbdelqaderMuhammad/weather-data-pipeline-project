from prefect import task, flow
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import psycopg2
from prefect.filesystems import LocalFileSystem
from psycopg2.extras import execute_values
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


# Weather data structure
@dataclass
class WeatherData:
    city_id: str
    city_name: str
    temperature: float
    humidity: float
    wind_speed: float
    description: str
    measurement_time: str
    extraction_time: str


class WeatherDataCollector:
    def __init__(
            self,
            api_key: str,
            output_dir: str = "weather_data_extraction_logs",
            max_retries: int = 3,
            retry_backoff: int = 5,
            cities: Optional[List[Dict[str, str]]] = None,
            db_config: Optional[Dict[str, str]] = None
    ):
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.cities = cities or self._default_cities()
        self.session = self._setup_session(max_retries, retry_backoff)
        self._setup_output_dir()
        self._setup_logging()
        self.db_config = db_config

    @staticmethod
    def _default_cities() -> List[Dict[str, str]]:
        return [
            {"id": "2643743", "name": "London"},
            {"id": "5128581", "name": "New York"},
            {"id": "1850147", "name": "Tokyo"},
            {"id": "2147714", "name": "Sydney"}
        ]

    def _setup_output_dir(self):
        self.output_dir.mkdir(exist_ok=True)

    def _setup_logging(self):
        log_file = self.output_dir / "weather_extraction.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            handlers=[logging.FileHandler(log_file)]
        )

    def _setup_session(self, max_retries: int, retry_backoff: int) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_weather_data(self, city_id: str) -> Optional[Dict[str, Any]]:
        params = {"id": city_id, "appid": self.api_key, "units": "metric"}
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            logging.info(f"Successfully fetched weather data for city {city_id}")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch weather data for city {city_id}: {e}")
            return None

    def process_weather_data(self, raw_data: Dict[str, Any]) -> Optional[WeatherData]:
        try:
            return WeatherData(
                city_id=str(raw_data["id"]),
                city_name=raw_data["name"],
                temperature=raw_data["main"]["temp"],
                humidity=raw_data["main"]["humidity"],
                wind_speed=raw_data["wind"]["speed"],
                description=raw_data["weather"][0]["description"],
                measurement_time=datetime.fromtimestamp(raw_data["dt"]).isoformat(),
                extraction_time=datetime.utcnow().isoformat()
            )
        except (KeyError, ValueError) as e:
            logging.warning(f"Invalid weather data for city {raw_data.get('name')}: {e}")
            return None

    def save_to_db(self, data: List[WeatherData]) -> None:
        if not data:
            logging.warning("No weather data to save to the database.")
            return

        if not self.db_config:
            logging.error("Database configuration is not provided.")
            return

        try:
            connection = psycopg2.connect(**self.db_config)
            cursor = connection.cursor()

            create_table_query = """
            CREATE TABLE IF NOT EXISTS weather_data (
                id SERIAL PRIMARY KEY,
                city_id TEXT,
                city_name TEXT,
                temperature DECIMAL(5,2) NOT NULL,
                humidity DECIMAL(5,2) NOT NULL,
                wind_speed DECIMAL(6,2) NOT NULL,
                description VARCHAR(50) NOT NULL,
                measurement_time TIMESTAMP NOT NULL,
                extraction_time TIMESTAMP NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)

            insert_query = """
            INSERT INTO weather_data (
                city_id, city_name, temperature, humidity, wind_speed,
                description, measurement_time, extraction_time
            ) VALUES %s
            """

            values = [(
                record.city_id, record.city_name, record.temperature, record.humidity,
                record.wind_speed, record.description, record.measurement_time, record.extraction_time
            ) for record in data]

            execute_values(cursor, insert_query, values)
            connection.commit()

            logging.info(f"Saved weather data for {len(data)} cities to the database.")
        except psycopg2.Error as e:
            logging.error(f"Database error: {e}")
        finally:
            if connection:
                cursor.close()
                connection.close()

    def run(self) -> None:
        weather_records = []
        for city in self.cities:
            raw_data = self.fetch_weather_data(city["id"])
            if raw_data:
                processed_data = self.process_weather_data(raw_data)
                if processed_data:
                    weather_records.append(processed_data)

        if weather_records:
            self.save_to_db(weather_records)


@task
def extract_weather_data():
    """Extracts weather data and saves to DB"""
    API_KEY = "4365f80a748975673df3b3945754f842"
    DB_CONFIG = {
        "dbname": "my_database",
        "user": "admin",
        "password": "password",
        "host": "postgres",
        "port": 5432
    }
    collector = WeatherDataCollector(api_key=API_KEY, db_config=DB_CONFIG)
    collector.run()


@task
def run_dbt_command(command: str, working_dir: str):
    """Runs dbt commands inside the container"""
    result = subprocess.run(command, shell=True, capture_output=True, cwd=working_dir)
    if result.returncode != 0:
        raise Exception(f"Error running dbt command: {result.stderr.decode()}")
    return result.stdout.decode()


@flow
def dbt_flow():
    """DBT Flow"""
    dbt_project_dir = "/usr/app/dbt/my_dbt_project"  # Change to the location of your dbt project
    profiles_dir = "/usr/app/dbt"  # Change to the location of your profiles.yml

    # Run dbt command with the correct profile directory
    command = f"dbt run --profiles-dir {profiles_dir}"
    run_dbt_command(command, dbt_project_dir)


@flow
def full_etl_flow():
    """Full ETL flow that runs weather extraction and then DBT"""
    extract_weather_data()
    dbt_flow()


if __name__ == "__main__":
    full_etl_flow.serve(
        name="scheduled-etl-flow",
        interval=120
    )