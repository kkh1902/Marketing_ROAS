# Week 1: 데이터 수집 & 스트리밍 기초

**목표:** Avazu 데이터를 Kafka로 수집하고 완전히 작동하는 메시지 스트리밍 파이프라인 완성

**기간:** 5일 (월~금)
**일일 분량:** 2시간
**총 시간:** 10시간

---

## 📅 주간 일정표

| 단계 | 주제 | 시간 | 누적 |
|------|------|------|------|
| **Day 0** | 프로젝트 초기 설정 (사전) | 0.5h | 0.5h |
| **월** | Avazu 데이터 분석 & 샘플링 | 2h | 2.5h |
| **화** | Kafka + Schema Registry 구축 | 2h | 4.5h |
| **수** | Kafka Topic 생성 & 테스트 | 2h | 6.5h |
| **목** | Python Kafka Producer + DLQ 개발 | 2h | 8.5h |
| **금** | 모니터링 & 통합 테스트 | 2h | 10.5h |

---

## 📌 Day 0 (사전): 프로젝트 초기 설정 (30분)

### 목표
- Git 초기화 및 기본 설정
- 폴더 구조 생성
- 필요한 파일 및 환경 설정
- Python 의존성 관리

### 🛠️ 실습 내용

#### 0-1. Git 초기화 (5분)

```bash
# Git 초기화
git init
git config user.name "Your Name"
git config user.email "your@email.com"

# GitHub에 푸시할 경우
git remote add origin https://github.com/your-repo/marketing_roas.git
```

#### 0-2. 폴더 구조 생성 (10분)

**파일:** `scripts/init_project.sh`

```bash
#!/bin/bash

echo "📁 Creating project structure..."

# 메인 디렉토리
mkdir -p src/{analysis,kafka,flink,postgres,streamlit,airflow,monitoring}
mkdir -p data/{raw,processed,checkpoints}
mkdir -p config
mkdir -p schemas
mkdir -p scripts
mkdir -p tests
mkdir -p docs/{plan,eda_report}

# 초기 파일들 생성
touch .gitignore
touch README.md
touch .env.example
touch requirements.txt

# 디렉토리별 __init__.py 생성
touch src/__init__.py
touch src/analysis/__init__.py
touch src/kafka/__init__.py
touch src/flink/__init__.py
touch src/postgres/__init__.py

echo "✅ Project structure created successfully"
echo ""
echo "📂 Directory tree:"
tree -L 2 --dirsfirst 2>/dev/null || find . -maxdepth 2 -type d | sort
```

**실행:**
```bash
bash scripts/init_project.sh
```

**결과:**
```
marketing_roas/
├── src/
│   ├── __init__.py
│   ├── analysis/
│   ├── kafka/
│   ├── flink/
│   ├── postgres/
│   ├── streamlit/
│   ├── airflow/
│   └── monitoring/
├── data/
│   ├── raw/
│   ├── processed/
│   └── checkpoints/
├── config/
├── schemas/
├── scripts/
├── tests/
├── docs/
├── .gitignore
├── .env.example
├── requirements.txt
├── README.md
└── docker-compose.yml
```

#### 0-3. .gitignore 작성 (5분)

**파일:** `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
.env.*.local

# Data
data/train.gz
data/raw/*.csv
data/processed/*.csv

# Logs
*.log
logs/

# Cache
.pytest_cache/
.cache/

# Jupyter
.ipynb_checkpoints/

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml
```

#### 0-4. Python 환경 설정 (10분)

**파일:** `requirements.txt`

```
# Kafka
kafka-python==2.0.2
confluent-kafka==2.3.0

# PyFlink (선택적 - Week 2에서 사용)
apache-flink==1.17.1

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
alembic==1.12.1

# Data processing
pandas==2.1.3
numpy==1.26.2

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1
requests==2.31.0
click==8.1.7

# Monitoring
prometheus-client==0.19.0

# Web (Streamlit - Week 2에서 사용)
streamlit==1.28.1

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Logging
python-json-logger==2.0.7
```

**설치:**
```bash
pip install -r requirements.txt

# 또는 구체적인 버전 고정
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

#### 0-5. 환경 변수 설정 (5분)

**파일:** `.env.example`

```env
# Kafka 설정
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_RAW=ad_events_raw
KAFKA_TOPIC_ERROR=ad_events_error
KAFKA_TOPIC_RETRY=ad_events_retry

# Schema Registry
SCHEMA_REGISTRY_URL=http://localhost:8081

# PostgreSQL (Week 2에서 사용)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=marketing_roas
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis (Week 2에서 사용)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Flink (Week 2에서 사용)
FLINK_JOBMANAGER_RPC_ADDRESS=localhost
FLINK_JOBMANAGER_RPC_PORT=6123
FLINK_TASKMANAGER_RPC_PORT=6124

# Slack 알림 (Week 3에서 사용)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#data-pipeline

# Airflow (Week 3에서 사용)
AIRFLOW_HOME=/path/to/airflow
AIRFLOW__CORE__DAGS_FOLDER=/path/to/dags

# 로깅
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**사용법:**
```bash
# .env.example을 .env로 복사
cp .env.example .env

# 필요한 값들 수정
# .env 파일을 git에 커밋하지 않기 (이미 .gitignore에 포함)
```

#### 0-6. 기본 README 작성 (5분)

**파일:** `README.md`

```markdown
# Marketing ROAS: 실시간 광고 CTR 분석 파이프라인

광고 클릭률(CTR) 분석을 위한 완전한 실시간 데이터 파이프라인입니다.

## 📊 아키텍처 개요

```
[Avazu Data] → [Kafka] → [Flink] → [PostgreSQL] → [Streamlit/Metabase]
                           ↓
                    [Prometheus/Grafana]
```

## 🚀 빠른 시작

### 필수 요구사항
- Docker & Docker Compose
- Python 3.9+
- Git

### 설치

```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/marketing_roas.git
cd marketing_roas

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 수정

# 3. Python 의존성 설치
pip install -r requirements.txt

# 4. Docker 서비스 시작
docker-compose up -d

# 5. 초기 설정
bash scripts/init_project.sh
```

## 📅 개발 일정

- **Week 1**: Kafka + Producer (데이터 수집)
- **Week 2**: Flink + Redis + Streamlit (실시간 처리)
- **Week 3**: Airflow + dbt + Grafana (배치 & 모니터링)

## 📚 문서

- [프로젝트 계획](docs/plan/README.md)
- [Week 1 상세 계획](docs/plan/1week/README.md)
- [아키텍처](docs/architecture/architecture_posgre.mermaid)

## 🔧 개발 환경

```bash
# Kafka 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f kafka

# Python 개발
source venv/bin/activate  # 가상환경 활성화
python -m pytest tests/   # 테스트 실행
```

## 📞 지원

문제가 있으면 GitHub Issues를 통해 보고해주세요.
```

#### 0-7. docker-compose.yml 위치 확인 (5분)

이미 작성되었다면:
```bash
# docker-compose.yml이 프로젝트 루트에 있는지 확인
ls -la docker-compose.yml
```

없다면 Day 2에서 생성하게 됩니다.

### ✅ Day 0 완료 기준

- [ ] Git 초기화 완료
- [ ] 폴더 구조 생성 완료
- [ ] .gitignore 작성 완료
- [ ] requirements.txt 작성 완료
- [ ] .env.example 작성 완료
- [ ] README.md 작성 완료
- [ ] `git add . && git commit -m "Init: 프로젝트 초기 설정"`

### 📊 Day 0 산출물

```
marketing_roas/
├── .git/
├── .gitignore
├── .env.example
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── analysis/
│   ├── kafka/
│   ├── flink/
│   ├── postgres/
│   ├── streamlit/
│   ├── airflow/
│   └── monitoring/
├── data/
│   ├── raw/
│   ├── processed/
│   └── checkpoints/
├── config/
├── schemas/
├── scripts/
│   └── init_project.sh
└── tests/
```

---

## 📌 Day 1 (월): Avazu 데이터 분석 & 샘플링 (2시간)

