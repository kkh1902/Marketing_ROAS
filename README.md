## 📄 README.md

```markdown
# 🎯 Ad Click Pipeline

Kafka, Flink, dbt를 활용한 실시간 광고 클릭 데이터 파이프라인

## 📌 프로젝트 개요

Avazu CTR 데이터셋(40M rows)을 활용한 실시간/배치 하이브리드 데이터 파이프라인입니다.

### 주요 기능
- **실시간 처리**: Kafka → Flink로 1분/5분 단위 CTR 집계
- **배치 처리**: Airflow + dbt로 일별 분석 마트 생성
- **에러 처리**: DLQ Consumer 자동 retry + Slack 알림
- **모니터링**: Prometheus + Grafana 시스템 메트릭

---

## 🏗️ 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Avazu     │────▶│   Kafka     │────▶│   Flink     │
│  train.gz   │     │  Producer   │     │  Streaming  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
            ┌─────────────┐           ┌─────────────┐            ┌─────────────┐
            │  PostgreSQL │           │  로컬 파일   │            │  Checkpoint │
            │  realtime   │           │  ./data     │            │             │
            └──────┬──────┘           └──────┬──────┘            └─────────────┘
                   │                         │
                   ▼                         ▼
            ┌─────────────┐           ┌─────────────┐
            │  Streamlit  │           │   Airflow   │
            │  실시간 CTR  │           │     dbt     │
            └─────────────┘           └──────┬──────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │  PostgreSQL │
                                      │  analytics  │
                                      └──────┬──────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │  Metabase   │
                                      └─────────────┘
```

---

## 🛠️ 기술 스택

| 레이어 | 기술 | 역할 |
|--------|------|------|
| Ingestion | Kafka, Schema Registry | 이벤트 스트리밍, 스키마 관리 |
| Processing | PyFlink | 실시간 윈도우 집계 |
| Orchestration | Airflow | 배치 파이프라인 스케줄링 |
| Transform | dbt | SQL 기반 데이터 모델링 |
| Storage | PostgreSQL | realtime/analytics/errors 스키마 |
| Visualization | Streamlit, Metabase | 실시간/배치 대시보드 |
| Monitoring | Prometheus, Grafana, Slack | 메트릭 수집, 알림 |

---

## 📁 프로젝트 구조

```
ad-click-pipeline/
├── docker-compose.yml
├── data/
│   ├── raw/
│   ├── processed/
│   └── checkpoints/
├── producer/
│   ├── main.py
│   ├── config.py
│   └── requirements.txt
├── flink/
│   └── src/
│       └── ctr_streaming.py
├── airflow/
│   └── dags/
│       ├── dag_daily_etl.py
│       └── dag_dbt_run.py
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       ├── intermediate/
│       └── marts/
├── dlq_consumer/
│   └── main.py
├── streamlit/
│   └── realtime_dashboard.py
├── prometheus/
│   └── prometheus.yml
├── grafana/
│   └── dashboards/
└── scripts/
    └── init_db.sql
```

---

## 🚀 실행 방법

### 1. 사전 요구사항

- Docker 20.10+
- Docker Compose 2.0+
- 최소 RAM 16GB (권장 32GB)

### 2. 데이터 다운로드

```bash
# Kaggle에서 Avazu 데이터셋 다운로드
kaggle competitions download -c avazu-ctr-prediction
unzip avazu-ctr-prediction.zip -d data/raw/
```

### 3. 서비스 실행

```bash
# 전체 서비스 실행
docker-compose up -d

# 상태 확인
docker-compose ps
```

### 4. 접속 URL

| 서비스 | URL |
|--------|-----|
| Airflow | http://localhost:8080 |
| Streamlit | http://localhost:8501 |
| Metabase | http://localhost:3000 |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
| Flink UI | http://localhost:8082 |

---

## 📊 데이터 흐름

### 실시간 파이프라인

```
Avazu CSV → Kafka Producer → ad_events_raw 토픽
    → Flink (1분/5분 Tumbling Window)
    → PostgreSQL realtime.ctr_metrics
    → Streamlit 대시보드
```

### 배치 파이프라인

```
Flink → 로컬 파일 (./data/processed)
    → Airflow dag_daily_etl
    → dbt transform
    → PostgreSQL analytics 스키마
    → Metabase 대시보드
```

### 에러 처리 흐름

```
실패 이벤트 → DLQ 토픽 (ad_events_error)
    → DLQ Consumer (retry 3회)
    → 성공: 원본 토픽으로 재전송
    → 실패: PostgreSQL errors 저장 + Slack 알림
```

---

## 📈 PostgreSQL 스키마

| 스키마 | 용도 | 주요 테이블 |
|--------|------|-------------|
| `realtime` | Flink 실시간 메트릭 | `ctr_metrics` |
| `analytics` | dbt 마트 | `stg_ad_events`, `fct_daily_metrics` |
| `errors` | DLQ 에러 로그 | `dlq_messages` |

---

## 🔧 dbt 모델

```
models/
├── staging/
│   └── stg_ad_events.sql        # 원본 정제
├── intermediate/
│   └── int_hourly_agg.sql       # 시간별 집계
└── marts/
    ├── fct_daily_metrics.sql    # 일별 KPI
    └── dim_campaigns.sql        # 캠페인 마스터
```

---

## 📡 모니터링

### Grafana 대시보드
- Kafka: Lag, Throughput, ISR
- Flink: Checkpoint, Backpressure, Records/sec

### Slack 알림
- DLQ retry 실패
- Airflow DAG 실패
- dbt test 실패

---

## 🔮 향후 확장 계획

### ML 파이프라인 추가
```
Redis (Feature Store) → FastAPI (예측 API) → MLflow (모델 관리)
```

### 클라우드 마이그레이션
```
PostgreSQL → Snowflake/Redshift
로컬 파일 → S3
dbt profiles.yml target만 변경
```

---

## 📝 License

MIT License
```

---

파일로 저장해줄까?