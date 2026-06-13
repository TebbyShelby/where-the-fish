-- Overall score should always be between 0 and 100

with validation as (
    select count(*) as out_of_range
    from {{ ref('fishing_score') }}
    where overall_score < 0
       or overall_score > 100
)

select * from validation where out_of_range > 0
