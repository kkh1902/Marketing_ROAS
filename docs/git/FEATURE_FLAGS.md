# 🚩 Feature Flags 가이드

## 개요

Feature Flags는 Trunk-Based Development의 핵심입니다.

> **Feature Flag**: 코드 배포 없이 기능을 활성화/비활성화할 수 있는 메커니즘

### 왜 Feature Flags가 필요한가?

Trunk-Based Development에서는 매일 main에 코드를 병합하지만, 모든 기능이 완성되지 않을 수 있습니다.
Feature Flags를 사용하면:

- ✅ 미완성 기능을 프로덕션에 배포해도 안전
- ✅ 기능 활성화를 런타임에 제어
- ✅ A/B 테스팅 가능
- ✅ 빠른 롤백 가능

---

## 아키텍처

### 위치

```
src/
├── config.py           # 🔧 Feature flags 설정
├── feature_flags.py    # 📋 Feature flags 관리 클래스
└── ...
```

### 플로우

```
코드 실행
  ↓
Feature Flag 체크
  ↓
├─ 활성화 (True) → 새 기능 실행
└─ 비활성화 (False) → 기존 기능 실행
```

---

## 구현 방식

### 방식 1: 환경 변수 (간단함)

```python
# src/config.py
import os

FEATURES = {
    "ENABLE_GOOGLE_ADS_COLLECTOR": os.getenv("ENABLE_GOOGLE_ADS_COLLECTOR", "false").lower() == "true",
    "ENABLE_META_ADS_COLLECTOR": os.getenv("ENABLE_META_ADS_COLLECTOR", "false").lower() == "true",
    "ENABLE_LOOKER_SYNC": os.getenv("ENABLE_LOOKER_SYNC", "false").lower() == "true",
    "ENABLE_EMAIL_ALERTS": os.getenv("ENABLE_EMAIL_ALERTS", "false").lower() == "true",
}
```

**.env 파일:**
```bash
ENABLE_GOOGLE_ADS_COLLECTOR=true
ENABLE_META_ADS_COLLECTOR=false
ENABLE_LOOKER_SYNC=false
ENABLE_EMAIL_ALERTS=false
```

### 방식 2: 설정 파일 (추천)

```python
# src/config.py
import json

def load_feature_flags():
    with open("config/feature_flags.json") as f:
        return json.load(f)

FEATURES = load_feature_flags()
```

**config/feature_flags.json:**
```json
{
  "ENABLE_GOOGLE_ADS_COLLECTOR": true,
  "ENABLE_META_ADS_COLLECTOR": false,
  "ENABLE_LOOKER_SYNC": false,
  "ENABLE_EMAIL_ALERTS": false,
  "ENABLE_DATA_VALIDATION": true
}
```

### 방식 3: 클래스 기반 (확장성)

```python
# src/feature_flags.py
from dataclasses import dataclass
from typing import Dict
import json

@dataclass
class FeatureFlagConfig:
    """Feature flag 설정 클래스"""
    name: str
    enabled: bool
    rollout_percentage: int = 100  # 점진적 배포용
    description: str = ""

class FeatureFlagManager:
    def __init__(self, config_file: str = "config/feature_flags.json"):
        self.flags: Dict[str, FeatureFlagConfig] = {}
        self.load_config(config_file)

    def load_config(self, config_file: str):
        with open(config_file) as f:
            data = json.load(f)
            for name, flag_data in data.items():
                self.flags[name] = FeatureFlagConfig(**flag_data)

    def is_enabled(self, flag_name: str, user_id: str = None) -> bool:
        """Feature flag 활성화 여부 확인"""
        if flag_name not in self.flags:
            return False

        flag = self.flags[flag_name]
        if not flag.enabled:
            return False

        # Rollout 백분율 확인 (점진적 배포)
        if flag.rollout_percentage < 100:
            if user_id:
                return hash(user_id) % 100 < flag.rollout_percentage
            return False

        return True

# 사용법
feature_flags = FeatureFlagManager()
if feature_flags.is_enabled("ENABLE_GOOGLE_ADS_COLLECTOR"):
    # 새 기능
    pass
```

