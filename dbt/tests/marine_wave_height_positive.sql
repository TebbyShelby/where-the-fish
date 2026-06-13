-- Wave height should not be negative

with validation as (
    select count(*) as bad_count
    from {{ ref('stg_marine') }}
    where wave_height < 0
)

select * from validation where bad_count > 0
