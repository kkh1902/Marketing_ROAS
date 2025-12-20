-- 테스트: 일별 클릭 수가 노출 수보다 많으면 안됨
-- daily_clicks > daily_impressions면 실패

select *
from {{ ref('fct_daily_metrics') }}
where daily_total_clicks > daily_total_impressions
