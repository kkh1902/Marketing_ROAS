# 🎯 Airflow - Orchestration Layer

Apache Airflow를 활용한 **배치 파이프라인 자동화 및 스케줄링**입니다.
Flink 실시간 처리 완료 후 dbt로 데이터를 변환하는 DAG를 관리합니다.

---

## 📦 구조

```
airflow/
├── README.md                      # 이 파일
├── Dockerfile                     # Airflow 컨테이너 환경
├── requirements.txt               # Python 의존성 (airflow, dbt-postgres)
├── config/
│   └── airflow.cfg               # Airflow 설정 파일
└── dags/                         # DAG 정의 폴더
    ├── __init__.py
    ├── dag_dbt_run.py           # dbt 모델 실행 DAG (매일 00:00)
    └── dag_daily_etl.py         # 일일 ETL DAG (미구현)
```

---

## 🔄 파이프라인 흐름

```
Flink 완료 (realtime 스키마에 데이터 저장)
    ↓ (매일 00:00)
Airflow Scheduler
    ├─ dag_dbt_run.py
    │  ├─ dbt run (모델 실행)
    │  ├─ dbt test (데이터 검증)
    │  └─ PostgreSQL analytics 스키마 저장
    │
    └─ dag_daily_etl.py (미구현)
       ├─ 추가 변환 작업
       └─ 비즈니스 로직 처리
```

---

## 🛠️ 주요 DAG

### **1️⃣ dag_dbt_run.py** (구현 중)
```yaml
스케줄: 매일 00:00 (UTC)
작업:
  ├─ dbt_run: dbt 모델 실행
  │  └─ stg_ad_events → int_hourly_agg → fct_daily_metrics
  └─ dbt_test: 데이터 검증
     └─ 17개 커스텀 테스트 + YAML 테스트

의존성: Flink 완료 필수
출력: PostgreSQL analytics 스키마
```

**특징:**
- 실패 시 자동 재시도 (3회)
- 실패 시 Slack 알림
- SLA 모니터링 (1시간 이내 완료)

### **2️⃣ dag_daily_etl.py** (미구현)
```yaml
스케줄: 매일 06:00 (UTC)
작업:
  ├─ validate_source_data
  ├─ run_dbt_models
  └─ generate_reports

의존성: dag_dbt_run.py 완료 필수
```

---

## 🚀 실행 방법

### 1️⃣ Airflow 시작

```bash
cd airflow

# Docker Compose로 시작
docker-compose up -d airflow-webserver airflow-scheduler

# 또는 로컬에서
airflow db init
airflow webserver -p 8080 &
airflow scheduler &
```

### 2️⃣ Airflow 웹 UI 접속
- **URL**: http://localhost:8080
- **기본 계정**: `airflow` / `airflow`

### 3️⃣ DAG 활성화

```bash
# CLI로 DAG 활성화
airflow dags unpause dag_dbt_run

# 또는 웹 UI에서 토글 버튼 클릭
```

### 4️⃣ DAG 수동 실행 (테스트)

```bash
# 수동 트리거
airflow dags trigger -e 2024-12-20 dag_dbt_run

# 또는 웹 UI의 "Trigger DAG" 버튼 클릭
```

### 5️⃣ 로그 확인

```bash
# 특정 DAG 로그
airflow tasks logs dag_dbt_run dbt_run 2024-12-20

# 또는 웹 UI에서 Task Instance 클릭
```

---

## 📋 DAG 상세 설정

### **스케줄 표현식 (Cron)**

```yaml
dag_dbt_run:
  schedule_interval: "0 0 * * *"    # 매일 00:00 (UTC)

dag_daily_etl:
  schedule_interval: "0 6 * * *"    # 매일 06:00 (UTC)
```

**UTC 시간 변환:**
- UTC 00:00 = KST 09:00
- UTC 06:00 = KST 15:00

### **재시도 정책**

```python
default_args = {
    'retries': 3,                  # 3회 재시도
    'retry_delay': timedelta(minutes=5),  # 5분 간격
    'on_failure_callback': slack_notify  # 실패 시 Slack 알림
}
```

### **SLA (Service Level Agreement)**

```python
sla = timedelta(hours=1)  # 1시간 내에 완료해야 함
```

---

## 🔧 Airflow 설정

### **config/airflow.cfg** 주요 설정

| 항목 | 설명 |
|------|------|
| `executor` | LocalExecutor (또는 CeleryExecutor) |
| `sql_alchemy_conn` | PostgreSQL 연결 (메타데이터 저장) |
| `base_log_folder` | 로그 저장 경로 |
| `dag_folder` | DAG 폴더 경로 (`./dags`) |
| `schedule_interval` | 기본 스케줄 간격 |

---

