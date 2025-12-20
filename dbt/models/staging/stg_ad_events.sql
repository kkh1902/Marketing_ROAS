{{ config(
    materialized='table',
    partition_by={
        "field": "event_date",
        "data_type": "date",
        "granularity": "day"
    }
) }}

with source_data as (
    select
        id,
        click,
        hour,
        banner_pos,
        site_id,
        site_domain,
        site_category,
        app_id,
        app_domain,
        app_category,
        device_id,
        device_ip,
        device_model,
        device_type,
        device_conn_type,
        c1,
        c14,
        c15,
        c16,
        c17,
        c18,
        c19,
        c20,
        c21
    from {{ source('realtime', 'ad_events') }}
),

validated_data as (
    select
        id,
        click,
        hour,
        banner_pos,
        site_id,
        site_domain,
        site_category,
        app_id,
        app_domain,
        app_category,
        device_id,
        device_ip,
        device_model,
        device_type,
        device_conn_type,
        c1,
        c14,
        c15,
        c16,
        c17,
        c18,
        c19,
        c20,
        c21,
        -- Convert hour to timestamp
        to_timestamp(hour::text, 'YYYYMMDDHH') as event_timestamp,
        to_date(to_timestamp(hour::text, 'YYYYMMDDHH'), 'YYYY-MM-DD') as event_date,
        to_char(to_timestamp(hour::text, 'YYYYMMDDHH'), 'HH24') as event_hour
    from source_data
    where 1=1
        -- Remove invalid click values (must be 0 or 1)
        and click in (0, 1)
        -- Remove rows with NULL critical columns
        and id is not null
        and hour is not null
        and site_id is not null
),

deduplicated_data as (
    select
        *,
        row_number() over (partition by id order by event_timestamp desc) as rn
    from validated_data
),

final as (
    select
        id,
        click,
        event_timestamp,
        event_date,
        event_hour,
        banner_pos,
        site_id,
        site_domain,
        site_category,
        app_id,
        app_domain,
        app_category,
        device_id,
        device_ip,
        device_model,
        device_type,
        device_conn_type,
        c1,
        c14,
        c15,
        c16,
        c17,
        c18,
        c19,
        c20,
        c21,
        current_timestamp as dbt_loaded_at
    from deduplicated_data
    where rn = 1
)

select * from final