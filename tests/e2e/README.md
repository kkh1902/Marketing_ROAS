# 🔄 E2E Tests - End-to-End Pipeline Testing

End-to-End 테스트는 **전체 데이터 파이프라인의 흐름**을 검증합니다.
Kafka 데이터 수집부터 PostgreSQL 저장, dbt 변환, Streamlit 시각화까지의 전체 과정을 테스트합니다.

---

## 📊 Integration vs E2E 비교

| 항목 | Integration | E2E |
|------|-------------|-----|
| **범위** | 각 계층별 독립 테스트 | 전체 파이프라인 흐름 |
| **예시** | Kafka Producer 테스트 | Kafka → Flink → PostgreSQL |
| **인프라** | 단일 서비스 | 전체 스택 |
| **시간** | 빠름 (5-10분) | 느림 (10-30분) |
| **목표** | 컴포넌트 검증 | 엔드투엔드 검증 |

---

## 🏗️ 구조

```
tests/e2e/
├── README.md                      # 이 파일
├── conftest.py                    # Pytest fixtures (Kafka 설정)
├── __init__.py
│
├── test_full_pipeline.py          # 전체 파이프라인 흐름 테스트 (미구현)
│   ├─ test_kafka_to_flink_flow
│   ├─ test_flink_to_postgres_flow
│   └─ test_full_pipeline_latency
│
├── test_data_quality.py           # 데이터 품질 검증 (미구현)
│   ├─ test_data_uniqueness
│   ├─ test_data_completeness
│   └─ test_ctr_calculation
│
└── test_performance.py            # 성능 테스트 (미구현)
    ├─ test_throughput
    ├─ test_latency
    └─ test_memory_usage
```

---

## 🚀 필요한 인프라

### 필수 (E2E 테스트 실행)
```
✅ Kafka
   - bootstrap-servers: localhost:9092
   - zookeeper: localhost:2181
   - schema-registry: localhost:8081

✅ PostgreSQL
   - host: localhost
   - port: 5432
   - database: marketing_roas
   - user: postgres
```

### 선택 (전체 파이프라인 테스트)
```
⏳ Flink JobManager & TaskManager
   - jobmanager: localhost:8081
   - taskmanager: 포트 6122+

⏳ Airflow (DAG 스케줄링 테스트)
   - webserver: localhost:8080

⏳ Streamlit (UI 통합 테스트)
   - server: localhost:8501
```

---

## 🧪 테스트 시나리오

### **Scenario 1: Kafka → Flink → PostgreSQL 전체 흐름**

```
1️⃣ Kafka Producer
   └─ test_ad_events_raw 토픽에 샘플 데이터 발송

2️⃣ Flink Streaming Job
   └─ 데이터 수신 및 CTR 계산

3️⃣ PostgreSQL 저장
   └─ realtime.ad_events 테이블 검증

4️⃣ 검증
   ✅ 데이터 개수 확인
   ✅ CTR 계산 정확성
   ✅ 저장 완료
```

**테스트 케이스:**
- 단일 메시지 처리
- 배치 메시지 처리 (100, 1000개)
- 메시지 손실 확인
- 처리 시간 측정

### **Scenario 2: dbt 변환 검증**

```
1️⃣ PostgreSQL realtime 스키마에 데이터 있음

2️⃣ dbt run 실행
   └─ stg_ad_events
   └─ int_hourly_agg
   └─ dim_campaigns
   └─ fct_daily_metrics

3️⃣ 검증
   ✅ 모든 테이블 생성됨
   ✅ 행 개수 확인
   ✅ 계산 정확성 (CTR)
   ✅ 테스트 통과
```

**테스트 케이스:**
- dbt run 성공 여부
- 모델별 행 개수 확인
- CTR 계산 정확성
- 17개 커스텀 테스트 통과

### **Scenario 3: 데이터 품질**

```
✅ 중복 제거 확인
✅ NULL 값 처리
✅ 데이터 타입 검증
✅ 범위 검증 (CTR 0-100%)
✅ 관계 무결성 (FK 확인)
```

---

## 📋 실행 방법

### **1️⃣ 인프라 시작**

```bash
# 전체 스택 실행
docker-compose up -d

# 또는 필수 서비스만
docker-compose up -d postgres zookeeper kafka broker schema-registry
```

### **2️⃣ E2E 테스트 실행**

```bash
# 모든 E2E 테스트 실행
pytest tests/e2e/ -v

# 특정 테스트만 실행
pytest tests/e2e/test_full_pipeline.py -v

# 특정 테스트 함수 실행
pytest tests/e2e/test_full_pipeline.py::test_kafka_to_flink_flow -v

# 상세 로그 출력
pytest tests/e2e/ -v -s

# 성능 메트릭 포함
pytest tests/e2e/ -v --durations=10
```

### **3️⃣ 커버리지 확인**

```bash
pytest tests/e2e/ --cov=kafka --cov=flink --cov-report=html
```

### **4️⃣ 결과 확인**

```bash
# 최근 테스트 결과
cat htmlcov/index.html  # 브라우저에서 열기
```

---

## 🔧 Fixtures 설명

### **conftest.py**

#### `kafka_bootstrap_servers`
```python
@pytest.fixture(scope="session")
def kafka_bootstrap_servers():
    """Kafka Bootstrap 서버 주소"""
    return os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
```
- 모든 테스트에서 Kafka 연결 정보 제공
- 환경변수로 커스터마이징 가능

#### `kafka_producer`
```python
@pytest.fixture(scope="function")
def kafka_producer(kafka_bootstrap_servers):
    """실제 Kafka Producer (테스트용)"""
    # 테스트 메시지 발송에 사용
```
- 테스트용 Kafka Producer
- 함수별로 새로 생성/정리

