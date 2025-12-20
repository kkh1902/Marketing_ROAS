-- 테스트: 캠페인 속성 조합이 고유한지 확인
-- 같은 site_id, app_id, banner_pos, device_type 조합이 여러 번 나오면 실패

select
    site_id,
    app_id,
    banner_pos,
    device_type
from {{ ref('dim_campaigns') }}
group by 1, 2, 3, 4
having count(*) > 1
