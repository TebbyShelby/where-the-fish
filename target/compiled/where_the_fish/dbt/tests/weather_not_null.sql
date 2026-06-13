-- Ensure core weather fields are not null

with validation as (
    select count(*) as null_count
    from "dev"."silver"."stg_weather"
    where location_id is null
       or forecast_date is null
       or min_temp_celsius is null
)

select * from validation where null_count > 0