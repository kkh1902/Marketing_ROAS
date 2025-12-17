# Integration Tests

실제 인프라(Kafka + PostgreSQL)와의 상호작용을 테스트합니다.

## Fixtures

[conftest.py](conftest.py)에서 제공:

- `kafka_producer`: Kafka Producer
- `kafka_consumer`: Kafka Consumer
- `postgres_connection`: PostgreSQL 연결
- `postgres_cursor`: PostgreSQL 커서
- `temp_log_dir`: 임시 로그 디렉토리

## 테스트 토픽

```python
TEST_RAW_TOPIC = "test_ad_events_raw"      # Producer 메시지
TEST_RETRY_TOPIC = "test_ad_events_retry"  # Retry 메시지
TEST_DLQ_TOPIC = "test_ad_events_dlq"      # DLQ 메시지
```

## 작성해야 할 테스트

### 1. test_producer_kafka_integration.py
- [ ] CSV 읽기 → Kafka 발행
- [ ] Kafka에서 메시지 수신 확인
- [ ] 배치 메시지 발행

### 2. test_flink_streaming_integration.py
- [ ] Kafka 메시지 → Flink 수신 확인
- [ ] 1분 Tumbling Window CTR 집계
- [ ] 결과 → PostgreSQL realtime.ctr_metrics 저장

### 3. test_dlq_consumer_integration.py
- [ ] 실패 메시지 → DLQ Topic
- [ ] DLQ → PostgreSQL errors 테이블 저장
- [ ] 에러 로그 기록

### 4. test_retry_consumer_integration.py
- [ ] Retry Topic 메시지 수신
- [ ] 지수 백오프 재시도 (1초, 2초, 4초)
- [ ] 최대 재시도 초과 → DLQ 전송

## 실행

```bash
# 모든 Integration 테스트
pytest tests/integration -v

# 특정 테스트만
pytest tests/integration/test_producer_kafka_integration.py -v

# 마크로
pytest -m integration -v
```

## PostgreSQL 스키마

### realtime 스키마 (Flink 실시간 메트릭)
```sql
CREATE TABLE realtime.ctr_metrics (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    ctr FLOAT,
    impressions INT,
    clicks INT
);
```

### errors 스키마 (DLQ 에러 로그)
```sql
CREATE TABLE errors.dlq_messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR,
    error_message TEXT,
    retry_count INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 환경 변수

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## 사전 요구사항

```bash
# 인프라 시작
docker-compose up -d

# 확인
docker-compose ps

# PostgreSQL 스키마 생성 필요
# - realtime.ctr_metrics
# - errors.dlq_messages
```
