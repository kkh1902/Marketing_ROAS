# Flink Stream Processing

Apache Flink을 활용한 실시간 광고 클릭 데이터 처리 파이프라인입니다.

---

## 📦 구조

```
flink/
├── src/
│   ├── config.py              # Flink 설정 (Kafka, 병렬성, Checkpoint)
│   ├── ctr_streaming.py       # CTR 스트림 집계 로직
│   └── simple_flink_test.py   # 기본 테스트 작업
├── lib/
│   ├── flink-connector-kafka-*.jar
│   └── kafka-clients-*.jar
├── Dockerfile                 # Flink Python 환경 빌드
└── requirements.txt           # Python 의존성
```

---

## 🚀 실행 방법

**1. Flink 클러스터 시작**
```bash
cd <project-root>
docker-compose up -d jobmanager taskmanager
```

**2. Flink 대시보드 접속**
- URL: [http://localhost:8085](http://localhost:8085)

**3. 작업 제출**
```bash
# 테스트 작업
docker-compose up pyflink-job

# 또는 직접 제출
flink run -m jobmanager:8081 -py src/ctr_streaming.py
```

---

## 🔧 핵심 설정

**[config.py](src/config.py):**

| 항목 | 값 | 설명 |
|------|-----|------|
| `BOOTSTRAP_SERVERS` | `broker:29092` | Kafka 브로커 |
| `TOPIC` | `ad_events_raw` | 소비 토픽 |
| `GROUP_ID` | `flink-consumer-group` | Consumer 그룹 |
| `PARALLELISM` | `1` | 병렬 수준 |
| `CHECKPOINT_INTERVAL` | `60000` (ms) | 상태 저장 주기 |

---

## 📊 컴포넌트

- **JobManager**: 작업 조율 및 관리 (포트 8085)
- **TaskManager**: 데이터 처리 실행 (4 Task Slots)
- **PyFlink Job**: Kafka → CTR 집계

---

## 🧪 작업 상태 확인

```bash
docker-compose logs jobmanager
curl http://localhost:8085/api/v1/jobs
```

---

---

## 💾 데이터베이스 테이블

### Kafka에서 들어오는 데이터

**Topic:** `ad_events_raw`

```json
{
  "id": 1.4199688212321208e+19,
  "click": 0,
  "hour": 14102101,
  "banner_pos": 0,
  "site_id": "12fb4121",
  "site_domain": "6b59f079",
  "site_category": "f028772b",
  "app_id": "ecad2386",
  "app_domain": "7801e8d9",
  "app_category": "07d7df22",
  "device_id": "a99f214a",
  "device_ip": "183586aa",
  "device_model": "8bfcd3c6",
  "device_type": 1,
  "device_conn_type": 0,
  "C1": 1005,
  "C14": 20970,
  "C15": 320,
  "..."
}
```

**노출(Impression) vs 클릭(Click) 구분:**

| 필드 | 값 | 의미 |
|------|-----|------|
| `click` | 0 | 광고 노출 (Impression) |
| `click` | 1 | 클릭 (Click) |

---

### Flink 처리 프로세스

```
Kafka 이벤트 수신
    ↓
1분 Tumbling Window 집계
├─ click=0인 이벤트 개수 → impressions
├─ click=1인 이벤트 개수 → clicks
└─ CTR = (clicks / impressions) × 100
    ↓
5분 Tumbling Window 집계 (동일)
    ↓
PostgreSQL에 저장
```

---

### PostgreSQL 테이블 구조

#### `realtime.ctr_metrics_1min` (1분 집계)

```sql
CREATE TABLE realtime.ctr_metrics_1min (
    metric_id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    impressions INT NOT NULL,
    clicks INT NOT NULL,
    ctr FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_window_start ON realtime.ctr_metrics_1min(window_start);
CREATE INDEX idx_created_at ON realtime.ctr_metrics_1min(created_at);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `metric_id` | SERIAL | 기본 키 |
| `window_start` | TIMESTAMP | 윈도우 시작 시간 |
| `window_end` | TIMESTAMP | 윈도우 종료 시간 |
| `impressions` | INT | 노출 건수 (click=0) |
| `clicks` | INT | 클릭 건수 (click=1) |
| `ctr` | FLOAT | CTR 비율 (0.0 ~ 100.0) |
| `created_at` | TIMESTAMP | 생성 시간 |
| `updated_at` | TIMESTAMP | 수정 시간 |

**예시 데이터:**
```
window_start: 2024-12-16 14:30:00
window_end: 2024-12-16 14:31:00
impressions: 834
clicks: 166
ctr: 16.41
```

---

#### `realtime.ctr_metrics_5min` (5분 집계, 선택)

1분 테이블과 동일 구조, 단 더 큰 집계 윈도우

---

## 📊 데이터 흐름 요약

```
Avazu Dataset (40M rows)
    ↓
Kafka Producer (JSON 변환)
    ↓
Kafka Topic: ad_events_raw
    ↓
Flink PyFlink Job (1분/5분 윈도우 집계)
    ↓
PostgreSQL realtime.ctr_metrics_1min
    ↓
Streamlit 대시보드 (실시간 모니터링)
```

**주요 지표:**
- 원본 데이터: 40,428,967 rows
- 기간: 2014-10-21 ~ 2014-10-31 (10일)
- 평균 CTR: 16.41%

---

## 📌 다음 단계

- [ ] PostgreSQL 테이블 생성 (dbt 또는 SQL 스크립트)
- [ ] Flink Kafka Consumer 구현
- [ ] Flink → PostgreSQL Sink 구현
- [ ] 성능 테스트 (처리량, 지연시간)
- [ ] Savepoint 설정 (장애 복구)
- [ ] 모니터링 대시보드 구성
