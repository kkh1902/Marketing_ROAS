-- 테스트: Surrogate Key (campaign_id)가 고유한지 확인
-- campaign_id 중복이 있으면 실패

select campaign_id
from {{ ref('dim_campaigns') }}
group by campaign_id
having count(*) > 1
