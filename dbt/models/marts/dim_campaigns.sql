{{ config(
    materialized='table'
) }}

with stg_events as (
    select
        site_id,
        site_domain,
        site_category,
        app_id,
        app_domain,
        app_category,
        banner_pos,
        device_type
    from {{ ref('stg_ad_events') }}
),

campaign_unique as (
    select distinct
        site_id,
        site_domain,
        site_category,
        app_id,
        app_domain,
        app_category,
        banner_pos,
        device_type
    from stg_events
    where 1=1
        and (site_id is not null or app_id is not null)
),

with_surrogate_key as (
    select
        row_number() over (order by site_id, app_id, banner_pos, device_type) as campaign_id,
        site_id,
        site_domain,
        site_category,
        app_id,
        app_domain,
        app_category,
        banner_pos,
        device_type
    from campaign_unique
),

final as (
    select
        campaign_id,
        site_id,
        site_domain,
        site_category,
        app_id,
        app_domain,
        app_category,
        banner_pos,
        device_type,
        1 as is_active,
        current_timestamp as created_at,
        current_timestamp as updated_at,
        current_timestamp as dbt_loaded_at
    from with_surrogate_key
)

select * from final
