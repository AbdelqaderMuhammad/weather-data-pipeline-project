WITH monthly_aggregates AS (
    SELECT
        city_id,
        city_name,
        DATE_TRUNC('month', measurement_time) AS measurement_month,
        AVG(temperature) AS avg_temperature,
        AVG(humidity) AS avg_humidity
    FROM {{ source('weather_data_source', 'weather_data') }}
    GROUP BY city_id, city_name, DATE_TRUNC('month', measurement_time)
)

SELECT *
FROM monthly_aggregates
ORDER BY measurement_month, city_name

