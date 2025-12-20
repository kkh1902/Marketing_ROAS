-- 테스트: CTR이 0~100% 범위 내인지 확인
-- CTR이 100%를 초과하거나 음수면 실패 (데이터 오류)

select *
from {{ ref('int_hourly_agg') }}
where ctr_percentage < 0
   or ctr_percentage > 100
   or ctr_percentage is null
