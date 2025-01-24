select *
from {{ ref('weather_data') }}
WHERE measurement_time > CURRENT_TIMESTAMP;