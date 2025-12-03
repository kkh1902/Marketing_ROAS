# Week 2: 실시간 처리 & 캐싱

## 목표
PyFlink로 실시간 스트리밍 처리를 구현하고, Redis 캐시와 PostgreSQL을 연동합니다.

## 세부 작업

### 2-1. PyFlink 개발환경 구축 (1일)
- [ ] PyFlink 설치 및 로컬 환경 설정
- [ ] Flink JobManager, TaskManager Docker 구성
- [ ] Kafka 소스 연동 테스트
- [ ] 기본 데이터 파이프라인 검증

**산출물:**
- `docker-compose.yml` 업데이트 (Flink 추가)
- `src/flink/config.py` (Flink 설정)

### 2-2. PyFlink 스트리밍 작업 구현 (3일)
- [ ] KafkaSource 설정 (Schema Registry 연동)
- [ ] Event Time + Watermark 설정
- [ ] Tumbling Window 구현 (1분, 5분)
- [ ] CTR 계산 로직 (click / impression)
- [ ] 상태 저장 (State Management)
- [ ] Checkpoint 설정 (`./data/checkpoints/`)

**산출물:**
- `src/flink/streaming_job.py` (메인 스트리밍 작업)
- `src/flink/aggregations.py` (집계 함수)
- Checkpoint 파일들

### 2-3. Redis 캐시 구축 (1.5일)
- [ ] Redis Docker 이미지 설정
- [ ] 실시간 CTR 데이터 저장 구조 설계
- [ ] TTL 설정 (5분 단위)
- [ ] PyFlink → Redis 싱크 구현
- [ ] 캐시 조회 성능 테스트

**산출물:**
- `docker-compose.yml` 업데이트 (Redis 추가)
- `src/redis/cache_manager.py` (캐시 관리)
- `src/redis/schema.py` (데이터 구조)

### 2-4. PostgreSQL 데이터베이스 구축 (1.5일)
- [ ] PostgreSQL Docker 설정
- [ ] `realtime` schema 생성
  - `metrics_1min` 테이블 (1분 집계)
  - `metrics_5min` 테이블 (5분 집계)
  - `raw_events` 테이블 (원본 이벤트)
- [ ] 인덱스 설계 (성능 최적화)
- [ ] PyFlink → PostgreSQL 싱크 구현
- [ ] 데이터 연결성 테스트

**산출물:**
- `docker-compose.yml` 업데이트 (PostgreSQL 추가)
- `src/postgres/schema.sql` (스키마 정의)
- `src/postgres/db_connector.py` (DB 연결)

### 2-5. Streamlit 실시간 대시보드 (2일)
- [ ] Streamlit 앱 구조 설계
- [ ] Redis에서 실시간 CTR 조회 및 표시
- [ ] 차트 구현 (시계열, 카테고리별)
- [ ] 실시간 갱신 기능
- [ ] localhost:8501에서 실행
- [ ] 배포 테스트

**산출물:**
- `src/streamlit/dashboard.py` (메인 앱)
- `src/streamlit/components/` (재사용 컴포넌트)
- `src/streamlit/config.toml` (설정)

## 주간 마일스톤
- ✅ PyFlink 스트리밍 작업 실행 중
- ✅ 1분, 5분 단위 CTR 계산 완료
- ✅ Redis 캐시에 실시간 데이터 저장
- ✅ PostgreSQL realtime 데이터 적재 중
- ✅ Streamlit 대시보드 localhost:8501에서 작동

## 성능 지표
- 메시지 처리 레이턴시: < 1초
- 캐시 조회 응답시간: < 100ms
- 대시보드 갱신 주기: 10초

## 위험요소
- 메모리 누수 (Flink 상태) → Checkpoint 용량 모니터링
- Redis 메모리 부족 → TTL 정책 강화
- 대시보드 느린 응답 → 캐시 최적화

## 다음 주 준비사항
- Airflow 환경 구축
- dbt 모델 설계
- DLQ 재처리 로직 준비