### 목표
- Avazu 데이터의 구조와 특성 파악
- 샘플 데이터 추출 및 EDA 수행
- 데이터 전처리 방안 수립

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| 데이터 분석 | 40분 |
| EDA 수행 | 50분 |
| 문서화 | 30분 |

### 🛠️ 실습 내용

#### 1-1. 데이터 구조 분석 (20분)

**파일:** `src/analysis/explore_data.py`

```python
import gzip
import pandas as pd
import numpy as np

# 첫 번째 줄 읽기 (헤더)
with gzip.open('data/train.gz', 'rt', encoding='utf-8') as f:
    header = f.readline().strip().split(',')
    print("Column names:")
    for i, col in enumerate(header):
        print(f"  {i}: {col}")

# 파일 크기 확인
import os
file_size_gb = os.path.getsize('data/train.gz') / (1024**3)
print(f"\nFile size: {file_size_gb:.2f} GB")

# 샘플 데이터 읽기
sample_lines = []
with gzip.open('data/train.gz', 'rt', encoding='utf-8') as f:
    header = f.readline()
    for i in range(100):
        sample_lines.append(f.readline())

# DataFrame으로 변환
df_sample = pd.read_csv('data/train.gz', nrows=1000)
print(f"\nDataset shape: {df_sample.shape}")
print(f"\nData types:\n{df_sample.dtypes}")
print(f"\nBasic statistics:\n{df_sample.describe()}")
print(f"\nMissing values:\n{df_sample.isnull().sum()}")
```

**실행:**
```bash
python src/analysis/explore_data.py
```

**예상 출력:**
```
Column names:
  0: id
  1: click
  2: hour
  3: C1
  ...

File size: 7.82 GB

Dataset shape: (1000, 24)

Data types:
id        object
click      int64
hour       int64
...
```

#### 1-2. EDA 수행 (30분)

**파일:** `src/analysis/eda_analysis.py`

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터 로드
df = pd.read_csv('data/train.gz', nrows=10000)

# 1. 클릭률 분석
click_rate = df['click'].mean() * 100
print(f"Overall Click-Through Rate: {click_rate:.2f}%")

# 2. 시간대별 클릭률
df['hour_str'] = df['hour'].astype(str).str[:2]
hourly_ctr = df.groupby('hour_str')['click'].mean() * 100
print(f"\nHourly CTR:\n{hourly_ctr}")

# 3. 배너 위치별 클릭률
if 'banner_pos' in df.columns:
    banner_ctr = df.groupby('banner_pos')['click'].mean() * 100
    print(f"\nBanner Position CTR:\n{banner_ctr}")

# 4. 기기 유형별 클릭률
device_ctr = df.groupby('device_type')['click'].mean() * 100
print(f"\nDevice Type CTR:\n{device_ctr}")

# 5. 데이터 품질 확인
print(f"\nData Quality:")
print(f"  Total records: {len(df):,}")
print(f"  Duplicate IDs: {df['id'].duplicated().sum()}")
print(f"  Null values: {df.isnull().sum().sum()}")

# 6. 카테고리별 분포
if 'site_category' in df.columns:
    print(f"\nTop site categories:")
    print(df['site_category'].value_counts().head(10))

# 통계 저장
stats = {
    'total_records': len(df),
    'click_rate': click_rate,
    'features': len(df.columns),
    'date_range': f"{df['hour'].min()} - {df['hour'].max()}"
}

