# 🎯 Marketing ROAS - Ad Click Pipeline

Kafka, Flink, dbt를 활용한 실시간 광고 클릭 데이터 파이프라인

---

## 📌 프로젝트 개요

Avazu CTR 데이터셋(40M rows)을 활용한 실시간/배치 하이브리드 데이터 파이프라인입니다.

### 데이터셋 정보
- **전체 크기:** 7.82GB (압축), ~30GB (압축 해제)
- **행 수:** 40,428,967건
- **컬럼 수:** 24개
- **기간:** 2014-10-21 ~ 2014-10-31 (10일)
- **클릭률 (CTR):** 16.41%

### 주요 기능
- **실시간 처리**: Kafka → Flink로 1분/5분 단위 CTR 집계
- **배치 처리**: Airflow + dbt로 일별 분석 마트 생성
- **에러 처리**: DLQ Consumer 자동 retry + Slack 알림
- **모니터링**: Prometheus + Grafana 시스템 메트릭

---

## 🏗️ 아키텍처

```
┌──────────────────┐
│   Avazu Data     │
│  (40M rows)      │
└────────┬─────────┘
         │
    ┌────▼──────┐
    │   Kafka   │ ◄─── Kafka Producer (CSV 변환)
    │  Producer │      Schema Registry
    └────┬──────┘
         │
    ┌────▼──────────┐
    │     Kafka     │
    │    Topics     │
    │ - raw_events  │
    │ - error       │
    │ - retry       │
    └────┬──────────┘
         │
         ├──────────────────┬──────────────────┬──────────────────┐
         │                  │                  │                  │
    ┌────▼──────┐      ┌────▼──────┐      ┌────▼──────┐      ┌────▼──────┐
    │   Flink   │      │ PostgreSQL │      │   Redis   │      │ Local     │
    │ Streaming │      │  realtime  │      │  Cache    │      │ Files     │
    │ (Window)  │      │            │      │           │      │           │
    └────┬──────┘      └────┬───────┘      └────┬──────┘      └────┬──────┘
         │                  │                  │                  │
         └──────────────────┼──────────────────┼──────────────────┘
                            │
                       ┌────▼──────────────────┐
                       │  Streamlit Dashboard  │
                       │  (Real-time CTR)      │
                       └───────────────────────┘
         │
    ┌────▼──────┐
    │   Airflow  │
    │ + dbt      │
    └────┬───────┘
         │
    ┌────▼──────────┐
    │  PostgreSQL   │
    │  analytics    │
    └────┬──────────┘
         │
    ┌────▼──────┐
    │ Metabase  │
    │ Dashboard │
    └───────────┘
```

---

## 🛠️ 기술 스택

| 계층 | 기술 | 버전 | 역할 |
|------|------|------|------|
| **Ingestion** | Kafka + Schema Registry | 3.x | 이벤트 스트리밍, 스키마 관리 |
| **Processing** | Apache Flink | 1.17+ | 실시간 윈도우 집계 |
| **Orchestration** | Apache Airflow | 2.x | 배치 파이프라인 스케줄링 |
| **Transform** | dbt | 1.5+ | SQL 기반 데이터 모델링 |
| **Storage** | PostgreSQL | 14+ | realtime/analytics/errors 스키마 |
| **Cache** | Redis | 7.x | 실시간 메트릭 캐싱 |
| **Visualization** | Streamlit + Metabase | - | 실시간/배치 대시보드 |
| **Monitoring** | Prometheus + Grafana | - | 메트릭 수집, 시각화 |
| **Alerting** | Slack | - | 실시간 알림 |
| **Container** | Docker + Docker Compose | - | 인프라 코드화 |

---

## 📁 프로젝트 구조

