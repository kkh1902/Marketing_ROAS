{{ config(
    materialized='table',
    partition_by={
        "field": "event_date",
        "data_type": "date",
        "granularity": "day"
    }
) }}

with hourly_agg as (
    select * from {{ ref('int_hourly_agg') }}
),

daily_metrics as (
    select
        event_date,
        site_id,
        site_domain,
        site_category,
        device_type,

        -- Daily aggregation
        sum(total_impressions) as daily_total_impressions,
        sum(total_clicks) as daily_total_clicks,
        round(
            100.0 * sum(total_clicks) / nullif(sum(total_impressions), 0),
            2
        ) as daily_ctr_percentage,

        -- Count of hours with data
        count(distinct event_hour_timestamp) as hours_with_data

    from hourly_agg
    group by 1, 2, 3, 4, 5
),

with_previous_day as (
    select
        dm.*,
        lag(dm.daily_total_clicks) over (
            partition by dm.site_id, dm.device_type
            order by dm.event_date
        ) as previous_day_clicks,
        lag(dm.daily_ctr_percentage) over (
            partition by dm.site_id, dm.device_type
            order by dm.event_date
        ) as previous_day_ctr
    from daily_metrics dm
),

with_calculations as (
    select
        event_date,
        site_id,
        site_domain,
        site_category,
        device_type,
        daily_total_impressions,
        daily_total_clicks,
        daily_ctr_percentage,
        hours_with_data,

        -- Day-over-day change
        case
            when previous_day_clicks is not null
            then round(
                ((daily_total_clicks - previous_day_clicks) / nullif(previous_day_clicks, 0) * 100),
                2
            )
            else null
        end as clicks_dod_pct_change,

        -- 7-day moving average
        round(
            avg(daily_total_clicks) over (
                partition by site_id, device_type
                order by event_date
                rows between 6 preceding and current row
            ),
            2
        ) as clicks_7day_moving_avg,

        round(
            avg(daily_ctr_percentage) over (
                partition by site_id, device_type
                order by event_date
                rows between 6 preceding and current row
            ),
            2
        ) as ctr_7day_moving_avg

    from with_previous_day
),

final as (
    select
        event_date,
        site_id,
        site_domain,
        site_category,
        device_type,
        daily_total_impressions,
        daily_total_clicks,
        daily_ctr_percentage,
        hours_with_data,
        clicks_dod_pct_change,
        clicks_7day_moving_avg,
        ctr_7day_moving_avg,
        current_timestamp as dbt_loaded_at
    from with_calculations
)

select * from final
