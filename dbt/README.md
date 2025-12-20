# 📊 dbt - Data Transformation Layer

Kafka → Flink → PostgreSQL에서 수집한 **원본 데이터를 정제 및 분석 마트로 변환**하는 계층입니다.

---

## 📌 역할

```
PostgreSQL (realtime schema)
    ↓
dbt Transform Models
├─ Staging: 데이터 정제
├─ Intermediate: 중간 집계
└─ Marts: 최종 분석 테이블
    ↓
PostgreSQL (analytics schema)
    ↓
Metabase/BI Tools
```

### dbt가 하는 일
- **데이터 정제**: NULL 처리, 이상치 제거, 타입 변환
- **재사용 가능한 SQL**: 버전 관리, 의존성 추적
- **데이터 검증**: 테스트 자동화 (중복, NULL 검사 등)
- **문서화**: 자동 생성 문서

---

## 🏗️ 모델 구조

### **Layer 1: Staging (stg_ad_events)**
```sql
Source: realtime.ad_events (Flink가 저장한 원본)

목표: 원본 데이터 정제 및 검증

처리 내용:
├─ NULL 값 제거
├─ 데이터 타입 변환 (hour → timestamp)
├─ 이상치 제거 (click = 0 or 1만 허용)
├─ 중복 제거 (event_id 기준)
├─ 필요 컬럼만 선택
└─ 파티셔닝 (date/hour 기준)

Output: analytics.stg_ad_events
```

### **Layer 2: Intermediate (int_hourly_agg)**
```sql
Source: stg_ad_events

목표: 시간별 집계 (Flink와 다른 방식으로 검증)

처리 내용:
├─ GROUP BY hour
├─ CTR 계산 (clicks / impressions * 100)
├─ 사이트별 집계
├─ 디바이스 타입별 집계
└─ 성능 메트릭 (최대값, 최소값 등)

Output: analytics.int_hourly_agg
```

### **Layer 3: Marts - Dimension (dim_campaigns)**
```sql
Source: stg_ad_events

목표: 캠페인 정보 마스터 테이블

처리 내용:
├─ 유니크 캠페인 추출:
│  ├─ site_id, site_domain, site_category
│  ├─ app_id, app_domain, app_category
│  ├─ banner_pos, device_type
├─ Surrogate Key (campaign_id) 생성
├─ Created/Updated 타임스탐프
└─ is_active 플래그

Output: analytics.dim_campaigns
```

### **Layer 4: Marts - Fact (fct_daily_metrics)**
```sql
Source: int_hourly_agg, dim_campaigns

목표: 일별 KPI 테이블 (최종 분석)

처리 내용:
├─ GROUP BY date
├─ 일별 CTR 계산
├─ 디바이스별 CTR
├─ 사이트별 CTR
├─ 어제 대비 변화율
├─ 7일 이동평균
└─ 카테고리별 성과 분석

Output: analytics.fct_daily_metrics
```

---

## 📂 폴더 구조

```
dbt/
├── README.md                     # 이 파일
├── dbt_project.yml               # dbt 프로젝트 설정
├── profiles.yml                  # PostgreSQL 연결 설정
├── requirements.txt              # Python 의존성 (dbt-postgres)
├── Dockerfile                    # Docker 이미지 정의
│
├── models/                       # dbt 모델
│   ├── staging/
│   │   └── stg_ad_events.sql     # 원본 정제
│   ├── intermediate/
│   │   └── int_hourly_agg.sql    # 시간별 집계
│   └── marts/
│       ├── dim_campaigns.sql     # 캠페인 마스터 (Dimension)
│       └── fct_daily_metrics.sql # 일별 KPI (Fact)
│
├── tests/                        # 데이터 검증 테스트
│   ├── stg_ad_events_tests.yml
│   ├── int_hourly_agg_tests.yml
│   └── fct_daily_metrics_tests.yml
│
└── macros/                       # 재사용 가능한 SQL 매크로
    └── (향후 추가)
```

---

## 🚀 빠른 시작

### 1️⃣ 설치

```bash
# dbt 의존성 설치
cd dbt
pip install -r requirements.txt

# dbt 초기화
dbt init
```

### 2️⃣ 연결 설정 (profiles.yml)

```yaml
marketing_roas:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: postgres
      password: postgres
      port: 5432
      dbname: marketing_roas
      schema: analytics
      threads: 4
      keepalives_idle: 0
```

### 3️⃣ 모델 실행

```bash
# 모든 모델 실행
dbt run

# 특정 모델만 실행
dbt run --select stg_ad_events
dbt run --select +fct_daily_metrics  # 의존성 포함

# 선택적 실행 (Staging만)
dbt run --select path:models/staging
```

### 4️⃣ 데이터 검증

```bash
# 모든 테스트 실행
dbt test

# 특정 모델 테스트
dbt test --select stg_ad_events
```

