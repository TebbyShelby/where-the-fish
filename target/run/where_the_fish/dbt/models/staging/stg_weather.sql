
  
  create view "dev"."silver"."stg_weather__dbt_tmp" as (
    -- Staging model for weather forecast data
-- Cleans JSON, deduplicates

with raw as (
    select * from bronze.weather_raw
),

cleaned as (
    select
        json_extract_string(data, '$.location.location_id') as location_id,
        json_extract_string(data, '$.location.location_name') as location_name,
        data['date']::date as forecast_date,
        data['min_temp']::int as min_temp_celsius,
        data['max_temp']::int as max_temp_celsius,
        json_extract_string(data, '$.morning_forecast') as morning_forecast,
        json_extract_string(data, '$.afternoon_forecast') as afternoon_forecast,
        json_extract_string(data, '$.night_forecast') as night_forecast,
        json_extract_string(data, '$.summary_forecast') as summary_forecast,
        json_extract_string(data, '$.summary_when') as summary_when,
        json_extract_string(data, '$._ingested_at')::timestamp as ingested_at
    from raw
),

-- Deduplicate: same location_name can have 2 rows per date (district + town level)
-- Keep the district-level (Ds prefix) or the more detailed forecast
ranked as (
    select *,
        row_number() over (
            partition by location_name, forecast_date
            order by
                case when location_id like 'Ds%' then 0 else 1 end,
                ingested_at desc
        ) as rn
    from cleaned
    where location_id is not null
      and forecast_date is not null
)

select
    location_id,
    location_name,
    forecast_date,
    min_temp_celsius,
    max_temp_celsius,
    morning_forecast,
    afternoon_forecast,
    night_forecast,
    summary_forecast,
    summary_when,
    ingested_at
from ranked
where rn = 1
order by location_name, forecast_date
  );
