-- Gold layer: daily fishing score per location
-- Combines marine, weather, and tide data into a 0-100 score

with marine_daily as (
    select
        spot_name as location,
        forecast_date,
        count(*) as hourly_readings,
        round(avg(wave_height), 2) as avg_wave_height,
        round(max(wave_height), 2) as max_wave_height,
        round(avg(sea_surface_temp), 1) as avg_sea_temp,
        round(avg(swell_wave_height), 2) as avg_swell_height,
        round(avg(ocean_current_velocity), 2) as avg_current
    from {{ ref('stg_marine') }}
    group by spot_name, forecast_date
),

weather_daily as (
    select
        location_name as location,
        forecast_date,
        min_temp_celsius,
        max_temp_celsius,
        summary_forecast
    from {{ ref('stg_weather') }}
),

tide_daily as (
    select
        spot_name as location,
        tide_date,
        count(*) as tide_events,
        min(tide_height_meters) as min_tide,
        max(tide_height_meters) as max_tide,
        count(case when tide_type = 'high' then 1 end) as high_tide_count
    from {{ ref('stg_tide') }}
    group by spot_name, tide_date
),

joined as (
    select
        coalesce(m.location, w.location) as location,
        coalesce(m.forecast_date, w.forecast_date) as forecast_date,
        m.avg_wave_height,
        m.max_wave_height,
        m.avg_sea_temp,
        m.avg_swell_height,
        m.avg_current,
        w.min_temp_celsius,
        w.max_temp_celsius,
        w.summary_forecast,
        t.high_tide_count,
        t.min_tide,
        t.max_tide
    from marine_daily m
    full outer join weather_daily w
        on m.location = w.location and m.forecast_date = w.forecast_date
    left join tide_daily t
        on coalesce(m.location, w.location) = t.location
        and coalesce(m.forecast_date, w.forecast_date) = t.tide_date
),

scored as (
    select
        *,

        -- Wave height score (lower is better, 0-40 points)
        case
            when avg_wave_height is null then 20
            when avg_wave_height <= 0.3 then 40
            when avg_wave_height <= 0.5 then 35
            when avg_wave_height <= 0.8 then 25
            when avg_wave_height <= 1.2 then 15
            when avg_wave_height <= 1.5 then 5
            else 0
        end as wave_score,

        -- Sea temperature score (25-30C is ideal, 0-25 points)
        case
            when avg_sea_temp is null then 15
            when avg_sea_temp between 25.0 and 30.0 then 25
            when avg_sea_temp between 22.0 and 32.0 then 15
            else 5
        end as temp_score,

        -- Weather score (no rain is best, 0-20 points)
        case
            when summary_forecast is null then 10
            when summary_forecast like '%Tiada hujan%' then 20
            when summary_forecast like '%Ribut%' then 5
            when summary_forecast like '%Hujan%' then 10
            else 10
        end as weather_score,

        -- Tide score (more high tide events = more feeding activity, 0-15 points)
        case
            when high_tide_count is null then 0
            when high_tide_count >= 2 then 15
            when high_tide_count = 1 then 10
            else 5
        end as tide_score,

        -- Air temp bonus (comfortable = 0-10 bonus)
        case
            when max_temp_celsius is null then 5
            when max_temp_celsius between 27.0 and 33.0 then 10
            when max_temp_celsius between 24.0 and 35.0 then 5
            else 0
        end as air_temp_bonus

    from joined
)

select
    location,
    forecast_date,

    avg_wave_height,
    avg_sea_temp,
    avg_swell_height,
    min_temp_celsius,
    max_temp_celsius,
    summary_forecast,
    high_tide_count,

    -- Component scores
    wave_score,
    temp_score,
    weather_score,
    tide_score,
    air_temp_bonus,

    -- Overall score (0-100, higher = better fishing conditions)
    wave_score + temp_score + weather_score + tide_score + air_temp_bonus as overall_score,

    -- Label
    case
        when wave_score + temp_score + weather_score + tide_score + air_temp_bonus >= 80 then 'Excellent'
        when wave_score + temp_score + weather_score + tide_score + air_temp_bonus >= 60 then 'Good'
        when wave_score + temp_score + weather_score + tide_score + air_temp_bonus >= 40 then 'Fair'
        else 'Poor'
    end as fishing_rating

from scored
where forecast_date is not null
order by forecast_date, location
