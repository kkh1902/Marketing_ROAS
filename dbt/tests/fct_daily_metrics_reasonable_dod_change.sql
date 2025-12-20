-- 테스트: 전일 대비 변화율이 합리적인 범위인지 확인
-- 1000% 이상 변화는 이상 (모니터링 필요)

select *
from {{ ref('fct_daily_metrics') }}
where abs(coalesce(clicks_dod_pct_change, 0)) > 1000
