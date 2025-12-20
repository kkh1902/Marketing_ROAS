-- 테스트: 같은 날짜/사이트/디바이스 조합이 여러 개면 실패
-- 각 조합은 하루에 1개씩만 있어야 함

select
    event_date,
    site_id,
    device_type
from {{ ref('fct_daily_metrics') }}
group by 1, 2, 3
having count(*) > 1
