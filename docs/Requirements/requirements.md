# 📄 **requirements.md (초안)**

아래 내용을 그대로 복붙해서 저장하면 된다.
추가하고 싶은 요구사항 있으면 바로 확장해줄게.

---

# **Requirements: Ad Events Realtime & Batch Data Pipeline**

## **1. 프로젝트 개요**

광고 플랫폼에서 발생하는 대규모 광고 이벤트 로그(40M rows / 10일)를 실시간·배치 방식으로 처리하여
CTR/CPA/ROAS 등 핵심 메트릭을 빠르게 분석할 수 있는 데이터 파이프라인을 구축한다.

---

## **2. 데이터**

### **2.1 Source Data**

* Dataset: **Avazu Click-Through Prediction**
* Format: `.gz` 압축 CSV
* Volume: **약 40M rows (10일치)**
* Fields: `click`, `hour`, `device_id`, `site_domain`, `app_id`, … (약 20+ 컬럼)

---

## **3. 시스템 구성 요구사항**

## **3.1 Ingestion Layer**

* Python Kafka Producer는 row 단위로 JSON 이벤트 생성하여 Kafka topic에 발행한다.
* 레코드 검증 실패 시 **DLQ Topic(ad_events_error)**로 전송한다.
* Schema Registry를 사용해 JSON schema를 관리한다.

---

## **3.2 Streaming Layer (Kafka)**

* 주요 Topic:

  * `ad_events_raw` (partition=3)
  * `ad_events_error` (DLQ)
* Kafka JMX Exporter 활성화 (메트릭: consumer lag, throughput, broker I/O)
* Kafka Connect(optional) 연결 가능 구조 유지

---

## **3.3 Realtime Compute Layer (Flink)**

* PyFlink Streaming Job 사용
* Event Time 기반 처리
* Watermark 적용
* Window Aggregation:

  * **1분 tumbling window**
  * **5분 tumbling window**
* 계산 메트릭:

  * CTR(clicks / impressions)
  * CPC(cost / clicks)
  * CPA(cost / conversions)
  * ROAS(revenue / cost)
* 처리 실패 시 DLQ로 전송
* Checkpoint/State Backend:

  * 로컬: `./data/checkpoints`
    *(향후 MinIO/S3로 확장 가능)*

---

## **3.4 Storage Layer**

### **PostgreSQL**

* Schema 구성:

  * `realtime` : 실시간 윈도우 집계 결과 저장
  * `analytics` : DW 및 Mart 테이블
  * `errors` : DLQ 영구 저장
* Constraint:

  * primary key 기반 upsert 지원
  * 시간 파티션 고려

### **File Storage (Batch)**

* 경로:

  * `./data/raw/`
  * `./data/processed/`
* Batch ETL에서 사용

---

## **3.5 Batch Layer**

### **Airflow (localhost:8080)**

DAGs:

1. `dag_daily_etl`

   * Raw → Processed 변환
   * 결측값/형식 검증

2. `dag_dbt_run`

   * dbt model run
   * dbt test 수행
   * Failed tests → Slack Alert

### **dbt**

* staging / mart 모델 구성
* 테스트:

  * not_null
  * unique
  * relationship
* Logical Layer:

  * daily_impressions
  * daily_clicks
  * campaign_performance

---

## **3.6 Analytics Layer**

### **Streamlit (localhost:8501)**

* 실시간 CTR 모니터링 대시보드
* PostgreSQL realtime schema에서 pull

### **Metabase (localhost:3000)**

* DW 기반 리포트 생성
* 광고 성과 분석(CTR/CPA/ROAS 등)

---

## **3.7 Monitoring & Alerting**

### **Prometheus**

* Kafka JMX Exporter 수집
* Flink metrics 수집
* Airflow API metrics 수집(optional)

### **Grafana**

* Consumer lag dashboard
* Flink job throughput
* PG QPS trends

### **Slack Alerts**

* DLQ 재시도 실패
* Airflow DAG 실패
* dbt test 실패

---

## **4. DLQ Requirements**

DLQ 이벤트는 다음 데이터를 반드시 포함한다:

* raw_payload
* error_type (parsing, schema, flink_logic)
* retry_count
* error_timestamp
* stacktrace(optional)

재시도 정책:

* 최대 3회 재시도 → 실패 시 PostgreSQL `errors` 테이블에 저장
* Slack 알림 발송

---

## **5. 운영 요구사항**

### **5.1 로컬 개발**

* 모든 시스템은 Docker Compose 기반으로 실행 가능해야 한다.
* 구성 요소:

  * Kafka, Zookeeper
  * Schema Registry
  * Prometheus, Grafana
  * PostgreSQL
  * Airflow
  * Streamlit
  * Metabase

### **5.2 확장성**

* partition 수 증가 시 Flink 병렬 처리 자동 확장
* PostgreSQL → Cloud warehouse(BigQuery/Snowflake/Athena)로 확장 고려

### **5.3 신뢰성**

* Exactly-once 가능하도록 Flink 체크포인트 안정적인 backend 필요
* Airflow task-level retry 적용
* Monitoring & Alerting 필수

---

## **6. 주요 KPI**

* 실시간 처리 지연: < 5초
* Kafka ingestion TPS: 5k/s+
* Flink window latency: < 2s
* Daily batch 처리 소요: < 10분
* DLQ 발생률: < 0.1%

---

## **7. 산출물**

* 전체 아키텍처 Flowchart (Mermaid)
* Docker Compose 파일
* PyFlink streaming job
* Airflow DAG 2종
* dbt project
* Streamlit dashboard
* Metabase dashboards
* requirements.md(본 문서)