```
marketing_roas/
├── README.md                       # 프로젝트 개요
├── docker-compose.yml              # 전체 서비스 정의
├── requirements.txt                # Python 의존성
│
├── config/                         # 설정 파일
│   ├── kafka_config.yml
│   ├── postgres_config.yml
│   ├── schema_registry.yml
│   └── prometheus/
│
├── data/                           # 데이터 저장소
│   ├── raw/                        # 원본 데이터
│   │   ├── train.gz
│   │   ├── test.gz
│   │   └── sampleSubmission.gz
│   ├── sample/                     # 테스트 샘플
│   │   ├── train_sample_1k.csv
│   │   ├── train_sample_10k.csv
│   │   └── train_sample_50k.csv
│   ├── processed/                  # 처리된 데이터
│   └── checkpoints/                # Flink 체크포인트
│
├── src/
│   ├── kafka/                      # Kafka Producer
│   │   ├── producer/
│   │   │   ├── main.py
│   │   │   └── config.py
│   │   └── consumers/
│   │       └── dlq_consumer/
│   │
│   ├── flink/                      # Flink 스트리밍
│   │   └── src/
│   │       ├── config.py
│   │       ├── ctr_streaming.py
│   │       └── __init__.py
│   │
│   ├── airflow/                    # Airflow DAG
│   │   ├── config/
│   │   └── dags/
│   │       ├── dag_daily_etl.py
│   │       └── dag_dbt_run.py
│   │
│   ├── redis/                      # Redis 캐시
│   │   └── cache_manager.py
│   │
│   ├── postgres/                   # PostgreSQL 스키마
│   │   └── schema.sql
│   │
│   ├── streamlit/                  # 대시보드
│   │   ├── pages/
│   │   └── dashboard.py
│   │
│   └── analysis/                   # 데이터 분석
│       └── explore_data.ipynb
│
├── dbt/                            # dbt 변환 레이어
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   └── tests/
│
├── schemas/                        # Avro 스키마
│   └── ad_event.avsc
│
├── monitoring/                     # 모니터링
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── rules/
│   └── grafana/
│       ├── dashboards/
│       └── provisioning/
│
├── scripts/                        # 유틸리티 스크립트
│   ├── init_project.sh
│   ├── create_topics.sh
│   └── init_db.sql
│
└── docs/                           # 문서
    ├── plan/                       # 개발 계획
    │   ├── 1week/README.md
    │   ├── 2week/README.md
    │   └── 3week/README.md
    ├── data/
    │   └── eda_report.md           # EDA 분석 보고서
    ├── architecture/
    └── Requirements/
```

---

## 📊 데이터 흐름

### 실시간 파이프라인

```
Avazu CSV
    ↓
Kafka Producer (CSV → JSON)
    ↓
Kafka Topic: ad_events_raw
    ↓
Apache Flink
├─ 1분 Tumbling Window (CTR 계산)
├─ 5분 Tumbling Window (CTR 계산)
└─ Event Time + Watermark 처리
    ↓
PostgreSQL realtime.ctr_metrics
    ↓
Redis Cache (5분 TTL)
    ↓
Streamlit 대시보드 (localhost:8501)
```

### 배치 파이프라인

```
Flink → 로컬 파일 (./data/processed)
    ↓
Airflow DAG 트리거 (매일 00:00)
    ↓
dbt Transform
├─ Staging: 원본 정제
├─ Intermediate: 시간별 집계
└─ Marts: 분석용 마트
    ↓
PostgreSQL analytics 스키마
    ↓
Metabase 대시보드 (localhost:3000)
```

### 에러 처리 흐름

```
실패 이벤트
    ↓
DLQ 토픽: ad_events_error
    ↓
DLQ Consumer
├─ Retry 1회 (지수 백오프)
├─ Retry 2회
└─ Retry 3회
    ↓
    ├─ 성공: ad_events_raw로 재전송
    └─ 실패: PostgreSQL errors 저장 + Slack 알림
```

---

## 🚀 빠른 시작

### 1. 사전 요구사항

```bash
# Python 3.10+
# Docker 20.10+
# Docker Compose 2.0+
# 최소 RAM: 16GB (권장 32GB)
# 디스크: 50GB 이상
```

### 2. 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Mac/Linux)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 서비스 실행

