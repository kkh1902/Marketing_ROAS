# Week 3: 배치 처리 & 모니터링 완성

## 목표
Airflow 배치 파이프라인, dbt 변환, 모니터링/알림 시스템을 완성합니다.

## 세부 작업

### 3-1. Airflow 설정 및 DAG 구축 (2일)
- [ ] Airflow Docker 구성 (localhost:8080)
- [ ] DAG 디렉토리 구조 설계
- [ ] `dag_daily_etl` 작성
  - 로컬 파일 (`./data/raw/`) 읽기
  - 데이터 검증
  - 처리된 데이터 저장 (`./data/processed/`)
- [ ] `dag_dbt_run` 작성 (dbt 트리거)
- [ ] `dag_dlq_retry` 작성 (DLQ 재처리)
- [ ] `dag_dlq_alert` 작성 (에러 알림)
- [ ] DAG 스케줄링 설정 (매일 자정)
- [ ] 의존성 관계 정의

**산출물:**
- `src/airflow/dags/dag_daily_etl.py`
- `src/airflow/dags/dag_dbt_run.py`
- `src/airflow/dags/dag_dlq_retry.py`
- `src/airflow/dags/dag_dlq_alert.py`
- `docker-compose.yml` 업데이트 (Airflow 추가)

### 3-2. dbt 모델 설계 및 구현 (2.5일)
- [ ] dbt 프로젝트 초기화
- [ ] 소스 정의 (PostgreSQL realtime schema)
- [ ] Stage 모델 작성 (stg_events, stg_metrics)
- [ ] Mart 모델 작성
  - `mart_daily_ctr` (일별 CTR)
  - `mart_hourly_ctr` (시간별 CTR)
  - `mart_device_performance` (기기별 성과)
  - `mart_category_analysis` (카테고리별 분석)
- [ ] 데이터 테스트 작성
  - Null 체크
  - 고유값 테크
  - 참조 무결성 확인
- [ ] 문서화
- [ ] dbt run & dbt test 실행

**산출물:**
- `dbt_project.yml` (프로젝트 설정)
- `models/staging/` (Stage 모델들)
- `models/marts/` (Mart 모델들)
- `tests/` (데이터 테스트)
- `docs/` (생성된 문서)

### 3-3. DLQ 에러 처리 시스템 (1.5일)
- [ ] PostgreSQL `errors` schema 생성
  - `dlq_errors` 테이블 (에러 저장)
  - `retry_history` 테이블 (재처리 이력)
- [ ] DLQ Consumer 구현
  - Kafka `ad_events_error` 토픽 구독
  - 에러 로깅
  - 재처리 큐에 추가
- [ ] 재처리 로직 구현
  - Exponential backoff 전략
  - 최대 재시도 횟수 설정
  - 실패 알림

**산출물:**
- `src/dlq/dlq_consumer.py` (DLQ 컨슈머)
- `src/dlq/retry_handler.py` (재처리 로직)
- `src/postgres/dlq_schema.sql` (DLQ 스키마)

### 3-4. 모니터링 및 알림 시스템 (1.5일)
- [ ] Prometheus 설정 완성
  - Kafka JMX 메트릭
  - Flink 메트릭
  - PostgreSQL 메트릭
- [ ] Grafana 대시보드 구축 (localhost:3001)
  - 실시간 처리량
  - 레이턴시 분포
  - 에러율
  - 리소스 사용률
- [ ] Slack 통합
  - Airflow DAG 실패 알림
  - 데이터 품질 테스트 실패 알림
  - 에러율 임계값 알림
  - 일일 요약 보고서
- [ ] Alert Rule 작성
  - 처리량 < 1,000/min
  - 레이턴시 > 5초
  - 에러율 > 1%

**산출물:**
- `config/prometheus.yml` (수정)
- `config/grafana/` (대시보드 JSON)
- `config/slack_config.json` (Slack 연동)
- `config/alert_rules.yml` (알림 규칙)

### 3-5. Metabase 분석 대시보드 (1.5일)
- [ ] Metabase Docker 설정 (localhost:3000)
- [ ] PostgreSQL analytics schema 연동
- [ ] 분석 대시보드 작성
  - CTR 추이 분석
  - 기기별 성과 비교
  - 사이트/앱 카테고리 분석
  - 배너 위치별 효과 분석
- [ ] 필터 및 드릴다운 설정
- [ ] 공유 및 임베딩 설정

**산출물:**
- `docker-compose.yml` 업데이트 (Metabase 추가)
- Metabase 대시보드 설정 파일

### 3-6. 문서화 및 배포 준비 (1일)
- [ ] 전체 시스템 아키텍처 문서 작성
- [ ] 운영 가이드 작성
  - 시작/종료 절차
  - 트러블슈팅
  - 성능 최적화 팁
- [ ] 개발자 가이드 작성
- [ ] 배포 체크리스트 작성

**산출물:**
- `docs/DEPLOYMENT.md` (배포 가이드)
- `docs/OPERATIONS.md` (운영 가이드)
- `docs/TROUBLESHOOTING.md` (트러블슈팅)
- `docs/ARCHITECTURE_FINAL.md` (최종 아키텍처)

## 주간 마일스톤
- ✅ Airflow에서 모든 DAG 정상 실행
- ✅ dbt로 4개 이상의 mart 테이블 생성
- ✅ 모든 데이터 테스트 통과
- ✅ DLQ 에러 처리 시스템 작동 중
- ✅ Grafana 모니터링 대시보드 실시간 표시
- ✅ Slack 알림 정상 전달
- ✅ Metabase 분석 대시보드 완성

## 성능 지표
- 데이터 처리 완성도: 100%
- dbt 테스트 통과율: 100%
- DAG 성공률: 100%
- 대시보드 조회 응답시간: < 2초

## 위험요소
- 리소스 부족 (메모리, CPU) → 최적화 및 확장 계획
- 데이터 일관성 문제 → dbt 테스트 강화
- Slack 알림 과다 → 임계값 재조정

## 완료 체크리스트
- [ ] 전체 파이프라인 엔드-투-엔드 테스트
- [ ] 문서화 완료
- [ ] 팀 리뷰 및 피드백 반영
- [ ] 운영 체계 확립
- [ ] 고가용성/재해복구 계획 수립

## 향후 개선 계획
- 클라우드 배포 (GCP, AWS, Azure)
- 머신러닝 모델 통합
- 실시간 이상탐지
- A/B 테스트 기능 추가
