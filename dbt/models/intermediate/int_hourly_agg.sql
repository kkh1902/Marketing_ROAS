{{ config(
    materialized='table',
    partition_by={
        "field": "event_date",
        "data_type": "date",
        "granularity": "day"
    }
) }}

with stg_events as (
    select * from {{ ref('stg_ad_events') }}
),

hourly_metrics as (
    select
        event_date,
        event_hour,
        site_id,
        site_domain,
        site_category,
        device_type,

        -- Count metrics
        count(*) as total_impressions,
        sum(click) as total_clicks,

        -- CTR calculation
        round(
            100.0 * sum(click) / nullif(count(*), 0),
            2
        ) as ctr_percentage,

        -- Click-through rate details
        sum(case when click = 1 then 1 else 0 end) as clicks_count,
        count(*) as impressions_count,

        -- Engagement metrics
        max(case when click = 1 then 1 else 0 end) as has_clicks,
        min(case when click = 1 then 1 else 0 end) as no_clicks

    from stg_events
    where 1=1
        and event_hour is not null
        and site_id is not null
    group by 1, 2, 3, 4, 5, 6
),

final as (
    select
        event_date,
        concat(cast(event_date as varchar), ' ', event_hour, ':00:00') as event_hour_timestamp,
        site_id,
        site_domain,
        site_category,
        device_type,
        total_impressions,
        total_clicks,
        ctr_percentage,
        clicks_count,
        impressions_count,
        has_clicks,
        no_clicks,
        current_timestamp as dbt_loaded_at
    from hourly_metrics
)

select * from final
