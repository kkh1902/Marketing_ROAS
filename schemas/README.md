# Schemas Directory

데이터 파이프라인에서 사용되는 모든 스키마 정의를 관리하는 디렉토리입니다.

## 파일 구조

### 1. `ad_event.avsc`
**Apache Avro 포맷 스키마** - Kafka 메시지 포맷

광고 클릭 이벤트 데이터의 스키마를 정의합니다.

**주요 필드:**
- `id`: 광고 ID (고유 식별자)
- `click`: 클릭 여부 (0=노출만, 1=클릭)
- `hour`: 타임스탬프 (YYMMDDHH 형식, UTC)
- `site_*`: 사이트 관련 정보 (ID, 도메인, 카테고리)
- `app_*`: 모바일 앱 관련 정보 (ID, 도메인, 카테고리)
- `device_*`: 기기 정보 (ID, IP, 모델, 타입, 연결 타입 등)
- `C1, C14-C21`: 익명화된 카테고리 변수

**용도:**
- Kafka 토픽에 publish되는 광고 이벤트 메시지 검증
- Flink 스트리밍 작업에서 데이터 역직렬화
- Schema Registry를 통한 버전 관리

### 2. `ctr_metric.avsc`
**Apache Avro 포맷 스키마** - CTR 메트릭 출력

Flink 스트리밍에서 집계된 CTR 메트릭의 스키마입니다.

**용도:**
- Flink에서 생성한 집계 메트릭을 Kafka로 전송할 때 사용
- CTR 메트릭 아웃풋의 데이터 구조 정의

### 3. `realtime_ctr_metrics.sql`
**PostgreSQL DDL 스크립트** - 원본 이벤트 및 실시간 메트릭 저장소

Kafka에서 수신한 원본 이벤트와 Flink에서 집계한 CTR 메트릭을 저장하는 PostgreSQL 스키마입니다.

**생성되는 객체:**

#### 테이블 (원본 데이터)
- **`realtime.ad_events`**: Kafka에서 수신한 원본 광고 이벤트
  - `event_id`: 이벤트 고유 ID (자동 증가, PRIMARY KEY)
  - `id`: 광고 ID
  - `click`: 클릭 여부 (0=노출, 1=클릭)
  - `hour`: 타임스탬프 (YYMMDDHH 형식, UTC)
  - `banner_pos`: 배너 위치
  - `site_*`: 사이트 정보 (ID, 도메인, 카테고리)
  - `app_*`: 모바일 앱 정보 (ID, 도메인, 카테고리)
  - `device_*`: 기기 정보 (ID, IP, 모델, 타입, 연결 타입)
  - `C1, C14-C21`: 익명화된 카테고리 변수
  - 인덱스: `hour`, `created_at`, `event_time`, `site_id`, `device_id`
  - 용도: 원본 데이터 보관, 추후 재분석, 감사(audit)

#### 테이블 (집계 데이터)
- **`realtime.ctr_metrics_1min`**: 1분 단위 Tumbling Window 집계 결과
  - `window_start`, `window_end`: 윈도우 시간 범위
  - `impressions`, `clicks`: 노출 및 클릭 건수
  - `ctr`: Click-Through Rate (%)
  - 인덱스: `window_start`, `created_at`, `window_range`

- **`realtime.ctr_metrics_5min`**: 5분 단위 Tumbling Window 집계 결과
  - 구조는 1분 테이블과 동일

#### 뷰
- **`realtime.latest_ctr_1min`**: 최근 1시간 1분 단위 메트릭
- **`realtime.latest_ctr_5min`**: 최근 2시간 5분 단위 메트릭

#### 함수 (통계)
- **`realtime.get_avg_ctr_1h()`**: 최근 1시간 평균 CTR 계산

#### 함수 (데이터 보관 정책)
- **`realtime.cleanup_old_events(days INT)`**: 지정된 일수 이상 된 ad_events 삭제
  - 기본값: 90일
  - 반환: 삭제된 행 수
  - 예: `SELECT realtime.cleanup_old_events(90);`

- **`realtime.optimize_tables()`**: 모든 테이블 VACUUM ANALYZE
  - ad_events, ctr_metrics_1min, ctr_metrics_5min 최적화
  - 쿼리 성능 개선 및 저장 공간 회수

- **`realtime.maintenance()`**: 통합 유지보수 함수
  - 1단계: 오래된 데이터 정리
  - 2단계: 테이블 최적화
  - 3단계: 완료 보고

**용도:**
- Flink 스트리밍 결과를 저장하는 데이터베이스 구조 정의
- 대시보드 및 분석 쿼리의 기반 데이터 소스

## 데이터 흐름

### 전체 파이프라인

