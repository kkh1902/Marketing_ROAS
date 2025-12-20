-- 테스트: is_active 값이 0 또는 1만 있는지 확인

select *
from {{ ref('dim_campaigns') }}
where is_active not in (0, 1)
   or is_active is null