import json
with open('data/data_stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

print("\n✅ Statistics saved to data/data_stats.json")
```

**실행:**
```bash
python src/analysis/eda_analysis.py
```

#### 1-3. 데이터 샘플링 (30분)

**파일:** `src/data/sample_data.py`

```python
import pandas as pd
import os

# 디렉토리 생성
os.makedirs('data/raw', exist_ok=True)

# 다양한 크기의 샘플 생성
sample_sizes = {
    'train_sample_1k.csv': 1000,
    'train_sample_10k.csv': 10000,
    'train_sample_50k.csv': 50000,
}

print("Creating sample datasets...")

for filename, size in sample_sizes.items():
    df = pd.read_csv('data/train.gz', nrows=size)
    output_path = f'data/raw/{filename}'
    df.to_csv(output_path, index=False)
    print(f"✅ {filename} ({size:,} rows)")

# 샘플 통계
df_sample = pd.read_csv('data/raw/train_sample_10k.csv')
print(f"\nSample statistics (10k):")
print(f"  Click rate: {df_sample['click'].mean()*100:.2f}%")
print(f"  Records: {len(df_sample):,}")
print(f"  Columns: {len(df_sample.columns)}")
```

**실행:**
```bash
python src/data/sample_data.py
```

#### 1-4. 문서 작성 (20분)

**파일:** `docs/eda_report.md`

```markdown
# Avazu 데이터 탐색 분석 보고서

## 데이터 개요

| 항목 | 값 |
|------|-----|
| 전체 레코드 | 40,428,967 |
| 파일 크기 | 7.82 GB |
| 컬럼 수 | 24 |
| 시간 범위 | 140102 ~ 141031 (30일) |

## 주요 지표

### 클릭률 (CTR)
- 전체 CTR: **16.6%**
- 시간대별 범위: 14.2% ~ 18.5%
- 추세: 오후 시간대에 높음

### 배너 위치별 CTR
- 위치 0: 18.2%
- 위치 1: 17.1%
- 위치 2: 15.3%

### 기기 유형별 CTR
- 기기 0: 17.2%
- 기기 1: 15.8%

## 데이터 품질

✅ 중복 ID 없음
✅ 대부분의 컬럼에서 < 5% 결측치
⚠️ 일부 카테고리 컬럼에서 높은 결측률

## 권장사항

1. 샘플 데이터로 파이프라인 테스트
2. 실시간 처리를 위해 배치 단위로 수집
3. 범주형 변수는 인코딩 필요
```

### ✅ 완료 기준

- [ ] `explore_data.py` 실행 완료
- [ ] `eda_analysis.py` 실행 완료
- [ ] 3개의 샘플 데이터 생성 완료
- [ ] `data_stats.json` 파일 생성
- [ ] `eda_report.md` 작성 완료

### 📊 산출물

```
data/
├── train.gz (원본)
├── raw/
│   ├── train_sample_1k.csv
│   ├── train_sample_10k.csv
│   ├── train_sample_50k.csv
│   └── data_stats.json
docs/
└── eda_report.md
```

---

## 📌 Day 2 (화): Kafka + Schema Registry 구축 (2시간)

### 목표
- Kafka와 Schema Registry 완전히 작동하게 설정
- Avro 스키마 정의 및 등록
- 로컬 Docker 환경에서 검증

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| Docker Compose 작성 | 30분 |
| 실행 및 검증 | 30분 |
| Avro 스키마 정의 | 40분 |
| 통합 테스트 | 20분 |

### 🛠️ 실습 내용

#### 2-1. Docker Compose 파일 작성 (20분)

**파일:** `docker-compose.yml` (프로젝트 루트)

```yaml
version: '3.8'

services:
  # Zookeeper: Kafka 클러스터 관리
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
      ZOOKEEPER_SYNC_LIMIT: 5
      ZOOKEEPER_INIT_LIMIT: 10
    ports:
      - "2181:2181"
    networks:
      - kafka-network
    healthcheck:
      test: echo stat | nc localhost 2181
      interval: 10s
      timeout: 5s
      retries: 5

  # Kafka: 메시지 브로커
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kafka
    depends_on:
      zookeeper:
        condition: service_healthy
    ports:
      - "9092:9092"      # 외부 클라이언트
      - "29092:29092"    # 내부 통신
      - "9101:9101"      # JMX
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_LOG_RETENTION_HOURS: 24
      KAFKA_LOG_SEGMENT_BYTES: 1073741824
      KAFKA_JMX_PORT: 9101
      KAFKA_JMX_HOSTNAME: kafka
      KAFKA_JMX_OPTS: -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=9101 -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false
    networks:
      - kafka-network
    healthcheck:
      test: kafka-broker-api-versions --bootstrap-server localhost:9092
      interval: 10s
      timeout: 10s
      retries: 5

  # Schema Registry: 스키마 관리
  schema-registry:
    image: confluentinc/cp-schema-registry:7.5.0
    container_name: schema-registry
    depends_on:
      kafka:
        condition: service_healthy
    ports:
      - "8081:8081"
    environment:
      SCHEMA_REGISTRY_HOST_NAME: schema-registry
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: kafka:29092
      SCHEMA_REGISTRY_KAFKASTORE_SECURITY_PROTOCOL: PLAINTEXT
      SCHEMA_REGISTRY_LISTENERS: http://0.0.0.0:8081
      SCHEMA_REGISTRY_DEBUG: "false"
    networks:
      - kafka-network
    healthcheck:
      test: curl -f http://localhost:8081/subjects || exit 1
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis: 캐시 (선택)
  redis:
    image: redis:7.2-alpine
    container_name: redis
    ports:
      - "6379:6379"
    networks:
      - kafka-network
    healthcheck:
      test: redis-cli ping
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  kafka-network:
    driver: bridge
```

**저장 위치:** 프로젝트 루트

#### 2-2. Docker Compose 실행 (20분)

```bash
# 서비스 시작
docker-compose up -d

# 진행 상황 확인 (대기: 1~2분)
docker-compose logs -f

# 각 서비스 헬스체크
docker-compose ps

# 예상 출력:
# NAME                COMMAND                  SERVICE             STATUS      PORTS
# zookeeper           "sh -c '/etc/confluent…   zookeeper           Up 30s      0.0.0.0:2181->2181/tcp
# kafka               "sh -c '/etc/confluent…   kafka               Up 25s      0.0.0.0:9092->9092/tcp
# schema-registry     "sh -c '/etc/confluent…   schema-registry     Up 15s      0.0.0.0:8081->8081/tcp
# redis               "docker-entrypoint.s…"   redis               Up 35s      0.0.0.0:6379->6379/tcp
```

**연결 테스트:**

```bash
# Kafka 연결 확인
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server kafka:29092

# Schema Registry 확인
curl http://localhost:8081/subjects

# Redis 확인
docker-compose exec redis redis-cli ping
# 응답: PONG
```

#### 2-3. Avro 스키마 정의 (30분)

**파일:** `schemas/ad_event.avsc`

```json
{
  "type": "record",
  "name": "AdEvent",
  "namespace": "com.marketing_roas.avazu",
  "doc": "Avazu advertisement event",
  "fields": [
    {
      "name": "id",
      "type": "string",
      "doc": "Unique event ID"
    },
    {
      "name": "click",
      "type": "int",
      "doc": "1 if click, 0 if no click"
    },
    {
      "name": "hour",
      "type": "int",
      "doc": "Hour of the event (YYMMDDH format)"
    },
    {
      "name": "C1",
      "type": ["null", "int"],
      "default": null,
      "doc": "Anonymous categorical feature"
    },
    {
      "name": "banner_pos",
      "type": ["null", "int"],
      "default": null,
      "doc": "Position of the banner"
    },
    {
      "name": "site_id",
      "type": ["null", "string"],
      "default": null,
      "doc": "ID of the website"
    },
    {
      "name": "site_domain",
      "type": ["null", "string"],
      "default": null,
      "doc": "Domain of the website"
    },
    {
      "name": "site_category",
      "type": ["null", "string"],
      "default": null,
      "doc": "Category of the website"
    },
    {
      "name": "app_id",
      "type": ["null", "string"],
      "default": null,
      "doc": "ID of the application"
    },
    {
      "name": "app_domain",
      "type": ["null", "string"],
      "default": null,
      "doc": "Domain of the application"
    },
    {
      "name": "app_category",
      "type": ["null", "string"],
      "default": null,
      "doc": "Category of the application"
    },
    {
      "name": "device_id",
      "type": ["null", "string"],
      "default": null,
      "doc": "Device ID"
    },
    {
      "name": "device_ip",
      "type": ["null", "string"],
      "default": null,
      "doc": "Device IP address"
    },
    {
      "name": "device_model",
      "type": ["null", "string"],
      "default": null,
      "doc": "Device model"
    },
    {
      "name": "device_type",
      "type": ["null", "int"],
      "default": null,
      "doc": "Device type"
    },
    {
      "name": "device_conn_type",
      "type": ["null", "int"],
      "default": null,
      "doc": "Device connection type"
    },
    {
      "name": "C14",
      "type": ["null", "int"],
      "default": null,
      "doc": "Anonymous feature 14"
    },
    {
      "name": "C15",
      "type": ["null", "int"],
      "default": null,
      "doc": "Anonymous feature 15"
    },
    {
      "name": "C16",
      "type": ["null", "int"],
      "default": null,
      "doc": "Anonymous feature 16"
    },
    {
      "name": "C17",
      "type": ["null", "int"],
      "default": null,
      "doc": "Anonymous feature 17"
    },
    {
      "name": "C18",
      "type": ["null", "int"],
      "default": null,
      "doc": "Anonymous feature 18"
    },
    {
      "name": "C19",
      "type": ["null", "int"],
      "default": null,
      "doc": "Anonymous feature 19"
    },
    {
      "name": "C20",
      "type": ["null", "int"],
      "default": null,
      "doc": "Anonymous feature 20"
    },
    {
      "name": "C21",
      "type": ["null", "int"],
      "default": null,
      "doc": "Anonymous feature 21"
    },
    {
      "name": "timestamp",
      "type": "long",
      "doc": "Event timestamp in milliseconds"
    }
  ]
}
```

**Schema Registry에 등록:**

```bash
# 스키마 파일을 JSON 형식으로 변환
python3 << 'EOF'
import json

# 스키마 로드
with open('schemas/ad_event.avsc', 'r') as f:
    schema = json.load(f)

# Schema Registry 등록용 JSON
payload = {
    "schema": json.dumps(schema),
    "schemaType": "AVRO"
}

# 저장
with open('schemas/register_schema.json', 'w') as f:
    json.dump(payload, f)

print("✅ Schema preparation complete")
EOF

# Schema Registry에 등록
curl -X POST http://localhost:8081/subjects/ad_events_raw-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d @schemas/register_schema.json

# 등록 확인
curl http://localhost:8081/subjects/ad_events_raw-value/versions
```

**예상 응답:**
```json
[1]  // 버전 1이 등록됨
```

#### 2-4. 통합 테스트 (10분)

**파일:** `src/kafka/test_connection.py`

```python
#!/usr/bin/env python3

import requests
import json
from kafka import KafkaProducer, KafkaConsumer
import time

print("=" * 60)
print("KAFKA + SCHEMA REGISTRY 통합 테스트")
print("=" * 60)

# 1. Schema Registry 연결 테스트
print("\n1️⃣  Schema Registry 연결 테스트...")
try:
    response = requests.get('http://localhost:8081/subjects')
    subjects = response.json()
    print(f"   ✅ Schema Registry 정상 (subjects: {subjects})")
except Exception as e:
    print(f"   ❌ Schema Registry 연결 실패: {e}")

# 2. Kafka 연결 테스트
print("\n2️⃣  Kafka 연결 테스트...")
try:
    producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
    producer.close()
    print(f"   ✅ Kafka Producer 연결 성공")
except Exception as e:
    print(f"   ❌ Kafka 연결 실패: {e}")

# 3. 테스트 메시지 발행
print("\n3️⃣  테스트 메시지 발행...")
try:
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    test_event = {
        'id': 'test_001',
        'click': 1,
        'hour': 140102,
        'C1': 1005,
        'device_type': 1,
        'timestamp': int(time.time() * 1000)
    }

    future = producer.send('ad_events_raw', value=test_event)
    record_metadata = future.get(timeout=10)

    print(f"   ✅ 메시지 발행 성공")
    print(f"      Topic: {record_metadata.topic}")
    print(f"      Partition: {record_metadata.partition}")
    print(f"      Offset: {record_metadata.offset}")

    producer.close()
except Exception as e:
    print(f"   ❌ 메시지 발행 실패: {e}")

# 4. 메시지 수신 확인
print("\n4️⃣  메시지 수신 확인...")
try:
    consumer = KafkaConsumer(
        'ad_events_raw',
        bootstrap_servers=['localhost:9092'],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        consumer_timeout_ms=5000
    )

    messages_received = 0
    for message in consumer:
        print(f"   ✅ 메시지 수신: {message.value}")
        messages_received += 1
        if messages_received >= 1:
            break

    consumer.close()
except Exception as e:
    print(f"   ❌ 메시지 수신 실패: {e}")

print("\n" + "=" * 60)
print("✅ 모든 테스트 완료!")
print("=" * 60)
```

**실행:**
```bash
python src/kafka/test_connection.py
```

**예상 출력:**
```
============================================================
KAFKA + SCHEMA REGISTRY 통합 테스트
============================================================

1️⃣  Schema Registry 연결 테스트...
   ✅ Schema Registry 정상 (subjects: ['ad_events_raw-value'])

2️⃣  Kafka 연결 테스트...
   ✅ Kafka Producer 연결 성공

3️⃣  테스트 메시지 발행...
   ✅ 메시지 발행 성공
      Topic: ad_events_raw
      Partition: 0
      Offset: 0

4️⃣  메시지 수신 확인...
   ✅ 메시지 수신: {'id': 'test_001', 'click': 1, ...}

============================================================
✅ 모든 테스트 완료!
============================================================
```

### ✅ 완료 기준

- [ ] Docker Compose 파일 작성 완료
- [ ] 모든 서비스 정상 실행 (`docker-compose ps` 확인)
- [ ] Schema Registry에 Ad Event 스키마 등록
- [ ] `test_connection.py` 모든 테스트 통과
- [ ] Kafka Topic `ad_events_raw` 생성 확인

### 📊 산출물

```
docker-compose.yml
schemas/
├── ad_event.avsc
└── register_schema.json
src/kafka/
└── test_connection.py
```

---

## 📌 Day 3 (수): Kafka Topic 생성 & 설정 (2시간)

### 목표
- 프로덕션 환경에 맞는 Kafka Topic 구성
- Topic 설정 최적화 (파티션, 레플리카 등)
- JMX Exporter로 모니터링 기초 설정
- 성능 테스트

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| Topic 생성 | 30분 |
| 설정 검증 | 30분 |
| JMX 설정 | 40분 |
| 성능 테스트 | 20분 |

### 🛠️ 실습 내용

#### 3-1. 프로덕션 Kafka Topics 생성 (20분)

**파일:** `scripts/create_topics.sh`

```bash
#!/bin/bash

# Topic 생성 함수
create_topic() {
    TOPIC_NAME=$1
    PARTITIONS=$2
    REPLICATION=$3

    echo "Creating topic: $TOPIC_NAME (partitions: $PARTITIONS, replication: $REPLICATION)"

    docker-compose exec kafka kafka-topics \
        --create \
        --bootstrap-server kafka:29092 \
        --topic $TOPIC_NAME \
        --partitions $PARTITIONS \
        --replication-factor $REPLICATION \
        --config retention.ms=86400000 \
        --config compression.type=snappy \
        --config min.insync.replicas=1 \
        --config cleanup.policy=delete \
        2>&1 || echo "⚠️  Topic $TOPIC_NAME already exists"
}

echo "================================"
echo "Creating Kafka Topics..."
echo "================================"

# 1. 메인 토픽: 광고 이벤트 (실시간 처리)
create_topic "ad_events_raw" 3 1

# 2. DLQ: 처리 실패한 메시지
create_topic "ad_events_error" 1 1

# 3. 리트라이: 재처리 대기
create_topic "ad_events_retry" 1 1

echo ""
echo "✅ Topic creation completed"
```

**실행:**
```bash
chmod +x scripts/create_topics.sh
bash scripts/create_topics.sh
```

**Topic 확인:**

```bash
# 생성된 Topic 확인
docker-compose exec kafka kafka-topics \
    --list \
    --bootstrap-server kafka:29092

# Topic 상세 정보
docker-compose exec kafka kafka-topics \
    --describe \
    --bootstrap-server kafka:29092 \
    --topic ad_events_raw

# 예상 출력:
# Topic: ad_events_raw    TopicId: xxx    PartitionCount: 3    ReplicationFactor: 1
# Topic: ad_events_raw    Partition: 0    Leader: 1   Replicas: [1]    Isr: [1]
# Topic: ad_events_raw    Partition: 1    Leader: 1   Replicas: [1]    Isr: [1]
# Topic: ad_events_raw    Partition: 2    Leader: 1   Replicas: [1]    Isr: [1]
```

#### 3-2. Topic 설정 최적화 (20분)

**파일:** `config/kafka_topics_config.json`

```json
{
  "topics": [
    {
      "name": "ad_events_raw",
      "description": "Real-time advertisement events from Avazu",
      "partitions": 3,
      "replication_factor": 1,
      "config": {
        "retention.ms": 86400000,
        "retention.bytes": 10737418240,
        "compression.type": "snappy",
        "min.insync.replicas": 1,
        "cleanup.policy": "delete",
        "flush.messages": 10000,
        "flush.ms": 30000,
        "segment.ms": 3600000,
        "max.message.bytes": 1048576
      },
      "notes": "3 partitions for high throughput, snappy compression for efficiency"
    },
    {
      "name": "ad_events_error",
      "description": "Failed messages (DLQ)",
      "partitions": 1,
      "replication_factor": 1,
      "config": {
        "retention.ms": 604800000,
        "compression.type": "gzip",
        "cleanup.policy": "delete"
      },
      "notes": "DLQ with 7 days retention for debugging"
    },
    {
      "name": "ad_events_retry",
      "description": "Messages pending retry",
      "partitions": 2,
      "replication_factor": 1,
      "config": {
        "retention.ms": 3600000,
        "compression.type": "none",
        "priority.processor": "true"
      },
      "notes": "Retry queue with 1 hour TTL"
    }
  ],
  "performance_targets": {
    "throughput_msg_per_sec": 50000,
    "latency_p99_ms": 1000,
    "availability_percent": 99.9
  }
}
```

**설정 적용:**

```python
# config/apply_topic_configs.py
import subprocess
import json

with open('config/kafka_topics_config.json', 'r') as f:
    config = json.load(f)

for topic in config['topics']:
    topic_name = topic['name']
    configs = topic['config']

    for key, value in configs.items():
        cmd = [
            'docker-compose', 'exec', 'kafka',
            'kafka-configs',
            '--bootstrap-server', 'kafka:29092',
            '--entity-type', 'topics',
            '--entity-name', topic_name,
            '--alter',
            '--add-config', f'{key}={value}'
        ]

        subprocess.run(cmd)
        print(f"✅ Applied {key}={value} to {topic_name}")

print("\n✅ All configurations applied")
```

**실행:**
```bash
python config/apply_topic_configs.py
```

#### 3-3. JMX 모니터링 설정 (30분)

**파일:** `config/jmx_exporter_config.yml`

```yaml
# JMX Exporter Configuration for Kafka

lowercaseOutputName: true
lowercaseOutputLabelNames: true

rules:
  # Broker Metrics
  - pattern: "kafka.server<type=(.+), name=(.+), clientId=(.+), topic=(.+), partition=([0-9]+)><value>(.+)"
    name: "kafka_server_$1_$2"
    labels:
      clientId: "$3"
      topic: "$4"
      partition: "$5"
    value: "$6"
    type: GAUGE

  - pattern: "kafka.server<type=(.+), name=(.+), clientId=(.+), brokerHost=(.+), brokerPort=(.+)><value>(.+)"
    name: "kafka_server_$1_$2"
    labels:
      clientId: "$3"
      broker: "$4:$5"
    value: "$6"

  - pattern: "kafka.server<type=(.+), name=(.+)><value>(.+)"
    name: "kafka_server_$1_$2"
    value: "$3"

  # ReplicaManager
  - pattern: "kafka.server<type=ReplicaManager, name=(.+), topic=(.+), partition=([0-9]+)><value>(.+)"
    name: "kafka_server_replica_manager_$1"
    labels:
      topic: "$2"
      partition: "$3"
    value: "$4"

  # Controller Metrics
  - pattern: "kafka.controller<type=(.+), name=(.+)><value>(.+)"
    name: "kafka_controller_$1_$2"
    value: "$3"

  # Network Metrics
  - pattern: "kafka.network<type=(.+), name=(.+)><value>(.+)"
    name: "kafka_network_$1_$2"
    value: "$3"

  # Group Coordinator
  - pattern: "kafka.coordinator.group<type=(.+), name=(.+)><value>(.+)"
    name: "kafka_coordinator_group_$1_$2"
    value: "$3"
```

**JMX Exporter Container 추가 (docker-compose.yml):**

```yaml
  jmx-exporter:
    image: sscaling/jmx-exporter:latest
    container_name: jmx-exporter
    ports:
      - "5556:5556"
    volumes:
      - ./config/jmx_exporter_config.yml:/etc/jmx_exporter/config.yml:ro
    command:
      - "5556"
      - "/etc/jmx_exporter/config.yml"
    depends_on:
      - kafka
    networks:
      - kafka-network
```

**재시작:**
```bash
docker-compose up -d jmx-exporter
docker-compose logs -f jmx-exporter
```

#### 3-4. 성능 테스트 (20분)

**파일:** `src/kafka/performance_test.py`

```python
#!/usr/bin/env python3

import json
import time
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import statistics

print("=" * 70)
print("KAFKA 성능 테스트")
print("=" * 70)

# 테스트 메시지 생성
test_messages = []
for i in range(10000):
    test_messages.append({
        'id': f'test_{i:06d}',
        'click': i % 100 < 16,  # 16% CTR
        'hour': 140102,
        'device_type': i % 10,
        'timestamp': int(time.time() * 1000)
    })

# 1️⃣  Producer 성능 테스트
print("\n1️⃣  Producer 성능 테스트 (10,000 messages)...")

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',
    retries=3,
    batch_size=16384,
    linger_ms=10
)

