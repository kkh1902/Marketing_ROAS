-- 테스트: 클릭 수가 노출 수보다 많으면 안됨
-- clicks > impressions면 실패 (논리적 오류)

select *
from {{ ref('int_hourly_agg') }}
where clicks_count > impressions_count
