-- 테스트: 각 시간별 집계에 데이터가 있는지 확인
-- 0이 아닌 노출수가 있어야 함

select *
from {{ ref('int_hourly_agg') }}
where total_impressions = 0
   or impressions_count = 0