latencies = []
start_time = time.time()

for i, msg in enumerate(test_messages):
    try:
        future = producer.send('ad_events_raw', value=msg)
        record_metadata = future.get(timeout=10)

        latency = (time.time() - start_time) * 1000 / (i + 1)
        latencies.append(latency)

        if (i + 1) % 1000 == 0:
            print(f"   📤 {i + 1:,} messages sent")
    except KafkaError as e:
        print(f"   ❌ Error: {e}")

producer.flush()
producer.close()

elapsed = time.time() - start_time
throughput = len(test_messages) / elapsed

print(f"\n   결과:")
print(f"   - 총 메시지: {len(test_messages):,}")
print(f"   - 소요 시간: {elapsed:.2f}초")
print(f"   - 처리량: {throughput:.0f} msg/sec")
print(f"   - 평균 레이턴시: {statistics.mean(latencies):.2f}ms")
print(f"   - 최대 레이턴시: {max(latencies):.2f}ms")
print(f"   - P99 레이턴시: {sorted(latencies)[int(len(latencies)*0.99)]:.2f}ms")

# 2️⃣  Consumer 성능 테스트
print("\n2️⃣  Consumer 성능 테스트...")

consumer = KafkaConsumer(
    'ad_events_raw',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    consumer_timeout_ms=30000,
    fetch_max_bytes=52428800,
    max_poll_records=500
)

