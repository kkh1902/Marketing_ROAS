-- 테스트: 음수 값이 없는지 확인
-- 노출수, 클릭수가 음수면 실패

select *
from {{ ref('fct_daily_metrics') }}
where daily_total_impressions < 0
   or daily_total_clicks < 0
   or hours_with_data < 0
