-- 테스트: 음수 값이 없는지 확인
-- 노출수나 클릭수가 음수면 실패 (데이터 오류)

select *
from {{ ref('int_hourly_agg') }}
where total_impressions < 0
   or total_clicks < 0
   or clicks_count < 0
   or impressions_count < 0
