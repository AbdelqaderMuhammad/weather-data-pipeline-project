SELECT *
FROM {{ ref('weather_data.sql') }}
WHERE temperature < -50 OR temperature > 60