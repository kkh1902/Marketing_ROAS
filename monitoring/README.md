# Monitoring System

이 디렉토리는 **Marketing ROAS Data Pipeline**을 운영하기 위한
모니터링 스택(Prometheus, Grafana, Kafka Exporter, JMX Exporter)을 포함합니다.

이 구성으로 **Kafka → Flink → Database** 전체 파이프라인의 상태와 성능을
실시간으로 모니터링할 수 있습니다.

---

## 📦 Folder Structure

```

monitoring/
├── grafana/
│    ├── dashboards/
│    │    ├── kafka-overview.json
│    │    ├── flink-overview.json
│    │    └── jvm-metrics.json
│    └── provisioning/
│         ├── dashboards.yaml
│         └── datasources.yaml
│
├── prometheus/
│    ├── prometheus.yml
│    └── alerts.yml   (optional)
│
├── exporters/
│    ├── kafka-exporter.yml
│    ├── jmx-kafka.yaml
│    ├── jmx-zookeeper.yaml
│    ├── jmx-schema-registry.yaml
│    ├── jmx-flink-jobmanager.yaml
│    └── jmx-flink-taskmanager.yaml
│
├── docker-compose.monitoring.yml

````

---

# 🔧 Components

## 1. Kafka Exporter
Kafka Exporter는 Kafka의 **토픽, 파티션, consumer group lag**을 Prometheus로 보내는 Exporter입니다.

주요 수집 메트릭:
- Consumer group lag
- Under-replicated partitions
- Message in/out rate
- Topic throughput

필요한 이유:
- Consumer lag 증가나 Kafka 병목을 빠르게 파악할 수 있음

---

## 2. JMX Exporter
Kafka / Zookeeper / Schema Registry / Flink(JM/TM) 같은 JVM 기반 시스템의
내부 상태(JVM 메트릭, GC, Thread)를 Prometheus로 전달합니다.

주요 메트릭:
- Heap / Non-heap memory
- GC pause time
- CPU usage
- Thread count

필요한 이유:
- Kafka/Flink 장애 원인의 절반은 JVM 메모리/GC 문제이기 때문

---

## 3. Prometheus
Prometheus는 Exporter들에서 메트릭을 **scraping**하여 시계열 데이터로 저장합니다.

Scrape 대상:
- kafka-exporter
- jmx-kafka / jmx-zookeeper
- jmx-schema-registry
- jmx-flink-jobmanager / jmx-flink-taskmanager

---

## 4. Grafana
Grafana는 Prometheus 데이터를 활용해 대시보드를 시각화합니다.

이 프로젝트에는 기본적으로 다음 대시보드가 포함됩니다:
- Kafka Overview
- Flink Overview
- JVM Metrics

Grafana provisioning 기능으로 자동 로드됩니다.

---

# 🚀 Running Monitoring Stack

모니터링 스택 실행:

```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
````

접속 주소:

| Component                          | URL                                            |
| ---------------------------------- | ---------------------------------------------- |
| **Prometheus**                     | [http://localhost:9090](http://localhost:9090) |
| **Grafana**                        | [http://localhost:3000](http://localhost:3000) |
| **Flink Dashboard (Main Compose)** | [http://localhost:8081](http://localhost:8081) |

Grafana 기본 로그인:

```
ID: admin
PW: admin
```

---

# 📊 Available Dashboards

### ✔ Kafka Overview Dashboard

* Topic throughput
* Consumer lag
* Under-replicated partitions
* Broker request rate

### ✔ Flink Overview Dashboard

* Checkpoint duration/size
* Backpressure %
* Watermark lag
* Records in/out
* TaskManager load

### ✔ JVM Metrics Dashboard

* Heap memory usage
* GC pause
* CPU load
* Thread count

---

# 🧪 Health Checks

### Kafka 정상 상태 조건

* `under_replicated_partitions == 0`
* Consumer lag가 일정값 이하 유지
* Broker request timeout 없음

### Flink 정상 상태 조건

* Checkpoints regularly completed
* Backpressure < 80%
* Watermarks 정상 증가
* TM CPU/Heap 안정적

---

# 📌 Summary

이 모니터링 구성은 다음을 목표로 합니다:

* Kafka → Flink 전체 파이프라인 상태 실시간 모니터링
* Consumer lag 및 backpressure 이상 탐지
* JVM 기반 시스템의 성능/안정성 측정
* 운영 환경에서 빠른 장애 원인 파악 가능

Kafka + Flink 기반 파이프라인에서 필요한 모든 메트릭 수집이 가능합니다.
