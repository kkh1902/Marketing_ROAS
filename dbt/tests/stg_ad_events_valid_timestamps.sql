-- 테스트: 타임스탬프 변환이 올바르게 되었는지 확인
-- event_timestamp가 과거 날짜인지 확인 (미래 데이터 방지)

select *
from {{ ref('stg_ad_events') }}
where event_timestamp > current_timestamp
   or event_timestamp < '2014-10-21'::timestamp
