select
    city_id,
    city_name,
    measurement_time,
    temperature,
    humidity,
    wind_speed,
    description
from {{ source('weather_data_source', 'weather_data') }}
WHERE
    temperature > 40 OR
    humidity < 10 OR
    wind_speed > 100
ORDER BY measurement_time DESC
