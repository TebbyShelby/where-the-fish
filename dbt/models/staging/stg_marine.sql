-- Staging model for marine data (DuckDB)
-- Unpacks hourly JSON arrays into row-per-hour records

with raw as (
    select
        json_extract_string(data, '$._spot_name') as spot_name,
        json_extract_string(data, '$._ingested_at') as ingested_at_str,
        data['hourly'] as h
    from bronze.marine_raw
),

unpacked as (
    select
        spot_name,
        ingested_at_str::timestamp as ingested_at,
        unnest(h['time']::varchar[])::timestamp as forecast_hour,
        unnest(h['sea_surface_temperature']::float[]) as sea_surface_temp,
        unnest(h['wave_height']::float[]) as wave_height,
        unnest(h['wave_direction']::float[]) as wave_direction,
        unnest(h['wave_period']::float[]) as wave_period,
        unnest(h['swell_wave_height']::float[]) as swell_wave_height,
        unnest(h['swell_wave_direction']::float[]) as swell_wave_direction,
        unnest(h['swell_wave_period']::float[]) as swell_wave_period,
        unnest(h['ocean_current_velocity']::float[]) as ocean_current_velocity
    from raw
)

select
    spot_name,
    ingested_at,
    forecast_hour,
    forecast_hour::date as forecast_date,
    sea_surface_temp,
    wave_height,
    wave_direction,
    wave_period,
    swell_wave_height,
    swell_wave_direction,
    swell_wave_period,
    ocean_current_velocity
from unpacked
where forecast_hour is not null
order by spot_name, forecast_hour
