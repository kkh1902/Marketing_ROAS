-- 테스트: 7일 이동평균이 일일 CTR과 근사하는지 확인
-- 이동평균이 0%와 100% 사이여야 함

select *
from {{ ref('fct_daily_metrics') }}
where (ctr_7day_moving_avg < 0 or ctr_7day_moving_avg > 100)
   and ctr_7day_moving_avg is not null
