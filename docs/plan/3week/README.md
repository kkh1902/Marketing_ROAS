# Week 3: 배치 처리 & 모니터링 & 분석 대시보드

**목표:** Airflow 배치 스케줄링, dbt 데이터 변환, Streamlit 분석 대시보드, Grafana 모니터링을 구축하여 완전한 데이터 파이프라인 완성

**기간:** 5일 (월~금)
**일일 분량:** 2시간
**총 시간:** 10시간

---

## 📅 주간 일정표

| 단계 | 주제 | 시간 | 누적 |
|------|------|------|------|
| **월** | PostgreSQL + 배치 DB 설계 | 2h | 2h |
| **화** | Airflow DAG 및 스케줄링 | 2h | 4h |
| **수** | dbt 모델 개발 및 테스트 | 2h | 6h |
| **목** | Streamlit 대시보드 개발 | 2h | 8h |
| **금** | Grafana 모니터링 + 최종 통합 | 2h | 10h |

---

## 📌 Day 1 (월): PostgreSQL + 배치 DB 설계 (2시간)

### 목표
- PostgreSQL Docker 환경 구축
- 배치 처리용 데이터베이스 스키마 설계
- 실시간/배치 데이터 저장 테이블 생성
- 성능 최적화 (인덱스, 파티셔닝)

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| PostgreSQL Docker 구성 | 30분 |
| 스키마 설계 | 40분 |
| DDL 작성 및 실행 | 40분 |
| 검증 및 문서화 | 10분 |

### 🛠️ 실습 내용

#### 1-1. PostgreSQL Docker 설정 (15분)

**파일:** `docker-compose.yml` (업데이트)

```yaml
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: marketing_roas
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_postgres.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"
    networks:
      - kafka-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

**실행:**
```bash
docker-compose up -d postgres
docker-compose logs -f postgres
```

#### 1-2. 데이터베이스 스키마 설계 (25분)

**파일:** `scripts/init_postgres.sql`

```sql
-- ============================================================
-- DATABASE & SCHEMA CREATION
-- ============================================================

-- Realtime 스키마 (실시간 메트릭)
CREATE SCHEMA IF NOT EXISTS realtime;

-- Analytics 스키마 (분석용 마트)
CREATE SCHEMA IF NOT EXISTS analytics;

-- Errors 스키마 (DLQ 메시지)
CREATE SCHEMA IF NOT EXISTS errors;

-- ============================================================
-- REALTIME SCHEMA TABLES (실시간 메트릭)
-- ============================================================

