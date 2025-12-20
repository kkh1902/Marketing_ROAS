-- 테스트: 시간별 데이터 개수가 합리적인지 확인
-- 일반적으로 24시간 중 일부 데이터가 있어야 함 (0-24 사이)

select *
from {{ ref('fct_daily_metrics') }}
where hours_with_data < 0 or hours_with_data > 24
