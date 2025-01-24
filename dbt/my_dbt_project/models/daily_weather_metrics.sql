with daily_aggregates as (
    select
        city_id,
        city_name,
        date(measurement_time) as measurement_date,
        avg(temperature) as avg_temperature,
        avg(humidity) as avg_humidity,
        avg(wind_speed) as avg_wind_speed
    from {{ source('weather_data_source', 'weather_data') }}
    GROUP BY city_id, city_name, DATE(measurement_time)
)

select *
from daily_aggregates
order by measurement_date, city_name