**config/feature_flags.json:**
```json
{
  "ENABLE_GOOGLE_ADS_COLLECTOR": {
    "name": "Google Ads 수집기",
    "enabled": true,
    "rollout_percentage": 100,
    "description": "Google Ads API 통합 기능"
  },
  "ENABLE_META_ADS_COLLECTOR": {
    "name": "Meta Ads 수집기",
    "enabled": false,
    "rollout_percentage": 0,
    "description": "Meta Ads API 통합 기능 (개발중)"
  },
  "ENABLE_LOOKER_SYNC": {
    "name": "Looker Studio 동기화",
    "enabled": true,
    "rollout_percentage": 50,
    "description": "50% 사용자에게만 제공 (A/B 테스트)"
  }
}
```

---

## 사용 패턴

### 패턴 1: IF-ELSE

```python
# src/main.py
from src.config import FEATURES

def run_pipeline():
    if FEATURES["ENABLE_GOOGLE_ADS_COLLECTOR"]:
        print("Google Ads 데이터 수집 중...")
        collect_google_ads()
    else:
        print("Google Ads 수집 스킵")

    if FEATURES["ENABLE_META_ADS_COLLECTOR"]:
        print("Meta Ads 데이터 수집 중...")
        collect_meta_ads()

    if FEATURES["ENABLE_LOOKER_SYNC"]:
        print("Looker Studio 동기화 중...")
        sync_looker_dashboard()
```

### 패턴 2: 래퍼 함수

```python
# src/collectors/google_ads.py
from src.config import FEATURES

def collect_google_ads():
    """Google Ads 수집기 (Feature flag 제어)"""
    if not FEATURES["ENABLE_GOOGLE_ADS_COLLECTOR"]:
        print("Google Ads 수집이 비활성화됨")
        return None

    print("Google Ads 데이터 수집...")
    # 실제 구현
    return data

# 사용법
data = collect_google_ads()
```

### 패턴 3: 데코레이터

```python
# src/decorators.py
from functools import wraps
from src.config import FEATURES

def feature_flag(flag_name: str):
    """Feature flag 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not FEATURES.get(flag_name, False):
                print(f"{flag_name}이 비활성화되어 있습니다")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 사용법
@feature_flag("ENABLE_GOOGLE_ADS_COLLECTOR")
def collect_google_ads():
    print("Google Ads 데이터 수집...")
    return data
```

### 패턴 4: 전략 패턴 (권장)

```python
# src/collectors/strategy.py
from abc import ABC, abstractmethod
from src.config import FEATURES

class CollectorStrategy(ABC):
    @abstractmethod
    def collect(self):
        pass

class GoogleAdsCollector(CollectorStrategy):
    def collect(self):
        return "Google Ads 데이터"

class MetaAdsCollector(CollectorStrategy):
    def collect(self):
        return "Meta Ads 데이터"

class NoOpCollector(CollectorStrategy):
    def collect(self):
        return None

def get_google_ads_collector() -> CollectorStrategy:
    """Google Ads 수집기 (Feature flag)"""
    if FEATURES["ENABLE_GOOGLE_ADS_COLLECTOR"]:
        return GoogleAdsCollector()
    return NoOpCollector()

# 사용법
collector = get_google_ads_collector()
data = collector.collect()
```

---

## 실제 프로젝트 적용

### 1단계: Feature Flags 정의

```python
# src/config.py
from src.feature_flags import FeatureFlagManager

# Feature flag 설정 로드
feature_flags = FeatureFlagManager("config/feature_flags.json")
```

**config/feature_flags.json:**
```json
{
  "ENABLE_GOOGLE_ADS_COLLECTOR": {
    "name": "Google Ads 수집",
    "enabled": true,
    "rollout_percentage": 100
  },
  "ENABLE_META_ADS_COLLECTOR": {
    "name": "Meta Ads 수집",
    "enabled": false,
    "rollout_percentage": 0
  },
  "ENABLE_NAVER_ADS_COLLECTOR": {
    "name": "Naver Ads 수집",
    "enabled": false,
    "rollout_percentage": 0
  },
  "ENABLE_STAGING_PROCESSOR": {
    "name": "Staging 처리",
    "enabled": true,
    "rollout_percentage": 100
  },
  "ENABLE_METRICS_CALCULATION": {
    "name": "메트릭 계산",
    "enabled": false,
    "rollout_percentage": 0
  },
  "ENABLE_LOOKER_DASHBOARD": {
    "name": "Looker Studio 대시보드",
    "enabled": false,
    "rollout_percentage": 0
  },
  "ENABLE_EMAIL_ALERTS": {
    "name": "이메일 알림",
    "enabled": false,
    "rollout_percentage": 0
  }
}
```

