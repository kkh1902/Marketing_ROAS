-- 테스트: Click 값이 0 또는 1만 포함되는지 확인
-- 유효하지 않은 값이 있으면 실패

select *
from {{ ref('stg_ad_events') }}
where click not in (0, 1) or click is null
