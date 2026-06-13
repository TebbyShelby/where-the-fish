-- Staging model for tide data (DuckDB)
-- Unpacks tide extremes array from TideCheck API

with raw as (
    select * from bronze.tide_raw
),

tide_extremes as (
    select
        json_extract_string(raw.data, '$._spot_name') as spot_name,
        json_extract_string(raw.data, '$.station.name') as station_name,
        json_extract_string(raw.data, '$.station.id') as station_id,
        raw.data['station']['lat']::float as station_lat,
        raw.data['station']['lon']::float as station_lon,
        json_extract_string(raw.data, '$.datum') as datum,
        e['time']::timestamp as tide_time,
        e['localdate']::date as tide_date,
        e['height']::float as tide_height_meters,
        e['type']::varchar as tide_type,
        json_extract_string(raw.data, '$._ingested_at')::timestamp as ingested_at
    from raw,
    unnest(raw.data['extremes']::JSON[]) as t(e)
)

select
    spot_name,
    station_name,
    station_id,
    station_lat,
    station_lon,
    datum,
    tide_time,
    tide_date,
    tide_height_meters,
    tide_type,
    ingested_at
from tide_extremes
order by spot_name, tide_time