### 5️⃣ 문서 생성

```bash
# HTML 문서 생성
dbt docs generate

# 문서 서버 실행 (localhost:8000)
dbt docs serve
```

---

## 🔄 의존성 다이어그램

```
realtime.ad_events (Flink)
    ↓
stg_ad_events (정제)
    ├─────┬──────────────┐
    │     │              │
    ▼     ▼              ▼
int_hourly_agg    dim_campaigns
    │                    │
    └────────┬───────────┘
             │
             ▼
    fct_daily_metrics (최종)
             │
             ▼
    Metabase / BI Tools
```

---

## ✅ 모델 체크리스트

| 모델 | 상태 | 설명 |
|------|------|------|
| `stg_ad_events` | 🔄 진행중 | 원본 정제 |
| `int_hourly_agg` | ⏳ 대기 | 시간별 집계 |
| `dim_campaigns` | ⏳ 대기 | 캠페인 마스터 |
| `fct_daily_metrics` | ⏳ 대기 | 일별 KPI |

---

## 🧪 테스트 전략

### Staging 테스트
```yaml
# 필수 검사
- not_null: [id, event_date, click]
- accepted_values:
    click: [0, 1]
- unique: [id]
```

### Intermediate 테스트
```yaml
# 검증
- not_null: [event_hour, impressions, clicks]
- assert: clicks <= impressions  # CTR이 100% 초과 불가
```

### Marts 테스트
```yaml
# 최종 검증
- not_null: [event_date]
- relationships:  # FK 검사
    campaign_id: dim_campaigns.campaign_id
```

---

## 📊 성능 최적화

### 파티셔닝
```sql
-- 날짜 기준 파티셔닝 (쿼리 성능 향상)
{{
  config(
    materialized='table',
    partition_by={
      "field": "event_date",
      "data_type": "date",
      "granularity": "day"
    }
  )
}}
```

### 클러스터링
```sql
-- 자주 사용되는 컬럼으로 클러스터링
{{
  config(
    materialized='table',
    cluster_by=["site_id", "event_date"]
  )
}}
```

---

## 🔍 디버깅

### 모델 쿼리 확인
```bash
# 컴파일된 SQL 보기
dbt compile --select stg_ad_events

# 실행 전 쿼리 미리보기
dbt run --select stg_ad_events --debug
```

### 데이터 품질 검사
```bash
# 특정 모델의 행 수 확인
dbt show stg_ad_events --limit 10

# 통계 확인
dbt show fct_daily_metrics --where "event_date = '2024-12-20'"
```

---

## 📝 모범 사례

### ✅ DO
- 모델명에 계층 표기: `stg_`, `int_`, `fct_`, `dim_`
- Staging은 직접 Source에만 접근
- 각 모델에 설명 (description) 추가
- 테스트 작성 필수
- 버전 관리 (git)

### ❌ DON'T
- 복잡한 로직을 한 모델에
- Intermediate를 Source처럼 사용
- 하드코딩된 값 (매직 넘버)
- 테스트 없는 배포

---

## 🔗 관련 문서

- [dbt 공식 문서](https://docs.getdbt.com/)
- [PostgreSQL 스키마](../schemas/realtime_ctr_metrics.sql)
- [Flink 파이프라인](../flink/README.md)
- [Airflow 오케스트레이션](../airflow/README.md)

---

## 📧 트러블슈팅

### Q: "schema analytics does not exist"
```bash
# PostgreSQL에서 스키마 생성
CREATE SCHEMA analytics;
```

### Q: "relation does not exist" (stg_ad_events)
```bash
# realtime.ad_events가 존재하는지 확인
SELECT COUNT(*) FROM realtime.ad_events;

# Flink가 데이터를 저장했는지 확인
SELECT * FROM realtime.ad_events LIMIT 10;
```

### Q: CTR 계산이 100을 초과
```sql
-- 데이터 검증
SELECT
  event_date,
  clicks,
  impressions,
  ROUND(100.0 * clicks / NULLIF(impressions, 0), 2) AS ctr
FROM fct_daily_metrics
WHERE clicks > impressions
ORDER BY 1 DESC;
```

---

## 📅 개발 일정

| 단계 | 작업 | 일정 | 상태 |
|------|------|------|------|
| 1 | `stg_ad_events` 구현 | Week 3-1 | 🔄 |
| 2 | `int_hourly_agg` 구현 | Week 3-2 | ⏳ |
| 3 | `dim_campaigns` 구현 | Week 3-3 | ⏳ |
| 4 | `fct_daily_metrics` 구현 | Week 3-4 | ⏳ |
| 5 | 테스트 & 검증 | Week 3-5 | ⏳ |

---

**마지막 업데이트**: 2024-12-20
**담당자**: Engineering Team
**상태**: 개발 진행중 🚀