### 2단계: 파이프라인에 적용

```python
# airflow/dags/marketing_pipeline.py
from src.config import feature_flags
from src.collectors import google_ads, meta_ads
from src.processors import staging, metrics

def run_marketing_pipeline():
    results = {}

    # Google Ads 수집 (활성화됨)
    if feature_flags.is_enabled("ENABLE_GOOGLE_ADS_COLLECTOR"):
        results['google_ads'] = google_ads.collect()

    # Meta Ads 수집 (비활성화됨)
    if feature_flags.is_enabled("ENABLE_META_ADS_COLLECTOR"):
        results['meta_ads'] = meta_ads.collect()

    # Staging 처리 (활성화됨)
    if feature_flags.is_enabled("ENABLE_STAGING_PROCESSOR"):
        results['staging'] = staging.process(results)

    # 메트릭 계산 (비활성화됨 - 개발중)
    if feature_flags.is_enabled("ENABLE_METRICS_CALCULATION"):
        results['metrics'] = metrics.calculate(results['staging'])

    return results
```

### 3단계: 개발 워크플로우

```
[월요일]
feature/meta-ads-collector 생성
↓
코드 작성 + config/feature_flags.json에 "ENABLE_META_ADS_COLLECTOR": false 추가
↓
테스트 + main에 병합 (안전함! 기능이 비활성화됨)

[화요일]
feature/metrics-calculation 생성
↓
코드 작성 + 테스트
↓
config/feature_flags.json에 "ENABLE_METRICS_CALCULATION": false 추가
↓
main에 병합

[금요일]
Meta Ads 수집기가 완전히 완성됨
↓
config/feature_flags.json에서 "ENABLE_META_ADS_COLLECTOR": true로 변경
↓
프로덕션 배포 (재배포 필요 없음!)
```

---

## 점진적 배포 (Rollout)

### 개념

Feature를 100% 사용자에게 한 번에 배포하지 않고, 단계적으로 배포합니다.

```
0% → 10% → 50% → 100%
```

### 구현

```python
# src/feature_flags.py
def is_enabled(self, flag_name: str, user_id: str = None) -> bool:
    flag = self.flags[flag_name]

    # 롤아웃 백분율 계산
    if flag.rollout_percentage < 100:
        if not user_id:
            return False

        # 사용자 ID 기반으로 일관된 결과
        user_hash = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
        return (user_hash % 100) < flag.rollout_percentage

    return flag.enabled
```

**config/feature_flags.json:**
```json
{
  "ENABLE_NEW_DASHBOARD": {
    "name": "신규 대시보드",
    "enabled": true,
    "rollout_percentage": 10,
    "description": "10% 사용자에게만 제공"
  }
}
```

### 단계적 배포 계획

```bash
# Day 1: 10% 사용자에게 배포
"rollout_percentage": 10

# Day 2: 결과 모니터링 (에러율, 성능 등)

# Day 3: 50% 사용자에게 확대
"rollout_percentage": 50

# Day 4: 모니터링

# Day 5: 100% 배포
"rollout_percentage": 100
```

---

## 모니터링 및 로깅

### Feature Flag 사용 로깅

```python
# src/config.py
import logging

logger = logging.getLogger(__name__)

class FeatureFlagManager:
    def is_enabled(self, flag_name: str, user_id: str = None) -> bool:
        result = self._check_flag(flag_name, user_id)

        # 로깅
        logger.info(f"Feature flag check", extra={
            "flag_name": flag_name,
            "enabled": result,
            "user_id": user_id,
            "rollout_percentage": self.flags[flag_name].rollout_percentage
        })

        return result
```

