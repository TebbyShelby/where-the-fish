-- Tide height should be in a reasonable range (-1 to 10 meters globally)

with validation as (
    select count(*) as out_of_range
    from {{ ref('stg_tide') }}
    where tide_height_meters < -1
       or tide_height_meters > 10
)

select * from validation where out_of_range > 0
