SELECT *
FROM {{ ref('weather_data') }}
WHERE temperature < -50 AND humidity > 100;