## 📊 모니터링

### **Airflow 웹 UI 확인 항목**

1. **DAG 상태**
   - 성공/실패 여부
   - 최근 실행 시간
   - 다음 예정 실행

2. **Task 상태**
   - 각 작업별 성공/실패
   - 실행 시간
   - 로그

3. **SLA 모니터링**
   - SLA 위반 알림
   - 예상 완료 시간 대비 실제 완료 시간

---

## 🔗 의존성

### **dbt와 통합**

```bash
# DAG에서 dbt 실행
BashOperator(
    task_id='dbt_run',
    bash_command='cd /dbt && dbt run --profiles-dir .',
)
```

### **PostgreSQL 연결**

```yaml
Database: marketing_roas
Schema: analytics (dbt 모델 저장)
Connection: PostgreSQL
```

---

## 🧪 DAG 테스트

### **DAG 유효성 검사**

```bash
# 문법 확인
python dags/dag_dbt_run.py

# DAG 렌더링 확인
airflow dags test dag_dbt_run 2024-12-20
```

### **Task 단위 테스트**

```bash
# 특정 작업 테스트
airflow tasks test dag_dbt_run dbt_run 2024-12-20

# 작업 완료 시간 예측
airflow tasks render dag_dbt_run dbt_run 2024-12-20
```

---

## 🔍 트러블슈팅

### Q: DAG가 보이지 않음
```bash
# DAG 폴더 확인
ls -la dags/

# Airflow 캐시 초기화
airflow dags list

# 만약 안 보이면 scheduler 재시작
airflow scheduler --help
```

### Q: Task 실패 (dbt 에러)
```bash
# 로그 확인
airflow tasks logs dag_dbt_run dbt_run -1

# dbt 직접 실행으로 검증
cd /dbt
dbt run --profiles-dir .
dbt test
```

### Q: PostgreSQL 연결 에러
```bash
# 연결 테스트
airflow connections test postgres_default

# 또는 수동 테스트
psql -h postgres -U postgres -d marketing_roas -c "SELECT 1"
```

### Q: 메모리 부족
```bash
# Airflow 설정에서 병렬성 감소
parallelism: 4  # 동시 실행 작업 수
max_active_tasks_per_dag: 2
```

---

## 📈 성능 최적화

### **병렬 처리**

```python
# 동시에 여러 작업 실행
airflow_config = {
    'parallelism': 4,           # 전체 병렬 작업 수
    'max_active_dag_runs': 2,   # DAG별 최대 실행 수
}
```

### **리소스 제약**

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

---

## 📅 개발 일정

| 단계 | 작업 | 상태 |
|------|------|------|
| 1 | dag_dbt_run.py 구현 | 🔄 진행중 |
| 2 | dag_dbt_run.py 테스트 | ⏳ 대기 |
| 3 | dag_daily_etl.py 구현 | ⏳ 대기 |
| 4 | Slack 알림 연동 | ⏳ 대기 |
| 5 | 모니터링 대시보드 | ⏳ 대기 |

---

## 🔗 관련 문서

- [Airflow 공식 문서](https://airflow.apache.org/)
- [Airflow dbt 통합](https://airflow.apache.org/docs/apache-airflow-providers-dbt-cloud/stable/)
- [dbt 실행 가이드](../dbt/README.md)
- [Flink 파이프라인](../flink/README.md)

---

## 📧 자주 묻는 질문

### Q: Airflow는 뭐예요?
**A:** 데이터 파이프라인을 **코드로 정의하고 자동화하는 도구**입니다.
- 스케줄: 매일 자동으로 실행
- 모니터링: 실패/성공 상태 추적
- 알림: 문제 발생시 즉시 알림

### Q: 왜 dbt를 Airflow에서 실행하나?
**A:** Flink와 dbt를 자동으로 연결하기 위해서입니다.
```
Flink (자동, 실시간)
  ↓ (Airflow가 조율)
dbt (스케줄링된, 배치)
  ↓
분석용 데이터 준비
```

### Q: 실패하면?
**A:** 자동 재시도 + Slack 알림
- 3회까지 자동 재시도
- 최종 실패시 Slack 채널에 알림
- 웹 UI에서 실패 원인 확인

---

## 💡 Best Practices

### ✅ DO
- DAG를 작고 단순하게 유지
- 각 Task에 description 추가
- 실패 처리 (on_failure_callback) 정의
- 로그를 자세히 남기기

### ❌ DON'T
- Task를 과도하게 많이 만들기
- 하드코딩된 경로/날짜 사용
- 에러 처리 없이 DAG 작성
- 무한 재시도 (최대 횟수 설정)

---

**마지막 업데이트**: 2024-12-20
**상태**: 개발 진행중 🚀
