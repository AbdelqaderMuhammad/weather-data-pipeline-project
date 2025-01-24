select *
from {{ ref('weather_data') }}
WHERE extraction_time < measurement_time;