```bash
# 전체 서비스 실행
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

### 4. 접속 URL

| 서비스 | URL | 기본 계정 |
|--------|-----|---------|
| Airflow | http://localhost:8080 | airflow / airflow |
| Streamlit | http://localhost:8501 | - |
| Metabase | http://localhost:3000 | admin@example.com / metabase |
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Flink UI | http://localhost:8082 | - |
| PostgreSQL | localhost:5432 | postgres / postgres |

---

## 📈 PostgreSQL 스키마

### realtime 스키마
```sql
-- Flink 실시간 메트릭
CREATE TABLE realtime.ctr_metrics (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    ctr FLOAT,
    impressions INT,
    clicks INT
);
```

### analytics 스키마
```sql
-- dbt 변환 테이블
- stg_ad_events: 정제된 원본 이벤트
- int_hourly_agg: 시간별 집계
- fct_daily_metrics: 일별 KPI
- dim_campaigns: 캠페인 마스터
```

### errors 스키마
```sql
-- 에러 로그
CREATE TABLE errors.dlq_messages (
    message_id VARCHAR,
    error_message TEXT,
    retry_count INT,
    created_at TIMESTAMP
);
```

---

## 🔧 dbt 모델 구조

```
models/
├── staging/
│   └── stg_ad_events.sql          # 원본 데이터 정제
│
├── intermediate/
│   ├── int_hourly_agg.sql         # 시간별 집계
│   └── int_device_stats.sql       # 기기별 통계
│
└── marts/
    ├── fct_daily_metrics.sql      # 일별 KPI (메인 마트)
    ├── dim_campaigns.sql          # 캠페인 마스터
    ├── dim_devices.sql            # 기기 마스터
    └── mart_hourly_ctr.sql        # 시간별 CTR
```

---

## 📡 모니터링

### Prometheus 메트릭
- **Kafka:** broker metrics, topic lag, consumer lag
- **Flink:** task backpressure, checkpoint duration, records/sec
- **PostgreSQL:** connections, query performance
- **System:** CPU, Memory, Disk I/O

### Grafana 대시보드
- 파이프라인 처리량 및 레이턴시
- 에러율 및 DLQ 모니터링
- 데이터 품질 메트릭

### Slack 알림
- Kafka Topic 에러
- Flink 체크포인트 실패
- Airflow DAG 실패
- dbt 테스트 실패

---

## 📋 3주 실행 계획

### Week 1: 데이터 수집 & 스트리밍 기초 ✅ (진행 중)
- [x] 프로젝트 초기 설정
- [x] EDA & 샘플링 완료
- [ ] Kafka + Schema Registry 구축
- [ ] Python Kafka Producer 개발
- [ ] 모니터링 설정

### Week 2: 실시간 처리 & 캐싱
- [ ] PyFlink 스트리밍 작업
- [ ] Window 집계 구현
- [ ] Redis 캐시 구축
- [ ] PostgreSQL 실시간 스키마
- [ ] Streamlit 대시보드

### Week 3: 배치 처리 & 모니터링
- [ ] Airflow DAG 구축
- [ ] dbt 모델 설계
- [ ] DLQ 에러 처리
- [ ] Grafana 대시보드
- [ ] 문서화 & 배포

---

## 📚 문서

- [EDA 분석 보고서](docs/data/eda_report.md) - 데이터 탐색 결과
- [Week 1 계획](docs/plan/1week/README.md) - Day별 상세 가이드
- [Week 2 계획](docs/plan/2week/README.md) - 실시간 처리 계획
- [Week 3 계획](docs/plan/3week/README.md) - 배치 처리 계획

---

## 💡 주요 특징

### 확장성
- Docker Compose로 모든 서비스 컨테이너화
- Kubernetes 배포 가능

### 신뢰성
- DLQ Consumer로 실패 메시지 자동 재처리
- Flink 체크포인트로 정확히 1회 처리 보장
- dbt 테스트로 데이터 품질 검증

### 관찰성
- Prometheus + Grafana로 실시간 모니터링
- Slack 통합으로 즉시 알림
- 자세한 로깅 및 트레이싱

---

## 🔮 향후 확장 계획

### Phase 2: ML 파이프라인
```
Redis (Feature Store)
    ↓
FastAPI (예측 API)
    ↓
MLflow (모델 관리)
    ↓
Model Registry
```

### Phase 3: 클라우드 마이그레이션
```
Local PostgreSQL → AWS RDS / Snowflake
Local Files → AWS S3
Kafka → AWS MSK / Confluent Cloud
dbt profiles.yml target 변경만으로 마이그레이션
```

---

## 📞 문의 & 피드백

- GitHub Issues: [프로젝트 이슈](https://github.com/kkh1902/Marketing_ROAS/issues)
- 문서: [프로젝트 위키](https://github.com/kkh1902/Marketing_ROAS/wiki)

---

## 📝 License

MIT License - 자유롭게 사용, 수정, 배포 가능

---

**마지막 수정:** 2024-12-08
**프로젝트 상태:** Week 1 진행 중 (EDA & Sampling 완료)