-- 1. 광고 이벤트 테이블
CREATE TABLE IF NOT EXISTS realtime.ad_events (
    id BIGINT PRIMARY KEY,
    click SMALLINT NOT NULL,
    hour INTEGER NOT NULL,
    banner_pos SMALLINT,
    site_id VARCHAR(100),
    site_domain VARCHAR(100),
    site_category VARCHAR(100),
    app_id VARCHAR(100),
    app_domain VARCHAR(100),
    app_category VARCHAR(100),
    device_id VARCHAR(100),
    device_ip VARCHAR(50),
    device_model VARCHAR(100),
    device_type SMALLINT,
    device_conn_type SMALLINT,
    c1 SMALLINT,
    c14 SMALLINT,
    c15 SMALLINT,
    c16 SMALLINT,
    c17 SMALLINT,
    c18 SMALLINT,
    c19 SMALLINT,
    c20 SMALLINT,
    c21 SMALLINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_ad_events_hour ON realtime.ad_events(hour);
CREATE INDEX idx_ad_events_device_type ON realtime.ad_events(device_type);
CREATE INDEX idx_ad_events_created_at ON realtime.ad_events(created_at);

-- 2. 시간별 집계 테이블
CREATE TABLE IF NOT EXISTS realtime.hourly_stats (
    hour INTEGER PRIMARY KEY,
    impression_count BIGINT NOT NULL,
    click_count BIGINT NOT NULL,
    ctr DECIMAL(5, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ANALYTICS SCHEMA TABLES (배치 처리용 마트)
-- ============================================================

-- 1. Fact: 일일 집계
CREATE TABLE IF NOT EXISTS analytics.fact_daily_agg (
    date DATE,
    device_type SMALLINT,
    impressions BIGINT,
    clicks BIGINT,
    ctr DECIMAL(5, 2),
    PRIMARY KEY (date, device_type)
);

-- ============================================================
-- ERRORS SCHEMA TABLES (DLQ 에러 추적)
-- ============================================================

CREATE TABLE IF NOT EXISTS errors.dlq_messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(100),
    topic VARCHAR(100),
    partition INTEGER,
    offset BIGINT,
    message_content TEXT,
    error_reason VARCHAR(500),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_dlq_messages_received_at ON errors.dlq_messages(received_at);
```

**실행:**
```bash
docker-compose exec postgres psql -U postgres -d marketing_roas < scripts/init_postgres.sql
```

#### 1-3. 스키마 검증 (10분)

```bash
docker-compose exec postgres psql -U postgres -d marketing_roas -c "\dt realtime.*"
docker-compose exec postgres psql -U postgres -d marketing_roas -c "\dt analytics.*"
```

### ✅ 완료 기준

- [ ] PostgreSQL 컨테이너 정상 실행
- [ ] 3개 스키마 생성 (realtime, analytics, errors)
- [ ] 모든 테이블 생성 완료
- [ ] 데이터 삽입 테스트 성공

### 📊 산출물

```
scripts/
└── init_postgres.sql

docker-compose.yml (업데이트)
```

---

## 📌 Day 2 (화): Airflow DAG 및 스케줄링 (2시간)

### 목표
- Airflow Docker 환경 구축
- DAG (Directed Acyclic Graph) 정의
- 일일 배치 스케줄링 설정
- 의존성 관리

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| Airflow Docker 구성 | 30분 |
| DAG 작성 | 60분 |
| 스케줄링 설정 | 20분 |
| 테스트 | 10분 |

### 🛠️ 실습 내용

#### 2-1. Airflow Docker 설정 (20분)

**파일:** `docker-compose.yml` (업데이트)

```yaml
  airflow-postgres:
    image: postgres:15-alpine
    container_name: airflow-postgres
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - airflow_postgres_data:/var/lib/postgresql/data
    networks:
      - kafka-network

  airflow-webserver:
    image: apache/airflow:2.7.3-python3.11
    container_name: airflow-webserver
    environment:
      AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@airflow-postgres:5432/airflow
      AIRFLOW__CORE__LOAD_EXAMPLES: 'False'
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags:rw
    depends_on:
      airflow-postgres:
        condition: service_started
    networks:
      - kafka-network
    command: webserver

  airflow-scheduler:
    image: apache/airflow:2.7.3-python3.11
    container_name: airflow-scheduler
    environment:
      AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@airflow-postgres:5432/airflow
      AIRFLOW__CORE__LOAD_EXAMPLES: 'False'
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    volumes:
      - ./dags:/opt/airflow/dags:rw
    depends_on:
      airflow-postgres:
        condition: service_started
    networks:
      - kafka-network
    command: scheduler

volumes:
  airflow_postgres_data:
```

**초기화:**
```bash
docker-compose exec airflow-webserver airflow db init
docker-compose exec airflow-webserver airflow users create \
    --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin
```

#### 2-2. DAG 작성 (40분)

**파일:** `dags/dag_daily_etl.py`

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.postgres_operator import PostgresOperator

default_args = {
    'owner': 'data-team',
    'start_date': datetime(2025, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'dag_daily_etl',
    default_args=default_args,
    description='Daily ETL: Data validation',
    schedule_interval='0 2 * * *',
    catchup=False,
)

def check_data_quality(**context):
    from sqlalchemy import create_engine
    engine = create_engine('postgresql://postgres:postgres@postgres:5432/marketing_roas')
    result = engine.execute("SELECT COUNT(*) FROM realtime.ad_events WHERE created_at >= CURRENT_DATE")
    print(f"Today's records: {result}")

check_quality = PythonOperator(
    task_id='check_data_quality',
    python_callable=check_data_quality,
    dag=dag,
)
```

**파일:** `dags/dag_dbt_run.py`

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data-team',
    'start_date': datetime(2025, 1, 1),
    'retries': 2,
}

dag = DAG(
    'dag_dbt_run',
    default_args=default_args,
    schedule_interval='0 3 * * *',
    catchup=False,
)

dbt_run = BashOperator(
    task_id='dbt_run',
    bash_command='cd /opt/dbt && dbt run',
    dag=dag,
)

dbt_test = BashOperator(
    task_id='dbt_test',
    bash_command='cd /opt/dbt && dbt test',
    dag=dag,
)

dbt_run >> dbt_test
```

### ✅ 완료 기준

- [ ] Airflow Webserver 정상 실행 (localhost:8080)
- [ ] 2개 DAG 생성 (dag_daily_etl, dag_dbt_run)
- [ ] DAG 스케줄링 설정 확인
- [ ] 오류 없음

### 📊 산출물

```
dags/
├── dag_daily_etl.py
└── dag_dbt_run.py

docker-compose.yml (업데이트)
```

---

## 📌 Day 3 (수): dbt 모델 개발 및 테스트 (2시간)

### 목표
- dbt 프로젝트 초기화
- Staging 모델 작성 (데이터 정제)
- Mart 모델 작성 (비즈니스 로직)
- 테스트 실행

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| dbt 프로젝트 설정 | 20분 |
| Staging 모델 | 40분 |
| Mart 모델 | 40분 |
| 테스트 | 20분 |

### 🛠️ 실습 내용

#### 3-1. dbt 프로젝트 설정 (15분)

```bash
dbt init marketing_roas_dbt -d postgres
```

**파일:** `dbt/dbt_project.yml`

```yaml
name: 'marketing_roas'
version: '1.0.0'
profile: 'marketing_roas'
model-paths: ["models"]
```

**파일:** `dbt/profiles.yml`

```yaml
marketing_roas:
  target: dev
  outputs:
    dev:
      type: postgres
      host: postgres
      user: postgres
      password: postgres
      dbname: marketing_roas
      schema: analytics
      threads: 4
```

#### 3-2. Staging 모델 (25분)

**파일:** `dbt/models/staging/stg_ad_events.sql`

```sql
SELECT
    id,
    click,
    hour,
    device_type,
    created_at
FROM {{ source('realtime', 'ad_events') }}
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
```

#### 3-3. Mart 모델 (25분)

**파일:** `dbt/models/marts/fct_daily_agg.sql`

```sql
SELECT
    CURRENT_DATE as date,
    device_type,
    COUNT(*) as impressions,
    SUM(CASE WHEN click = 1 THEN 1 ELSE 0 END) as clicks,
    ROUND(SUM(CASE WHEN click = 1 THEN 1 ELSE 0 END)::float / COUNT(*) * 100, 2) as ctr
FROM {{ ref('stg_ad_events') }}
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY device_type
```

**실행:**
```bash
cd dbt
dbt run
dbt test
```

### ✅ 완료 기준

- [ ] dbt 프로젝트 생성
- [ ] Staging 모델 실행 성공
- [ ] Mart 모델 실행 성공
- [ ] PostgreSQL에서 테이블 확인

### 📊 산출물

```
dbt/
├── dbt_project.yml
├── profiles.yml
├── models/
│   ├── staging/
│   │   └── stg_ad_events.sql
│   └── marts/
│       └── fct_daily_agg.sql
└── tests/
```

---

## 📌 Day 4 (목): Streamlit 대시보드 개발 (2시간)

### 목표
- Streamlit 애플리케이션 초기 설정
- PostgreSQL 데이터 시각화
- 실시간 메트릭 대시보드
- 인터랙티브 필터

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| Streamlit 구조 설계 | 20분 |
| DB 연결 모듈 | 30분 |
| 대시보드 UI | 50분 |
| 배포 설정 | 20분 |

### 🛠️ 실습 내용

#### 4-1. Streamlit 프로젝트 (10분)

```bash
mkdir -p streamlit && cd streamlit
python -m venv venv
source venv/bin/activate
pip install streamlit pandas plotly sqlalchemy psycopg2-binary
```

**폴더 구조:**
```
streamlit/
├── app.py
├── pages/
│   ├── 01_Overview.py
│   └── 02_Realtime.py
├── components/
│   └── metrics.py
└── requirements.txt
```

#### 4-2. 메인 앱 (30분)

**파일:** `streamlit/app.py`

```python
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

st.set_page_config(page_title="Marketing ROAS", layout="wide")

@st.cache_resource
def get_db_engine():
    return create_engine('postgresql://postgres:postgres@postgres:5432/marketing_roas')

st.title("📊 Marketing ROAS Dashboard")

engine = get_db_engine()
result = pd.read_sql("""
SELECT COUNT(*) as total, SUM(CASE WHEN click = 1 THEN 1 ELSE 0 END) as clicks,
       ROUND(SUM(CASE WHEN click = 1 THEN 1 ELSE 0 END)::float / COUNT(*) * 100, 2) as ctr
FROM realtime.ad_events WHERE created_at >= CURRENT_DATE
""", engine)

col1, col2, col3 = st.columns(3)
col1.metric("Total Events", f"{result['total'][0]:,}")
col2.metric("Clicks", f"{result['clicks'][0]:,}")
col3.metric("CTR", f"{result['ctr'][0]:.2f}%")

st.subheader("Hourly Statistics")
hourly_data = pd.read_sql("""
SELECT hour, impression_count, click_count, ctr
FROM realtime.hourly_stats ORDER BY hour DESC LIMIT 24
""", engine)

fig = px.line(hourly_data, x='hour', y='ctr', title='CTR by Hour')
st.plotly_chart(fig, use_container_width=True)
```

#### 4-3. Docker 구성 (10분)

**docker-compose.yml 추가:**
```yaml
  streamlit:
    image: python:3.11-slim
    container_name: streamlit
    working_dir: /app
    volumes:
      - ./streamlit:/app
    ports:
      - "8501:8501"
    command: bash -c "pip install -r requirements.txt && streamlit run app.py"
    depends_on:
      - postgres
    networks:
      - kafka-network
```

**실행:**
```bash
docker-compose up -d streamlit
# http://localhost:8501
```

### ✅ 완료 기준

- [ ] Streamlit 앱 실행 (localhost:8501)
- [ ] PostgreSQL 연결 성공
- [ ] 메트릭 표시 확인
- [ ] 차트 렌더링 확인

### 📊 산출물

```
streamlit/
├── app.py
├── pages/
│   ├── 01_Overview.py
│   └── 02_Realtime.py
└── requirements.txt

docker-compose.yml (업데이트)
```

---

## 📌 Day 5 (금): Grafana 모니터링 + 최종 통합 (2시간)

### 목표
- Grafana 대시보드 구성
- Prometheus 메트릭 연동
- Kafka/PostgreSQL 모니터링
- 전체 E2E 테스트

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| Grafana Docker 구성 | 20분 |
| 대시보드 구성 | 40분 |
| 알람 규칙 | 20분 |
| E2E 테스트 | 40분 |

### 🛠️ 실습 내용

#### 5-1. Grafana Docker 설정 (15분)

**docker-compose.yml 추가:**
```yaml
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_USERS_ALLOW_SIGN_UP: 'false'
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - kafka-network

volumes:
  grafana_data:
```

**실행:**
```bash
docker-compose up -d grafana
# http://localhost:3000 (admin/admin)
```

#### 5-2. Prometheus 데이터소스 (15분)

Grafana에서:
1. Configuration > Data Sources
2. Add Prometheus
3. URL: http://prometheus:9090
4. Save & test

#### 5-3. Kafka 대시보드 (25분)

**Grafana UI에서 새 대시보드 생성:**
- 메시지 처리량
- 토픽별 메시지 수
- Producer/Consumer lag

#### 5-4. E2E 통합 테스트 (20분)

**파일:** `scripts/e2e_test.sh`

```bash
#!/bin/bash

echo "=========================================="
echo "WEEK 3 E2E TEST"
echo "=========================================="

echo "1. Checking services..."
docker-compose ps

echo "2. Checking PostgreSQL..."
docker-compose exec postgres psql -U postgres -d marketing_roas -c "SELECT COUNT(*) FROM realtime.ad_events;"

echo "3. Running dbt..."
docker-compose exec dbt dbt run

echo "4. Checking Airflow..."
docker-compose exec airflow-webserver airflow dags list

echo "5. Testing Streamlit..."
curl http://localhost:8501

echo "6. Testing Grafana..."
curl http://localhost:3000

echo "=========================================="
echo "✅ WEEK 3 E2E TEST COMPLETE"
echo "=========================================="
```

### ✅ 완료 기준

- [ ] Grafana 접속 가능 (localhost:3000)
- [ ] Prometheus 데이터소스 연결
- [ ] Kafka 대시보드 표시
- [ ] PostgreSQL 데이터 확인
- [ ] dbt 모델 생성 완료
- [ ] Airflow DAG 정상 작동
- [ ] Streamlit 데이터 로드 완료
- [ ] E2E 테스트 통과

### 📊 산출물

```
docker-compose.yml (최종)

scripts/
├── init_postgres.sql
└── e2e_test.sh
```

---

## 🎓 Week 3 핵심 학습 내용

### 기술
✅ PostgreSQL 스키마 설계
✅ Airflow DAG 및 스케줄링
✅ dbt 데이터 변환
✅ Streamlit 대시보드
✅ Grafana 모니터링

### 시스템
✅ 배치 처리 아키텍처
✅ 데이터 웨어하우스 설계
✅ 실시간 + 배치 통합
✅ 모니터링 및 알람

---

## ✅ 전체 체크리스트

### PostgreSQL
- [ ] Docker 컨테이너 실행
- [ ] 3개 스키마 생성
- [ ] 테이블 생성
- [ ] 인덱스 생성

### Airflow
- [ ] Webserver 실행 (localhost:8080)
- [ ] 2개 DAG 생성
- [ ] 스케줄링 확인

### dbt
- [ ] 프로젝트 초기화
- [ ] Staging 모델 완성
- [ ] Mart 모델 완성

### Streamlit
- [ ] 앱 실행 (localhost:8501)
- [ ] PostgreSQL 연결
- [ ] 메트릭 표시

### Grafana
- [ ] 앱 실행 (localhost:3000)
- [ ] Prometheus 연동
- [ ] 대시보드 생성

---

## 📊 Week 3 최종 산출물

```
Week 3 Complete
├── docker-compose.yml
├── scripts/
│   ├── init_postgres.sql
│   └── e2e_test.sh
├── dags/
│   ├── dag_daily_etl.py
│   └── dag_dbt_run.py
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
└── streamlit/
    ├── app.py
    └── requirements.txt
```

---

**작성 일시:** 2025-12-13
**담당자:** Data Engineering Team
**상태:** ✅ 최종 설계 완료

**다음 단계:** 프로덕션 배포 & 자동화