```
┌─────────────────────┐
│ Kafka (ad_event)    │
├─────────────────────┤
│  [ad_event.avsc]    │
└──────────┬──────────┘
           │
        ┌──┴──┐
        │     │
        │     │ ┌─────────────────────────────────────┐
        │     │ │ PostgreSQL (realtime schema)        │
        │     │ ├─────────────────────────────────────┤
        │     └─→ realtime.ad_events (원본 저장)     │
        │       │                                      │
        │       │ ✓ 원본 데이터 보관 (audit trail)   │
        │       │ ✓ 재분석 가능                       │
        │       │ ✓ 데이터 재처리 가능                │
        │       └─────────────────────────────────────┘
        │
        │ Flink Streaming (ctr_streaming.py)
        │
        └──────┬──────────┐
               │          │
      1min & 5min    [ctr_metric.avsc]
      Tumbling       (Kafka 출력)
      Windows
               │
               ↓
    ┌─────────────────────────────────────┐
    │ PostgreSQL (realtime schema)         │
    ├─────────────────────────────────────┤
    │ realtime.ctr_metrics_1min   (집계)  │
    │ realtime.ctr_metrics_5min   (집계)  │
    │ realtime.latest_ctr_1min    (뷰)    │
    │ realtime.latest_ctr_5min    (뷰)    │
    └──────────┬──────────────────────────┘
               │
               ↓
    ┌─────────────────────────────────────┐
    │ Dashboard / Analytics / API         │
    └─────────────────────────────────────┘
```

### 세부 사항

- **원본 저장소**: `realtime.ad_events`에 모든 원본 이벤트 저장
- **집계 처리**: Flink가 1분/5분 Tumbling Window로 CTR 계산
- **결과 저장**: 집계 결과를 `realtime.ctr_metrics_*min` 테이블에 저장
- **빠른 조회**: 뷰(`latest_ctr_*min`)를 통해 최신 메트릭에 빠르게 접근

## 스키마 관리 및 배포

### PostgreSQL 스키마 적용
```bash
psql -h <host> -U <user> -d <database> -f realtime_ctr_metrics.sql
```

### Avro 스키마 등록 (Schema Registry)
```bash
# Schema Registry 서버에 등록
curl -X POST http://localhost:8081/subjects/ad_event/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d @ad_event.avsc
```

### Flink에서 스키마 사용
```python
from confluent_kafka import avro
# Avro 스키마 로드 및 검증
```

## 참고 사항

### 데이터 관리
- 모든 타임스탐프는 **UTC** 기준입니다.
- 광고 이벤트의 개인 식별 정보(ID, IP, 모델)는 익명화되어 있습니다.
- CTR은 백분율(%)로 저장됩니다. (예: 19.90 = 19.90%)
- PostgreSQL 인덱스는 조회 성능 최적화를 위해 설계되었습니다.

### 데이터 보관 정책 (Retention Policy)

#### 원본 이벤트 (`realtime.ad_events`)
- **보관 기간**: 90일 (설정 변경 가능)
- **용도**: 감사(audit) 추적, 데이터 재분석, 모델 학습 재처리
- **정리 방법**:
  ```sql
  -- 수동 정리
  SELECT realtime.cleanup_old_events(90);

  -- 또는 다른 기간 설정
  SELECT realtime.cleanup_old_events(180);  -- 180일
  ```
- **주의**: 저장 공간이 크므로 정기적인 정리 필수

#### 집계 메트릭 (`realtime.ctr_metrics_*min`)
- **보관 기간**: 무제한 (또는 필요시 정책 수정)
- **용도**: 대시보드 및 실시간 분석
- **최적화**: 뷰(`latest_ctr_*min`)로 최신 데이터 빠른 접근

#### 자동 정리 스케줄 (선택)
**pg_cron 확장 사용 (매주 일요일 02:00 실행)**
```bash
# 1. PostgreSQL 컨테이너 접속
docker-compose exec postgres bash

# 2. pg_cron 확장 설치
psql -U admin -d my-app-db -c "CREATE EXTENSION IF NOT EXISTS pg_cron;"

# 3. 자동 스케줄 등록
psql -U admin -d my-app-db -c "
  SELECT cron.schedule('cleanup-old-events', '0 2 * * 0', 'SELECT realtime.cleanup_old_events()');
  SELECT cron.schedule('optimize-tables', '0 3 * * 0', 'SELECT realtime.optimize_tables()');
"

# 4. 스케줄 확인
psql -U admin -d my-app-db -c "SELECT * FROM cron.job;"
```

#### 테이블 최적화
```sql
-- 모든 테이블 최적화
SELECT realtime.optimize_tables();

-- 또는 통합 유지보수
SELECT realtime.maintenance();
```
- **목적**: 삭제된 데이터로 인한 빈 공간 회수 (VACUUM)
- **효과**: 쿼리 성능 개선, 저장 공간 절약
- **주기**: 주 1회 이상 권장 (자동 스케줄 설정)

### Flink 통합
- `ad_events`는 Kafka Consumer로부터 직접 읽을 수 있음
- 원본 → 집계 매핑이 필요한 경우 `event_id`를 활용하여 조인 가능

## 버전 관리

| 파일 | 버전 | 최신 업데이트 | 설명 |
|------|------|-------------|------|
| ad_event.avsc | v1 | 2024-12-16 | 초기 스키마 |
| ctr_metric.avsc | v1 | 2024-12-16 | 초기 스키마 |
| realtime_ctr_metrics.sql | v3 | 2024-12-17 | 데이터 보관 정책 함수 추가 (cleanup, optimize, maintenance) |

## 관련 디렉토리

- [flink/](../flink/): Flink 스트리밍 작업 구현
- [src/](../src/): 메인 애플리케이션 소스 코드