### 모니터링 쿼리 (BigQuery)

```sql
-- Feature flag 사용률
SELECT
  flag_name,
  COUNT(*) as usage_count,
  SUM(CASE WHEN enabled THEN 1 ELSE 0 END) as enabled_count
FROM logs
WHERE date = CURRENT_DATE()
GROUP BY flag_name
ORDER BY usage_count DESC;
```

---

## 체크리스트

### 새 기능 개발 시

```
□ Feature flag 이름 결정
□ config/feature_flags.json에 추가 (enabled: false)
□ 코드에 flag 체크 로직 추가
□ 테스트 작성 (flag on/off 모두)
□ main에 병합 (안전함!)
□ 모니터링 설정
□ 기능 완성 후 enabled: true로 변경
```

### 배포 전

```
□ Feature flag 상태 확인
□ 불필요한 old flag 정리
□ 로깅/모니터링 설정
□ Rollback 계획 수립
```

### 배포 후

```
□ 에러율 모니터링
□ 성능 메트릭 확인
□ 사용자 피드백 수집
□ 문제 발생 시 즉시 flag disable
```

---

## 주의사항

### ❌ 피해야 할 것

```python
# 나쁜 예: Feature flag이 너무 깊게 중첩
if FEATURES["FLAG_A"]:
    if FEATURES["FLAG_B"]:
        if FEATURES["FLAG_C"]:
            # ... 복잡함

# 나쁜 예: Feature flag 없이 오래된 기능 유지
if old_feature:
    old_code()
else:
    new_code()

# 나쁜 예: Feature flag이 영구적으로 false
# (제거되어야 함)
ENABLE_OLD_FEATURE = False  # 6개월 전부터
```

### ✅ 해야 할 것

```python
# 좋은 예: 깔끔한 구조
if FEATURES["ENABLE_NEW_COLLECTOR"]:
    collector = NewCollector()
else:
    collector = OldCollector()

# 좋은 예: 하이레벨 추상화
strategy = get_collector_strategy()
data = strategy.collect()

# 좋은 예: 정기적으로 정리
# Flag 활성화 후 2주 지나면 제거
```

---

## 완성된 코드 예시

### 전체 구조

```
src/
├── config.py
├── feature_flags.py          # Feature flag 매니저
├── collectors/
│   ├── __init__.py
│   ├── base.py
│   ├── google_ads.py
│   ├── meta_ads.py
│   └── strategy.py           # Strategy 패턴
├── processors/
│   ├── staging.py
│   └── metrics.py
└── main.py

config/
└── feature_flags.json        # Feature flag 설정
```

### 통합 예시

```python
# src/main.py
from src.config import feature_flags
from src.collectors.strategy import CollectorFactory

def main():
    # 활성화된 수집기 가져오기
    collectors = []

    if feature_flags.is_enabled("ENABLE_GOOGLE_ADS"):
        collectors.append(CollectorFactory.create("google_ads"))

    if feature_flags.is_enabled("ENABLE_META_ADS"):
        collectors.append(CollectorFactory.create("meta_ads"))

    # 데이터 수집
    all_data = []
    for collector in collectors:
        data = collector.collect()
        all_data.append(data)

    # 통합
    merged = merge_data(all_data)

    # Processing (Feature flag 제어)
    if feature_flags.is_enabled("ENABLE_STAGING"):
        staged = staging_process(merged)

    if feature_flags.is_enabled("ENABLE_METRICS"):
        metrics = calculate_metrics(staged)

    # 대시보드 (Feature flag 제어)
    if feature_flags.is_enabled("ENABLE_DASHBOARD"):
        sync_to_looker(metrics)

if __name__ == "__main__":
    main()
```

---

## 참고 자료

- [Feature Toggles - Martin Fowler](https://martinfowler.com/articles/feature-toggles.html)
- [Launch Darkly Documentation](https://docs.launchdarkly.com/)
- [Unleash - Open Source Feature Management](https://www.getunleash.io/)

---

## 다음 읽을 문서

- [STRATEGY.md](./STRATEGY.md) - Git 전략 개요
- [WORKFLOW.md](./WORKFLOW.md) - 일일 워크플로우
