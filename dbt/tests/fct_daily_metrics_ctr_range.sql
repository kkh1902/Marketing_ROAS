-- 테스트: 일별 CTR이 0~100% 범위 내인지 확인
-- CTR이 100%를 초과하거나 음수면 실패

select *
from {{ ref('fct_daily_metrics') }}
where daily_ctr_percentage < 0
   or daily_ctr_percentage > 100
   or daily_ctr_percentage is null