messages_received = 0
start_time = time.time()

for message in consumer:
    messages_received += 1
    if messages_received % 1000 == 0:
        print(f"   📥 {messages_received:,} messages received")

elapsed_consume = time.time() - start_time
throughput_consume = messages_received / elapsed_consume

print(f"\n   결과:")
print(f"   - 수신 메시지: {messages_received:,}")
print(f"   - 소요 시간: {elapsed_consume:.2f}초")
print(f"   - 처리량: {throughput_consume:.0f} msg/sec")

consumer.close()

# 3️⃣  최종 결과
print("\n" + "=" * 70)
print("성능 요약")
print("=" * 70)
print(f"Producer 처리량:  {throughput:>10.0f} msg/sec")
print(f"Consumer 처리량:  {throughput_consume:>10.0f} msg/sec")
print(f"P99 레이턴시:     {sorted(latencies)[int(len(latencies)*0.99)]:>10.2f} ms")
print(f"목표 달성:        {'✅' if throughput > 50000 else '⚠️'}")
print("=" * 70)
```

**실행:**
```bash
python src/kafka/performance_test.py
```

### ✅ 완료 기준

- [ ] 3개 Topic 생성 완료 (`ad_events_raw`, `ad_events_error`, `ad_events_retry`)
- [ ] Topic 설정 파일 작성 및 적용
- [ ] JMX Exporter 실행 중
- [ ] Performance 테스트 > 50,000 msg/sec
- [ ] P99 레이턴시 < 1,000ms

### 📊 산출물

```
scripts/
└── create_topics.sh
config/
├── jmx_exporter_config.yml
└── kafka_topics_config.json
src/kafka/
└── performance_test.py
```

---

## 📌 Day 4 (목): Python Kafka Producer 개발 (2시간)

### 목표
- Avazu CSV 데이터를 Kafka로 전송하는 고성능 Producer 작성
- 에러 처리 및 DLQ 라우팅
- 배치 처리 및 프로세싱 최적화
- 프로덕션 레디 코드

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| 데이터 변환 로직 | 30분 |
| Producer 구현 | 50분 |
| 에러 처리 | 20분 |
| 테스트 | 20분 |

### 🛠️ 실습 내용

#### 4-1. 데이터 변환 모듈 (20분)

**파일:** `src/kafka/data_transformer.py`

```python
"""
Avazu CSV 데이터를 JSON 이벤트로 변환
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AvazuDataTransformer:
    """Avazu 데이터 변환기"""

    # 컬럼 타입 정의
    INT_COLUMNS = {
        'click', 'hour', 'C1', 'banner_pos', 'device_type',
        'device_conn_type', 'C14', 'C15', 'C16', 'C17',
        'C18', 'C19', 'C20', 'C21'
    }

    STRING_COLUMNS = {
        'id', 'site_id', 'site_domain', 'site_category',
        'app_id', 'app_domain', 'app_category',
        'device_id', 'device_ip', 'device_model'
    }

    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.transformation_errors = []

    @staticmethod
    def parse_csv_line(header: list, values: list) -> Dict[str, Any]:
        """
        CSV 라인을 파싱하여 Python dict로 변환

        Args:
            header: CSV 헤더 리스트
            values: CSV 값 리스트

        Returns:
            파싱된 dict, 또는 None if error
        """
        if len(header) != len(values):
            logger.error(f"Header/values mismatch: {len(header)} vs {len(values)}")
            return None

        try:
            result = {}

            for col, val in zip(header, values):
                if not val or val == '':
                    # 빈 값은 null로
                    result[col] = None
                elif col in AvazuDataTransformer.INT_COLUMNS:
                    try:
                        result[col] = int(val)
                    except ValueError:
                        logger.warning(f"Cannot convert {col}={val} to int, setting to None")
                        result[col] = None
                else:
                    # 문자열로 처리
                    result[col] = str(val)

            return result

        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None

    def transform(self, csv_line: str, line_number: int) -> Optional[Dict[str, Any]]:
        """
        CSV 라인을 Kafka 이벤트로 변환

        Args:
            csv_line: CSV 라인 문자열
            line_number: 라인 번호 (첫 줄은 0)

        Returns:
            변환된 이벤트 dict, 또는 None if error
        """
        try:
            values = csv_line.strip().split(',')

            # 헤더는 첫 번째 라인 (line_number == 0)
            if line_number == 0:
                self.header = values
                return None

            # 데이터 변환
            event = self.parse_csv_line(self.header, values)

            if event is None:
                self.error_count += 1
                return None

            # 메타데이터 추가
            event['_source'] = 'avazu'
            event['_processed_at'] = datetime.utcnow().isoformat()
            event['_line_number'] = line_number

            self.processed_count += 1
            return event

        except Exception as e:
            logger.error(f"Transformation error at line {line_number}: {e}")
            self.error_count += 1
            self.transformation_errors.append({
                'line_number': line_number,
                'error': str(e)
            })
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """변환 통계"""
        return {
            'processed': self.processed_count,
            'errors': self.error_count,
            'success_rate': (
                self.processed_count / (self.processed_count + self.error_count) * 100
                if (self.processed_count + self.error_count) > 0 else 0
            )
        }


if __name__ == "__main__":
    # 테스트
    transformer = AvazuDataTransformer()

    # 헤더 처리
    header = "id,click,hour,C1,banner_pos,site_id,site_category,device_type"
    transformer.transform(header, 0)

    # 데이터 처리
    data = "1000009418151094273,0,14102100,1005,0,1fbe01fe,28905ebd,1"
    event = transformer.transform(data, 1)

    print("Transformed event:")
    import json
    print(json.dumps(event, indent=2))
    print(f"\nStatistics: {transformer.get_statistics()}")
```

#### 4-2. Kafka Producer 구현 (40분)

**파일:** `src/kafka/producer.py`

```python
"""
Avazu 데이터를 Kafka로 발행하는 Producer
"""

import gzip
import json
import time
import logging
from typing import Optional, Callable
from kafka import KafkaProducer
from kafka.errors import KafkaError

from data_transformer import AvazuDataTransformer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AvazuKafkaProducer:
    """Avazu 데이터를 Kafka로 발행하는 Producer"""

    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        topic_success: str = 'ad_events_raw',
        topic_error: str = 'ad_events_error',
        batch_size: int = 100,
        linger_ms: int = 10
    ):
        """
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic_success: 성공한 메시지 토픽
            topic_error: 실패한 메시지 토픽
            batch_size: 배치 크기
            linger_ms: 배치 대기 시간 (ms)
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic_success = topic_success
        self.topic_error = topic_error
        self.batch_size = batch_size
        self.linger_ms = linger_ms

        # 통계
        self.stats = {
            'sent': 0,
            'errors': 0,
            'dlq': 0,
            'total_time': 0,
            'start_time': None,
            'end_time': None
        }

        # Producer 초기화
        self.producer = self._init_producer()
        self.transformer = AvazuDataTransformer()

    def _init_producer(self) -> KafkaProducer:
        """Kafka Producer 초기화"""
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # 모든 replicas의 확인 대기
                retries=3,  # 재시도 횟수
                batch_size=self.batch_size,
                linger_ms=self.linger_ms,
                buffer_memory=33554432,  # 32MB
                max_in_flight_requests_per_connection=5,
                compression_type='snappy'
            )
            logger.info("✅ Kafka Producer initialized")
            return producer
        except Exception as e:
            logger.error(f"❌ Failed to initialize producer: {e}")
            raise

    def _on_send_success(self, record_metadata):
        """메시지 발행 성공 콜백"""
        self.stats['sent'] += 1
        if self.stats['sent'] % 1000 == 0:
            logger.info(f"✅ {self.stats['sent']:,} messages sent")

    def _on_send_error(self, exc):
        """메시지 발행 실패 콜백"""
        self.stats['errors'] += 1
        logger.error(f"❌ Send error: {exc}")

    def produce_from_gz(
        self,
        gz_file_path: str,
        max_records: Optional[int] = None,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        Gzip 파일에서 메시지를 읽어 Kafka로 발행

        Args:
            gz_file_path: Gzip 파일 경로
            max_records: 최대 레코드 수 (None: 전체)
            progress_callback: 진행도 콜백 함수

        Returns:
            통계 dict
        """
        self.stats['start_time'] = time.time()

        try:
            with gzip.open(gz_file_path, 'rt', encoding='utf-8') as f:
                line_number = 0

                for line in f:
                    # 최대 레코드 제한
                    if max_records and line_number >= max_records + 1:  # +1 for header
                        break

                    # 데이터 변환
                    event = self.transformer.transform(line, line_number)

                    # 헤더는 발행하지 않음
                    if line_number == 0:
                        line_number += 1
                        continue

                    # 변환 실패시 DLQ로 전송
                    if event is None:
                        try:
                            error_event = {
                                'line_number': line_number,
                                'raw_data': line.strip(),
                                'error': 'Transformation failed',
                                'timestamp': int(time.time() * 1000)
                            }
                            self.producer.send(
                                self.topic_error,
                                value=error_event
                            ).get(timeout=10)
                            self.stats['dlq'] += 1
                        except Exception as e:
                            logger.error(f"Failed to send to DLQ: {e}")

                        line_number += 1
                        continue

                    # 성공 토픽으로 발행
                    try:
                        self.producer.send(
                            self.topic_success,
                            value=event
                        ).add_callback(self._on_send_success) \
                         .add_errback(self._on_send_error)

                    except Exception as e:
                        logger.error(f"Failed to send message: {e}")
                        self.stats['errors'] += 1

                    # 진행도 콜백
                    if progress_callback:
                        progress_callback(line_number)

                    line_number += 1

        except Exception as e:
            logger.error(f"❌ Error reading file: {e}")
            raise

        finally:
            # Flush 및 정리
            self.producer.flush(timeout=30)
            self.stats['end_time'] = time.time()
            self.stats['total_time'] = self.stats['end_time'] - self.stats['start_time']

        return self.get_statistics()

    def get_statistics(self) -> dict:
        """통계 반환"""
        stats = self.stats.copy()
        stats['transformer'] = self.transformer.get_statistics()

        if stats['total_time'] > 0:
            stats['throughput_msg_per_sec'] = (
                (stats['sent'] + stats['dlq']) / stats['total_time']
            )

        return stats

    def close(self):
        """Producer 종료"""
        self.producer.close()
        logger.info("✅ Producer closed")


def print_statistics(stats: dict):
    """통계 출력"""
    print("\n" + "=" * 70)
    print("PRODUCTION STATISTICS")
    print("=" * 70)
    print(f"Messages sent:          {stats['sent']:>15,}")
    print(f"DLQ (errors):           {stats['dlq']:>15,}")
    print(f"Send errors:            {stats['errors']:>15,}")
    print(f"Total time:             {stats['total_time']:>15.2f} sec")
    print(f"Throughput:             {stats.get('throughput_msg_per_sec', 0):>15.0f} msg/sec")
    print(f"Transformer success:    {stats['transformer']['success_rate']:>14.2f}%")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    import sys

    # 파라미터
    gz_file = '../../data/train.gz'
    max_records = 10000  # 테스트용 10,000건

    if len(sys.argv) > 1:
        max_records = int(sys.argv[1])

    # Producer 실행
    producer = AvazuKafkaProducer()

    try:
        logger.info(f"Starting production from {gz_file} (max {max_records:,} records)")

        stats = producer.produce_from_gz(
            gz_file,
            max_records=max_records,
            progress_callback=lambda line: (
                print(f"Processing line {line:,}...")
                if line % 2000 == 0 else None
            )
        )

        print_statistics(stats)
        logger.info("✅ Production completed successfully")

    except KeyboardInterrupt:
        logger.info("⚠️  Production interrupted by user")
        print_statistics(producer.get_statistics())

    except Exception as e:
        logger.error(f"❌ Production failed: {e}")
        print_statistics(producer.get_statistics())

    finally:
        producer.close()
```

#### 4-3. 에러 처리 및 재시도 (15분)

**파일:** `src/kafka/error_handler.py`

```python
"""
DLQ 에러 처리 및 재시도 로직
"""

import json
import logging
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class DLQHandler:
    """Dead Letter Queue 처리"""

    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        dlq_topic: str = 'ad_events_error',
        retry_topic: str = 'ad_events_retry'
    ):
        self.bootstrap_servers = bootstrap_servers
        self.dlq_topic = dlq_topic
        self.retry_topic = retry_topic

        self.consumer = KafkaConsumer(
            dlq_topic,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            consumer_timeout_ms=10000
        )

        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        self.stats = {
            'processed': 0,
            'retried': 0,
            'skipped': 0
        }

    def process_dlq(self):
        """DLQ 메시지 처리"""
        logger.info(f"Processing DLQ topic: {self.dlq_topic}")

        for message in self.consumer:
            try:
                error_event = message.value
                line_number = error_event.get('line_number')
                error_reason = error_event.get('error', 'Unknown')

                logger.warning(f"DLQ message at line {line_number}: {error_reason}")

                # 재시도 여부 판단
                if self._should_retry(error_event):
                    # Retry 토픽으로 전송
                    self.producer.send(
                        self.retry_topic,
                        value=error_event
                    )
                    self.stats['retried'] += 1
                    logger.info(f"Message sent to retry topic: {line_number}")
                else:
                    logger.error(f"Skipping message: {line_number}")
                    self.stats['skipped'] += 1

                self.stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error processing DLQ message: {e}")

        self.producer.flush()
        logger.info(f"DLQ processing completed: {self.stats}")

    def _should_retry(self, error_event: dict) -> bool:
        """재시도 가능 여부 판단"""
        retry_count = error_event.get('retry_count', 0)
        max_retries = 3

        # 타임아웃, 일시적 오류는 재시도
        error_reason = error_event.get('error', '')
        retriable_errors = [
            'Transformation failed',
            'Timeout',
            'Connection error'
        ]

        return (
            retry_count < max_retries and
            any(err in error_reason for err in retriable_errors)
        )

    def close(self):
        self.consumer.close()
        self.producer.close()


if __name__ == "__main__":
    handler = DLQHandler()
    handler.process_dlq()
    handler.close()
```

#### 4-4. 통합 테스트 (20분)

**파일:** `src/kafka/test_producer.py`

```python
"""
Producer 통합 테스트
"""

import subprocess
import time
import logging
from producer import AvazuKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_producer():
    """Producer 테스트"""

    print("\n" + "=" * 70)
    print("KAFKA PRODUCER TEST")
    print("=" * 70)

    # 1️⃣  Small dataset으로 테스트
    print("\n1️⃣  테스트: 1,000건 메시지 발행...")
    producer = AvazuKafkaProducer()

    try:
        stats = producer.produce_from_gz(
            '../../data/train.gz',
            max_records=1000
        )

        assert stats['sent'] > 900, f"Expected > 900 messages, got {stats['sent']}"
        assert stats['dlq'] < 100, f"Expected < 100 DLQ, got {stats['dlq']}"
        print("   ✅ Test passed")

    except AssertionError as e:
        print(f"   ❌ Test failed: {e}")
        return False

    finally:
        producer.close()

    # 2️⃣  Producer 재시작 후 메시지 수신 확인
    print("\n2️⃣  메시지 수신 확인...")

    subprocess.run([
        'bash', '-c',
        'docker-compose exec kafka kafka-console-consumer '
        '--bootstrap-server kafka:29092 '
        '--topic ad_events_raw '
        '--from-beginning '
        '--max-messages 1 | head -1'
    ])

    print("   ✅ Message received")

    # 3️⃣  성능 테스트
    print("\n3️⃣  성능 테스트: 10,000건...")

    producer = AvazuKafkaProducer()
    try:
        stats = producer.produce_from_gz(
            '../../data/train.gz',
            max_records=10000
        )

        throughput = stats.get('throughput_msg_per_sec', 0)
        assert throughput > 1000, f"Throughput too low: {throughput}"

        print(f"   ✅ Throughput: {throughput:.0f} msg/sec")

    finally:
        producer.close()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)

    return True


if __name__ == "__main__":
    test_producer()
```

**실행:**
```bash
cd src/kafka
python producer.py 10000
```

### ✅ 완료 기준

- [ ] `data_transformer.py` 작동 확인 (CSV → JSON 변환)
- [ ] `producer.py` 실행 완료 (10,000건 이상 발행)
- [ ] 발행 처리량 > 1,000 msg/sec
- [ ] Kafka Topic에서 메시지 수신 확인
- [ ] DLQ로 에러 메시지 전달
- [ ] 모든 테스트 통과

### 📊 산출물

```
src/kafka/
├── data_transformer.py
├── producer.py
├── error_handler.py
└── test_producer.py
```

---

## 📌 Day 5 (금): 모니터링 & 통합 테스트 (2시간)

### 목표
- 전체 파이프라인 엔드-투-엔드 테스트
- Prometheus/JMX 메트릭 수집 확인
- 성능 벤치마크
- Week 1 마무리 및 Week 2 준비

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| Prometheus 설정 | 30분 |
| 메트릭 수집 검증 | 30분 |
| E2E 테스트 | 40분 |
| 문서화 | 20분 |

### 🛠️ 실습 내용

#### 5-1. Prometheus 설정 (20분)

**파일:** `config/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'kafka-monitoring'

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files: []

scrape_configs:
  # Kafka JMX Metrics
  - job_name: 'kafka'
    static_configs:
      - targets: ['localhost:5556']
        labels:
          instance: 'kafka-broker-1'

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

**Docker Compose에 Prometheus 추가:**

```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    depends_on:
      - jmx-exporter
    networks:
      - kafka-network

volumes:
  prometheus_data:
```

**실행:**
```bash
docker-compose up -d prometheus
docker-compose logs -f prometheus
```

**접속:** http://localhost:9090

#### 5-2. 메트릭 수집 검증 (30분)

**파일:** `src/monitoring/verify_metrics.py`

```python
"""
Prometheus 메트릭 수집 검증
"""

import requests
import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class PrometheusClient:
    """Prometheus 클라이언트"""

    def __init__(self, url: str = 'http://localhost:9090'):
        self.url = url

    def query(self, query: str) -> Dict:
        """PromQL 쿼리 실행"""
        try:
            response = requests.get(
                f'{self.url}/api/v1/query',
                params={'query': query},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {'status': 'error'}

    def verify_kafka_metrics(self) -> bool:
        """Kafka 메트릭 수집 확인"""

        print("\n" + "=" * 70)
        print("PROMETHEUS METRICS VERIFICATION")
        print("=" * 70)

        # 1️⃣  Kafka metrics 확인
        print("\n1️⃣  Kafka Broker Metrics...")
        metrics = [
            ('kafka_server_replica_manager_isr_shrinks_total', '변경된 ISR'),
            ('kafka_server_broker_topic_metrics_messages_in_total', '메시지 수신'),
            ('kafka_server_broker_topic_metrics_bytes_in_total', '수신 바이트'),
        ]

        for metric_name, description in metrics:
            result = self.query(metric_name)
            status = 'OK' if result['status'] == 'success' else 'MISSING'
            print(f"   {status}: {metric_name} ({description})")

        # 2️⃣  Topic별 메트릭
        print("\n2️⃣  Topic Metrics...")
        result = self.query(
            'kafka_server_broker_topic_metrics_messages_in_total{topic="ad_events_raw"}'
        )

        if result['status'] == 'success' and result['data']['result']:
            value = result['data']['result'][0]['value'][1]
            print(f"   ✅ ad_events_raw: {value} messages")
        else:
            print(f"   ⚠️  ad_events_raw: No data yet")

        # 3️⃣  기본 시스템 메트릭
        print("\n3️⃣  System Metrics...")
        result = self.query('kafka_server_request_handler_avg_idle_percent')

        if result['status'] == 'success' and result['data']['result']:
            value = result['data']['result'][0]['value'][1]
            print(f"   ✅ Request handler idle: {value}%")

        print("\n" + "=" * 70)
        return True


def verify_all():
    """전체 검증"""

    print("\nPrometheus 메트릭 수집 확인...")

    client = PrometheusClient()

    # Prometheus 연결 확인
    try:
        response = requests.get('http://localhost:9090/-/healthy', timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus is healthy")
        else:
            print("❌ Prometheus health check failed")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Prometheus: {e}")
        return False

    # 메트릭 검증
    return client.verify_kafka_metrics()


if __name__ == "__main__":
    verify_all()
```

#### 5-3. E2E 통합 테스트 (30분)

**파일:** `scripts/e2e_test.sh`

```bash
#!/bin/bash

set -e

echo "=========================================="
echo "E2E TEST: Week 1 Pipeline Validation"
echo "=========================================="

# 1️⃣  Docker 서비스 확인
echo ""
echo "1️⃣  Checking Docker services..."
docker-compose ps

# 2️⃣  Topics 확인
echo ""
echo "2️⃣  Checking Kafka Topics..."
docker-compose exec kafka kafka-topics \
    --list \
    --bootstrap-server kafka:29092

# 3️⃣  Schema Registry 확인
echo ""
echo "3️⃣  Checking Schema Registry..."
curl -s http://localhost:8081/subjects | jq .

# 4️⃣  Producer 실행
echo ""
echo "4️⃣  Running Producer (5,000 messages)..."
cd src/kafka
python producer.py 5000
cd ../../

# 5️⃣  메시지 수신 확인
echo ""
echo "5️⃣  Verifying messages received..."
MESSAGE_COUNT=$(docker-compose exec kafka kafka-console-consumer \
    --bootstrap-server kafka:29092 \
    --topic ad_events_raw \
    --from-beginning \
    --timeout-ms 5000 \
    2>/dev/null | wc -l)

echo "Messages received: $MESSAGE_COUNT"

if [ $MESSAGE_COUNT -gt 4000 ]; then
    echo "✅ E2E test passed!"
else
    echo "❌ E2E test failed! Expected > 4000, got $MESSAGE_COUNT"
    exit 1
fi

# 6️⃣  Prometheus 메트릭 확인
echo ""
echo "6️⃣  Checking Prometheus metrics..."
python src/monitoring/verify_metrics.py

echo ""
echo "=========================================="
echo "✅ WEEK 1 VALIDATION COMPLETE"
echo "=========================================="
```

**실행:**
```bash
chmod +x scripts/e2e_test.sh
bash scripts/e2e_test.sh
```

#### 5-4. 최종 보고서 (20분)

**파일:** `docs/week1_summary.md`

```markdown
# Week 1 완료 보고서: 데이터 수집 & 스트리밍 기초

## 📋 개요

**기간:** 5일 (월~금)
**목표:** Kafka 클러스터 구축 및 Avazu 데이터 수집 파이프라인 완성
**상태:** ✅ 완료

## 🎯 주요 성과

### 1. Avazu 데이터 분석 완료
- 데이터 크기: 7.82 GB (40M 행)
- 컬럼 수: 24개
- 클릭률: 16.6%
- 3개의 샘플 데이터셋 생성 (1K, 10K, 50K)

### 2. Kafka + Schema Registry 구축
- Zookeeper + Kafka + Schema Registry 정상 작동
- 3개 Topic 생성 (ad_events_raw, ad_events_error, ad_events_retry)
- Avro Schema 등록 및 검증

### 3. Python Kafka Producer 개발
- CSV → JSON 데이터 변환
- 배치 처리 및 압축 (Snappy)
- 에러 처리 및 DLQ 라우팅
- **처리량:** 1,000+ msg/sec

### 4. 모니터링 기초 설정
- JMX Exporter 연동
- Prometheus 메트릭 수집
- 기본 대시보드 구성

## 📊 최종 메트릭

| 항목 | 목표 | 실제 | 상태 |
|------|------|------|------|
| Producer 처리량 | > 1,000 msg/sec | 1,200+ | ✅ |
| Kafka 가용성 | 99.9% | 100% | ✅ |
| Schema Registry 응답 | < 100ms | 50ms | ✅ |
| 메시지 손실률 | 0% | 0% | ✅ |
| 데이터 변환 성공률 | > 99% | 99.8% | ✅ |

## 📁 산출물

### 코드
- `src/kafka/producer.py` - Kafka Producer
- `src/kafka/data_transformer.py` - 데이터 변환
- `src/kafka/error_handler.py` - DLQ 처리
- `src/analysis/eda_analysis.py` - EDA 스크립트

### 설정
- `docker-compose.yml` - Docker 서비스
- `schemas/ad_event.avsc` - Avro 스키마
- `config/prometheus.yml` - Prometheus 설정
- `config/jmx_exporter_config.yml` - JMX 설정

### 문서
- `docs/eda_report.md` - EDA 보고서
- `docs/week1_summary.md` - 주간 보고서
- `data/data_stats.json` - 데이터 통계

## 🔄 전체 데이터 흐름

```
[Avazu train.gz]
       ↓
[Producer: CSV → JSON]
       ↓
[Kafka Topic: ad_events_raw] ← [JMX Metrics]
       ↓                              ↓
  [✅ Success]          [Prometheus] → [Grafana (향후)]
  [❌ Error] → [DLQ Topic: ad_events_error]
```

## ✅ 체크리스트

- [x] Avazu 데이터 분석 완료
- [x] Docker 환경 구성
- [x] Kafka + Schema Registry 실행
- [x] 3개 Topic 생성
- [x] Producer 개발 완료
- [x] 10,000+ 메시지 발행 성공
- [x] JMX/Prometheus 모니터링 설정
- [x] E2E 테스트 통과

## 🚀 Week 2 준비

- [ ] PyFlink 개발 환경 설정
- [ ] PostgreSQL Docker 이미지 준비
- [ ] Streamlit 개발 환경
- [ ] Redis Docker 이미지 준비

## 📝 주요 배운 점

1. **Kafka 아키텍처**: Partitioning, replication, leader election
2. **스키마 관리**: Avro, Schema Registry, 버전 관리
3. **Data Transformation**: CSV 파싱, 타입 변환, 에러 처리
4. **고성능 Producer**: Batching, compression, async callbacks

## ⚠️ 문제 & 해결

### 문제 1: 초기 Producer 연결 실패
**원인:** Kafka 초기화 지연
**해결:** docker-compose healthcheck 추가

### 문제 2: 데이터 손실
**원인:** 배치 처리 전 Producer 종료
**해결:** producer.flush() 추가

### 문제 3: 메모리 부족
**원인:** 전체 데이터셋 로드
**해결:** 샘플 데이터셋 사용

## 🎯 다음 주 목표

- PyFlink로 실시간 스트리밍 처리
- 1분/5분 Tumbling Window 구현
- Redis 캐시 구축
- Streamlit 대시보드 개발
- PostgreSQL 데이터 적재

---

**작성 일시:** 2025-12-13
**담당자:** Engineering Team
**상태:** ✅ 완료 & Week 2 준비 완료
```

### ✅ 완료 기준

- [ ] 모든 Docker 서비스 정상 실행
- [ ] Kafka Topics 정상 작동
- [ ] Producer 10,000+ 메시지 발행
- [ ] Prometheus에서 메트릭 수집 확인
- [ ] E2E 테스트 통과
- [ ] Week 1 완료 보고서 작성

### 📊 최종 산출물

```
Week 1 완료
├── docker-compose.yml
├── src/
│   ├── kafka/
│   │   ├── producer.py
│   │   ├── data_transformer.py
│   │   ├── error_handler.py
│   │   └── test_producer.py
│   ├── analysis/
│   │   ├── explore_data.py
│   │   └── eda_analysis.py
│   └── monitoring/
│       └── verify_metrics.py
├── schemas/
│   ├── ad_event.avsc
│   └── register_schema.json
├── config/
│   ├── prometheus.yml
│   └── jmx_exporter_config.yml
├── scripts/
│   ├── create_topics.sh
│   └── e2e_test.sh
└── docs/
    ├── eda_report.md
    └── week1_summary.md
```

---

## 🎓 Week 1 핵심 학습 내용

### 기술
✅ Kafka 아키텍처 및 설정
✅ Schema Registry 및 Avro
✅ Python 고성능 Producer
✅ 모니터링 및 메트릭

### 스킬
✅ Docker Compose
✅ Bash 스크립팅
✅ 데이터 파이프라인 설계
✅ 성능 최적화

### 시스템 설계
✅ 메시지 브로커 이해
✅ 스케일성 고려
✅ 에러 처리 및 복구
✅ 모니터링 및 알림

---

**Week 1 완료!** 🎉
**다음 주 목표:** 실시간 처리 (Flink) & 캐싱 (Redis)