#### `kafka_consumer`
```python
@pytest.fixture(scope="function")
def kafka_consumer(kafka_bootstrap_servers):
    """실제 Kafka Consumer (테스트용)"""
    # 테스트 메시지 수신에 사용
```
- 테스트용 Kafka Consumer
- 함수별로 새로 생성/정리

#### `clear_test_topics`
```python
@pytest.fixture(scope="function")
def clear_test_topics():
    """테스트 토픽의 메시지 정리"""
    # 테스트 전/후 토픽 초기화
```

### **테스트 토픽 상수**

```python
TEST_RAW_TOPIC = "test_ad_events_raw"      # Kafka Producer 전송 토픽
TEST_RETRY_TOPIC = "test_ad_events_retry"  # Retry Consumer 토픽
TEST_DLQ_TOPIC = "test_ad_events_dlq"      # Dead Letter Queue 토픽
```

---

## 📝 작성 예정 테스트

### **test_full_pipeline.py** (미구현)

```python
def test_kafka_to_flink_flow(kafka_producer, kafka_consumer):
    """Kafka → Flink 데이터 흐름 테스트"""
    # 1. 테스트 메시지 발송
    # 2. Flink에서 처리될 때까지 대기
    # 3. PostgreSQL에서 검증

def test_flink_to_postgres_flow():
    """Flink → PostgreSQL 저장 테스트"""
    # 1. 데이터 개수 확인
    # 2. 계산 정확성 검증 (CTR)
    # 3. 타임스탐프 검증

def test_full_pipeline_latency():
    """전체 파이프라인 지연시간 측정"""
    # 1. 시작 시간 기록
    # 2. 메시지 발송
    # 3. PostgreSQL 저장 시간 측정
    # 4. SLA 확인 (< 5초)
```

### **test_data_quality.py** (미구현)

```python
def test_data_uniqueness():
    """중복 제거 확인"""
    # SELECT id FROM realtime.ad_events
    # GROUP BY id HAVING COUNT(*) > 1

def test_data_completeness():
    """데이터 완전성 확인"""
    # 필수 컬럼 NULL 체크

def test_ctr_calculation():
    """CTR 계산 정확성"""
    # CTR = clicks / impressions * 100
    # 검증: 0 ≤ CTR ≤ 100
```

### **test_performance.py** (미구현)

```python
def test_throughput():
    """처리량 측정"""
    # 1초에 몇 개 메시지 처리?

def test_latency():
    """지연시간 측정"""
    # Kafka 발송 → PostgreSQL 저장 시간

def test_memory_usage():
    """메모리 사용량 모니터링"""
    # Flink 메모리 사용량 확인
```

---

## 🔍 트러블슈팅

### Q: Kafka 연결 실패
```bash
# Kafka 상태 확인
docker-compose ps kafka

# Kafka 로그 확인
docker-compose logs kafka

# 해결
docker-compose down
docker-compose up -d kafka zookeeper
```

### Q: PostgreSQL 데이터 없음
```bash
# PostgreSQL 연결 확인
psql -h localhost -U postgres -d marketing_roas

# 테이블 확인
\dt realtime.*

# 데이터 확인
SELECT COUNT(*) FROM realtime.ad_events;
```

### Q: Flink 작업이 실행 안 됨
```bash
# Flink JobManager 상태
curl http://localhost:8081/v1/overview

# 작업 제출
flink run -m localhost:8081 -py flink/src/ctr_streaming.py
```

### Q: 테스트 타임아웃
```bash
# 타임아웃 값 증가
pytest tests/e2e/ --timeout=300  # 5분

# 또는 conftest.py에서
@pytest.fixture
def long_timeout():
    import signal
    signal.alarm(300)
```

---

## 📊 테스트 실행 예시

```bash
# 1. 인프라 시작
$ docker-compose up -d
Starting postgres ... done
Starting kafka ... done

# 2. E2E 테스트 실행
$ pytest tests/e2e/ -v
test_kafka_to_flink_flow PASSED
test_flink_to_postgres_flow PASSED
test_data_quality PASSED
test_full_pipeline_latency PASSED

============= 4 passed in 45.23s =============

# 3. 결과 확인
✅ 모든 테스트 통과
✅ 평균 지연시간: 2.1초
✅ 처리량: 1,000 msg/sec
```

---

## 🎯 E2E 테스트 체크리스트

### 실행 전
- [ ] Docker 설치 및 실행
- [ ] Kafka 포트 9092 열려있음
- [ ] PostgreSQL 포트 5432 열려있음
- [ ] Python 3.10+ 설치
- [ ] 의존성 설치: `pip install pytest kafka-python psycopg2`

### 실행 중
- [ ] 모든 E2E 테스트 통과
- [ ] 데이터 정합성 확인
- [ ] 성능 메트릭 확인
- [ ] 로그에 에러 없음

### 완료 후
- [ ] 테스트 결과 기록
- [ ] 성능 메트릭 저장
- [ ] 인프라 정리 (`docker-compose down`)
- [ ] CI/CD 파이프라인에 추가

---

## 🔗 관련 문서

- [Integration 테스트](../integration/README.md)
- [Unit 테스트](../unit/README.md)
- [Kafka 구성](../../kafka/README.md)
- [Flink 파이프라인](../../flink/README.md)
- [dbt 모델](../../dbt/README.md)

---

**마지막 업데이트**: 2024-12-20
**상태**: E2E 테스트 계획 단계 🚀
