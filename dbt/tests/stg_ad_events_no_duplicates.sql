-- 테스트: ID 중복 제거 확인
-- Staging 레이어에서 중복 이벤트가 있으면 실패

select id
from {{ ref('stg_ad_events') }}
group by id
having count(*) > 1
