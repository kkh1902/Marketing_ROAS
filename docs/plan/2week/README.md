# Week 2: 실시간 처리 & 캐싱

**목표:** PyFlink로 실시간 스트리밍 처리를 구현하고, Redis 캐시와 PostgreSQL을 연동합니다.

**기간:** 5일 (월~금)
**일일 분량:** 2시간
**총 시간:** 10시간

---

## 📅 주간 일정표

| 단계 | 주제 | 시간 | 누적 |
|------|------|------|------|
| **월** | PyFlink 개발환경 구축 | 2h | 2h |
| **화** | PyFlink 스트리밍 작업 (1/3) | 2h | 4h |
| **수** | PyFlink 스트리밍 작업 (2/3) | 2h | 6h |
| **목** | Redis + PostgreSQL 구축 | 2h | 8h |
| **금** | Streamlit 대시보드 + 통합 테스트 | 2h | 10h |

---

## 📌 Day 1 (월): PyFlink 개발환경 구축 (2시간)

### 목표
- PyFlink 로컬 환경 설정
- Flink Job/Task Manager Docker 구성
- Kafka 소스 연동 테스트
- 기본 파이프라인 검증

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| PyFlink 설치 및 설정 | 40분 |
| Docker 구성 | 40분 |
| Kafka 연동 테스트 | 30분 |
| 문서화 | 10분 |

### 🛠️ 실습 내용

#### 1-1. PyFlink 설치 및 의존성 (20분)

**파일:** `requirements.txt` (업데이트)

```
# 기존 의존성...

# PyFlink (Week 2)
apache-flink==1.18.1
pyflink==1.18.1

# PyFlink 추가 의존성
avro-python3==1.11.0

# Real-time processing
redis==5.0.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# Streamlit (Week 2)
streamlit==1.28.1
plotly==5.17.0
pandas==2.1.3

# Monitoring
prometheus-client==0.19.0
```

**설치:**
```bash
pip install -r requirements.txt
```

#### 1-2. Flink 설정 파일 작성 (20분)

**파일:** `src/flink/config.py`

```python
"""
PyFlink 설정 파일
"""

import os
from dotenv import load_dotenv

load_dotenv()

class FlinkConfig:
    """Flink 설정"""

    # Flink 클러스터 설정
    JOB_MANAGER_RPC_ADDRESS = os.getenv('FLINK_JOBMANAGER_RPC_ADDRESS', 'localhost')
    JOB_MANAGER_RPC_PORT = int(os.getenv('FLINK_JOBMANAGER_RPC_PORT', 6123))
    TASK_MANAGER_RPC_PORT = int(os.getenv('FLINK_TASKMANAGER_RPC_PORT', 6124))

    # 병렬화 설정
    PARALLELISM = 4  # 4개 task manager slot
    CHECKPOINT_INTERVAL = 60000  # 60초
    CHECKPOINT_TIMEOUT = 600000  # 10분

    # Kafka 설정
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC = 'ad_events_raw'
    KAFKA_ERROR_TOPIC = 'ad_events_error'

    # Schema Registry
    SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL', 'http://localhost:8081')
    SCHEMA_SUBJECT = 'ad_events_raw-value'

    # 상태 저장소 (State Backend)
    CHECKPOINT_DIR = './data/checkpoints'
    STATE_BACKEND = 'rocksdb'  # or 'filesystem'

    # 윈도우 설정
    WINDOW_1MIN = 60  # 1분 (초)
    WINDOW_5MIN = 300  # 5분 (초)
    ALLOWED_LATENESS = 10  # 10초 지각 허용

    # 메모리 설정
    JVM_MEMORY = '1024m'
    TASK_MEMORY = '512m'

    @classmethod
    def get_env_variables(cls):
        """Flink 환경 변수 딕셔너리"""
        return {
            'jobmanager.rpc.address': cls.JOB_MANAGER_RPC_ADDRESS,
            'jobmanager.rpc.port': cls.JOB_MANAGER_RPC_PORT,
            'taskmanager.rpc.port': cls.TASK_MANAGER_RPC_PORT,
            'parallelism.default': cls.PARALLELISM,
            'state.checkpoints.dir': f'file://{cls.CHECKPOINT_DIR}',
            'state.backend': cls.STATE_BACKEND,
            'execution.checkpointing.interval': cls.CHECKPOINT_INTERVAL,
            'execution.checkpointing.timeout': cls.CHECKPOINT_TIMEOUT,
        }

    @classmethod
    def validate(cls):
        """설정 검증"""
        os.makedirs(cls.CHECKPOINT_DIR, exist_ok=True)
        print(f"✅ Flink config validated")
        print(f"   Parallelism: {cls.PARALLELISM}")
        print(f"   Checkpoint Dir: {cls.CHECKPOINT_DIR}")
```

#### 1-3. Docker Compose 업데이트 (30분)

**파일:** `docker-compose.yml` (Flink 서비스 추가)

```yaml
  # Flink JobManager
  flink-jobmanager:
    image: flink:1.18.1-scala_2.12
    container_name: flink-jobmanager
    command: jobmanager
    ports:
      - "6123:6123"
      - "8081:8081"  # Web UI
    environment:
      - JOB_MANAGER_RPC_ADDRESS=flink-jobmanager
      - FLINK_PROPERTIES=jobmanager.rpc.address:flink-jobmanager
    volumes:
      - ./data/checkpoints:/flink/checkpoints
      - ./src/flink:/flink/jobs
    networks:
      - kafka-network
    healthcheck:
      test: curl -f http://localhost:8081/overview || exit 1
      interval: 10s
      timeout: 5s
      retries: 5

  # Flink TaskManager (최소 2개)
  flink-taskmanager-1:
    image: flink:1.18.1-scala_2.12
    container_name: flink-taskmanager-1
    command: taskmanager
    depends_on:
      flink-jobmanager:
        condition: service_healthy
    ports:
      - "6124:6124"
      - "9081:8081"
    environment:
      - JOB_MANAGER_RPC_ADDRESS=flink-jobmanager
      - FLINK_PROPERTIES=jobmanager.rpc.address:flink-jobmanager
        taskmanager.rpc.port:6124
    volumes:
      - ./data/checkpoints:/flink/checkpoints
      - ./src/flink:/flink/jobs
    networks:
      - kafka-network

  flink-taskmanager-2:
    image: flink:1.18.1-scala_2.12
    container_name: flink-taskmanager-2
    command: taskmanager
    depends_on:
      flink-jobmanager:
        condition: service_healthy
    ports:
      - "6125:6124"
      - "9082:8081"
    environment:
      - JOB_MANAGER_RPC_ADDRESS=flink-jobmanager
      - FLINK_PROPERTIES=jobmanager.rpc.address:flink-jobmanager
        taskmanager.rpc.port:6124
    volumes:
      - ./data/checkpoints:/flink/checkpoints
      - ./src/flink:/flink/jobs
    networks:
      - kafka-network
```

**실행:**
```bash
docker-compose up -d flink-jobmanager flink-taskmanager-1 flink-taskmanager-2

# Flink Web UI 접속
# http://localhost:8081

# 로그 확인
docker-compose logs -f flink-jobmanager
docker-compose logs -f flink-taskmanager-1
```

#### 1-4. 기본 PyFlink 파이프라인 (30분)

**파일:** `src/flink/simple_pipeline.py`

```python
"""
기본 PyFlink 파이프라인 테스트
Kafka → Print Sink
"""

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaAdEventSource:
    """Kafka 소스 생성"""

    @staticmethod
    def create_kafka_source(bootstrap_servers='kafka:29092', topic='ad_events_raw'):
        """KafkaSource 생성"""
        kafka_source = KafkaSource.builder() \
            .set_bootstrap_servers(bootstrap_servers) \
            .set_topics(topic) \
            .set_group_id('flink-consumer-group') \
            .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
            .set_value_only_deserializer(SimpleStringSchema()) \
            .build()

        return kafka_source


def parse_event(json_str):
    """JSON 문자열을 파싱"""
    try:
        event = json.loads(json_str)
        return event
    except Exception as e:
        logger.error(f"Parse error: {e}")
        return None


def process_event(event):
    """이벤트 처리"""
    if event is None:
        return None

    # 필드 추출
    event_id = event.get('id', '')
    click = event.get('click', 0)
    hour = event.get('hour', 0)

    return {
        'id': event_id,
        'click': click,
        'hour': hour,
        'processed_at': int(__import__('time').time() * 1000)
    }


def main():
    """메인 파이프라인"""

    env = StreamExecutionEnvironment.get_execution_environment()

    # 병렬화 설정
    env.set_parallelism(2)

    # Checkpoint 설정
    env.enable_checkpointing(60000)  # 60초

    try:
        # Kafka 소스 생성
        logger.info("Creating Kafka source...")
        kafka_source = KafkaAdEventSource.create_kafka_source(
            bootstrap_servers='kafka:29092',
            topic='ad_events_raw'
        )

        # 데이터 스트림 생성
        data_stream = env.add_source(kafka_source)

        # 이벤트 파싱 및 처리
        processed_stream = data_stream \
            .map(lambda x: parse_event(x), output_type=Types.MAP(Types.STRING, Types.OBJECT)) \
            .filter(lambda x: x is not None) \
            .map(lambda x: process_event(x), output_type=Types.MAP(Types.STRING, Types.OBJECT))

        # 콘솔 출력 (디버깅용)
        processed_stream.print()

        # 파이프라인 실행
        logger.info("Starting Flink pipeline...")
        env.execute("Simple Kafka Pipeline")

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise


if __name__ == "__main__":
    main()
```

**실행:**
```bash
cd src/flink
python simple_pipeline.py
```

#### 1-5. 연동 테스트 (20분)

**파일:** `scripts/test_flink_kafka.sh`

```bash
#!/bin/bash

echo "================================"
echo "Flink + Kafka 연동 테스트"
echo "================================"

# 1️⃣  Flink 상태 확인
echo ""
echo "1️⃣  Flink 서비스 상태..."
docker-compose ps | grep flink

# 2️⃣  Kafka 토픽 확인
echo ""
echo "2️⃣  Kafka 토픽 확인..."
docker-compose exec kafka kafka-topics \
    --list \
    --bootstrap-server kafka:29092

# 3️⃣  Flink Web UI 접근성 확인
echo ""
echo "3️⃣  Flink Web UI 접근성 확인..."
curl -s http://localhost:8081/overview | jq '.["taskmanagers"]' || echo "Flink UI 준비 중..."

# 4️⃣  메시지 발행 (테스트용)
echo ""
echo "4️⃣  테스트 메시지 발행..."
python src/kafka/producer.py 100

# 5️⃣  토픽 메시지 확인
echo ""
echo "5️⃣  토픽 메시지 확인..."
docker-compose exec kafka kafka-console-consumer \
    --bootstrap-server kafka:29092 \
    --topic ad_events_raw \
    --from-beginning \
    --max-messages 1 \
    --timeout-ms 5000 2>/dev/null || echo "메시지 대기 중..."

echo ""
echo "✅ 테스트 완료"
```

**실행:**
```bash
chmod +x scripts/test_flink_kafka.sh
bash scripts/test_flink_kafka.sh
```

### ✅ 완료 기준

- [ ] PyFlink 설치 완료
- [ ] Flink 환경 설정 파일 작성
- [ ] docker-compose.yml에 Flink 서비스 추가
- [ ] 모든 Flink 컨테이너 정상 실행
- [ ] Flink Web UI (http://localhost:8081) 접근 가능
- [ ] Kafka → Flink 기본 파이프라인 실행 성공

### 📊 산출물

```
src/flink/
├── config.py (Flink 설정)
└── simple_pipeline.py (기본 파이프라인)

docker-compose.yml (Flink 서비스 추가)

scripts/
└── test_flink_kafka.sh (테스트 스크립트)
```

---

## 📌 Day 2-3 (화-수): PyFlink 스트리밍 작업 구현 (4시간)

### 목표
- KafkaSource 완전 구현 (Schema Registry 연동)
- Event Time 및 Watermark 설정
- Tumbling Window (1분, 5분) 구현
- CTR 계산 로직 구현
- State Management 및 Checkpoint

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| KafkaSource + 스키마 | 50분 |
| Window 및 집계 | 60분 |
| State 관리 | 50분 |
| 통합 테스트 | 40분 |

### 🛠️ 실습 내용

#### 2-1. KafkaSource with Schema Registry (30분)

**파일:** `src/flink/kafka_source.py`

```python
"""
Schema Registry와 연동하는 KafkaSource
"""

import json
import logging
from typing import Dict, Any
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.schema_registry.avro import AvroDeserializer
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.common.serialization import DeserializationSchema
from pyflink.common.typeinfo import Types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AvroDeserializationSchema(DeserializationSchema):
    """Avro 역직렬화 스키마"""

    def __init__(self, schema_registry_url: str, subject: str):
        self.schema_registry_url = schema_registry_url
        self.subject = subject
        self.deserializer = None
        self._init_deserializer()

    def _init_deserializer(self):
        """Avro 역직렬화기 초기화"""
        try:
            sr_client = SchemaRegistryClient({'url': self.schema_registry_url})
            schema = sr_client.get_latest_version(self.subject)
            self.deserializer = AvroDeserializer(sr_client, schema.schema)
            logger.info(f"✅ Avro deserializer initialized for {self.subject}")
        except Exception as e:
            logger.error(f"Failed to init deserializer: {e}")
            raise

    def deserialize(self, message: bytes) -> Dict[str, Any]:
        """바이트를 딕셔너리로 역직렬화"""
        try:
            return self.deserializer(message, ctx=None)
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            return None

    def is_end_of_stream(self, next_element: Dict) -> bool:
        return next_element is None

    def get_produced_type(self):
        return Types.MAP(Types.STRING, Types.OBJECT)


class AdEventKafkaSource:
    """광고 이벤트 Kafka 소스"""

    @staticmethod
    def create_source(
        bootstrap_servers: str = 'kafka:29092',
        topic: str = 'ad_events_raw',
        schema_registry_url: str = 'http://schema-registry:8081',
        group_id: str = 'flink-ad-events'
    ):
        """
        Kafka 소스 생성

        Args:
            bootstrap_servers: Kafka 부트스트랩 서버
            topic: 토픽명
            schema_registry_url: Schema Registry URL
            group_id: 컨슈머 그룹

        Returns:
            KafkaSource
        """

        # Avro 역직렬화 스키마
        avro_schema = AvroDeserializationSchema(
            schema_registry_url=schema_registry_url,
            subject=f'{topic}-value'
        )

        # KafkaSource 빌더
        kafka_source = KafkaSource.builder() \
            .set_bootstrap_servers(bootstrap_servers) \
            .set_topics(topic) \
            .set_group_id(group_id) \
            .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
            .set_value_only_deserializer(avro_schema) \
            .set_property('isolation.level', 'read_committed') \
            .build()

        logger.info(f"✅ KafkaSource created: {topic}")
        return kafka_source


if __name__ == "__main__":
    # 테스트
    source = AdEventKafkaSource.create_source()
    print("✅ Source created successfully")
```

#### 2-2. 집계 함수 및 Window (40분)

**파일:** `src/flink/aggregations.py`

```python
"""
실시간 집계 함수 및 Window 연산
"""

import logging
from typing import Dict, Any, Tuple
from datetime import datetime
from pyflink.datastream.window import TumblingEventTimeWindow
from pyflink.common.time import Time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdEventAggregator:
    """광고 이벤트 집계기"""

    @staticmethod
    def extract_timestamp(event: Dict[str, Any]) -> int:
        """이벤트에서 타임스탐프 추출"""
        try:
            # event['timestamp']는 밀리초 단위
            return int(event.get('timestamp', 0))
        except Exception as e:
            logger.error(f"Timestamp extraction error: {e}")
            return 0

    @staticmethod
    def create_window_key(event: Dict[str, Any]) -> str:
        """윈도우 키 생성 (파티셔닝용)"""
        # 예: hour별, device_type별로 분할
        hour = event.get('hour', 'unknown')
        device_type = event.get('device_type', 'unknown')
        return f"{hour}_{device_type}"

    @staticmethod
    def aggregate_1min(
        events: list,
        window_start: int,
        window_end: int
    ) -> Dict[str, Any]:
        """1분 단위 집계"""

        if not events:
            return None

        total_events = len(events)
        clicks = sum(1 for e in events if e.get('click', 0) == 1)
        impressions = total_events
        ctr = (clicks / impressions * 100) if impressions > 0 else 0

        # 카테고리별 CTR
        category_ctr = {}
        for event in events:
            cat = event.get('site_category', 'unknown')
            if cat not in category_ctr:
                category_ctr[cat] = {'clicks': 0, 'impressions': 0}
            category_ctr[cat]['impressions'] += 1
            if event.get('click') == 1:
                category_ctr[cat]['clicks'] += 1

        result = {
            'window_start': window_start,
            'window_end': window_end,
            'window_type': '1min',
            'total_impressions': impressions,
            'total_clicks': clicks,
            'ctr': round(ctr, 2),
            'category_ctr': {
                cat: round(
                    v['clicks'] / v['impressions'] * 100, 2
                ) for cat, v in category_ctr.items()
            },
            'timestamp': int(__import__('time').time() * 1000)
        }

        logger.info(f"1min aggregation: {impressions} events, CTR={ctr:.2f}%")
        return result

    @staticmethod
    def aggregate_5min(
        events: list,
        window_start: int,
        window_end: int
    ) -> Dict[str, Any]:
        """5분 단위 집계"""

        if not events:
            return None

        total_events = len(events)
        clicks = sum(1 for e in events if e.get('click', 0) == 1)
        impressions = total_events
        ctr = (clicks / impressions * 100) if impressions > 0 else 0

        # 디바이스 타입별 CTR
        device_ctr = {}
        for event in events:
            dev = event.get('device_type', 'unknown')
            if dev not in device_ctr:
                device_ctr[dev] = {'clicks': 0, 'impressions': 0}
            device_ctr[dev]['impressions'] += 1
            if event.get('click') == 1:
                device_ctr[dev]['clicks'] += 1

        result = {
            'window_start': window_start,
            'window_end': window_end,
            'window_type': '5min',
            'total_impressions': impressions,
            'total_clicks': clicks,
            'ctr': round(ctr, 2),
            'device_ctr': {
                dev: round(
                    v['clicks'] / v['impressions'] * 100, 2
                ) for dev, v in device_ctr.items()
            },
            'timestamp': int(__import__('time').time() * 1000)
        }

        logger.info(f"5min aggregation: {impressions} events, CTR={ctr:.2f}%")
        return result


class WindowConfig:
    """Window 설정"""

    # Window 크기
    WINDOW_1MIN = Time.milliseconds(60 * 1000)  # 1분
    WINDOW_5MIN = Time.milliseconds(5 * 60 * 1000)  # 5분

    # Watermark 설정
    WATERMARK_ALLOWED_LATENESS = Time.seconds(10)  # 10초 지각 허용

    @staticmethod
    def get_1min_window():
        """1분 Window 생성"""
        return TumblingEventTimeWindow(WindowConfig.WINDOW_1MIN)

    @staticmethod
    def get_5min_window():
        """5분 Window 생성"""
        return TumblingEventTimeWindow(WindowConfig.WINDOW_5MIN)
```

#### 2-3. 완전한 스트리밍 작업 (60분)

**파일:** `src/flink/streaming_job.py`

```python
"""
완전한 PyFlink 스트리밍 작업
Kafka → 1min/5min Window → Redis/PostgreSQL
"""

import logging
import json
import time
from typing import Dict, Any

from pyflink.datastream import StreamExecutionEnvironment, DataStream
from pyflink.datastream.window import TumblingEventTimeWindow
from pyflink.datastream.functions import WindowFunction, AggregateFunction
from pyflink.common.time import Time
from pyflink.common.typeinfo import Types

from kafka_source import AdEventKafkaSource
from aggregations import AdEventAggregator, WindowConfig
from config import FlinkConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdEventWindowFunction(WindowFunction):
    """Window 함수"""

    def __init__(self, window_size: int):
        self.window_size = window_size
        self.aggregator = AdEventAggregator()

    def apply(self, key, window, inputs):
        """Window 함수 실행"""
        events = list(inputs)
        window_start = window.start
        window_end = window.end

        if self.window_size == 60:
            # 1분 window
            result = self.aggregator.aggregate_1min(
                events, window_start, window_end
            )
        else:
            # 5분 window
            result = self.aggregator.aggregate_5min(
                events, window_start, window_end
            )

        if result:
            yield result


class SimpleAggregator(AggregateFunction):
    """간단한 집계 함수"""

    def create_accumulator(self):
        """누적기 생성"""
        return {
            'count': 0,
            'clicks': 0,
            'total_click': 0
        }

    def add(self, value, accumulator):
        """값 추가"""
        accumulator['count'] += 1
        if value.get('click') == 1:
            accumulator['clicks'] += 1
            accumulator['total_click'] += 1
        return accumulator

    def get_result(self, accumulator):
        """결과 반환"""
        ctr = (
            accumulator['clicks'] / accumulator['count'] * 100
            if accumulator['count'] > 0 else 0
        )
        return {
            'total': accumulator['count'],
            'clicks': accumulator['clicks'],
            'ctr': round(ctr, 2),
            'timestamp': int(time.time() * 1000)
        }

    def merge(self, a, b):
        """누적기 병합"""
        a['count'] += b['count']
        a['clicks'] += b['clicks']
        return a


class PrintSink:
    """콘솔 출력 Sink (디버깅)"""

    @staticmethod
    def print_result(data: Dict[str, Any]):
        """결과 출력"""
        logger.info(f"Window Result: {json.dumps(data, indent=2)}")
        return data


def create_streaming_job(env: StreamExecutionEnvironment):
    """스트리밍 작업 생성"""

    logger.info("=" * 60)
    logger.info("Starting Flink Streaming Job")
    logger.info("=" * 60)

    # 1️⃣  Kafka 소스 생성
    logger.info("Creating Kafka source...")
    kafka_source = AdEventKafkaSource.create_source(
        bootstrap_servers=FlinkConfig.KAFKA_BOOTSTRAP_SERVERS,
        topic=FlinkConfig.KAFKA_TOPIC,
        schema_registry_url=FlinkConfig.SCHEMA_REGISTRY_URL
    )

    # 2️⃣  데이터 스트림 생성
    data_stream = env.add_source(kafka_source)

    # 3️⃣  Timestamp 및 Watermark 설정
    logger.info("Setting watermark strategy...")
    data_stream = data_stream.assign_timestamps_and_watermarks(
        WatermarkStrategy.for_bounded_out_of_orderness(
            Time.seconds(FlinkConfig.ALLOWED_LATENESS)
        ).with_timestamp_selector(
            lambda event: AdEventAggregator.extract_timestamp(event)
        )
    )

    # 4️⃣  1분 Window 적용
    logger.info("Creating 1-minute window aggregation...")
    window_1min = data_stream \
        .key_by(lambda e: AdEventAggregator.create_window_key(e)) \
        .window(TumblingEventTimeWindow(Time.milliseconds(60 * 1000))) \
        .apply(AdEventWindowFunction(window_size=60))

    # 5️⃣  5분 Window 적용
    logger.info("Creating 5-minute window aggregation...")
    window_5min = data_stream \
        .key_by(lambda e: AdEventAggregator.create_window_key(e)) \
        .window(TumblingEventTimeWindow(Time.milliseconds(5 * 60 * 1000))) \
        .apply(AdEventWindowFunction(window_size=300))

    # 6️⃣  디버깅 출력
    window_1min.map(PrintSink.print_result).print()
    window_5min.map(PrintSink.print_result).print()

    return window_1min, window_5min


def main():
    """메인 함수"""

    # Flink 환경 설정 검증
    FlinkConfig.validate()

    # Flink 환경 생성
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(FlinkConfig.PARALLELISM)

    # Checkpoint 활성화
    env.enable_checkpointing(FlinkConfig.CHECKPOINT_INTERVAL)
    env.get_checkpoint_config().set_checkpointing_timeout(
        FlinkConfig.CHECKPOINT_TIMEOUT
    )

    try:
        # 스트리밍 작업 생성
        window_1min, window_5min = create_streaming_job(env)

        # 파이프라인 실행
        logger.info("Starting job execution...")
        env.execute("Ad Event Streaming Job")

    except Exception as e:
        logger.error(f"Job execution failed: {e}")
        raise
    finally:
        logger.info("Job completed")


if __name__ == "__main__":
    main()
```

**실행:**
```bash
cd src/flink
python streaming_job.py
```

### ✅ 완료 기준

- [ ] KafkaSource with Schema Registry 구현
- [ ] Timestamp 및 Watermark 설정 완료
- [ ] 1분 Window 집계 작동
- [ ] 5분 Window 집계 작동
- [ ] CTR 계산 정확도 검증
- [ ] Checkpoint 저장 확인
- [ ] 콘솔 로그에서 결과 출력 확인

### 📊 산출물

```
src/flink/
├── kafka_source.py (Schema Registry 연동)
├── aggregations.py (집계 함수)
└── streaming_job.py (메인 스트리밍 작업)

data/
└── checkpoints/ (Checkpoint 파일)
```

---

## 📌 Day 4 (목): Redis + PostgreSQL 구축 (2시간)

### 목표
- Redis Docker 설정 및 캐시 구조 설계
- PostgreSQL 스키마 생성
- Flink → Redis/PostgreSQL Sink 구현
- 데이터 연결성 테스트

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| Redis 캐시 설계 및 구현 | 40분 |
| PostgreSQL 스키마 | 40분 |
| Sink 구현 | 30분 |
| 통합 테스트 | 10분 |

### 🛠️ 실습 내용

#### 4-1. Redis 캐시 관리자 (25분)

**파일:** `src/redis/cache_manager.py`

```python
"""
Redis 캐시 관리자
"""

import redis
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisCacheManager:
    """Redis 캐시 관리"""

    def __init__(
        self,
        host: str = 'redis',
        port: int = 6379,
        db: int = 0,
        ttl_minutes: int = 5
    ):
        """
        초기화

        Args:
            host: Redis 호스트
            port: Redis 포트
            db: 데이터베이스 번호
            ttl_minutes: TTL (분)
        """
        self.host = host
        self.port = port
        self.db = db
        self.ttl = ttl_minutes * 60  # 초 단위

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_keepalive=True
            )
            # 연결 테스트
            self.client.ping()
            logger.info(f"✅ Connected to Redis {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def set_1min_metrics(self, window_id: str, metrics: Dict[str, Any]):
        """1분 메트릭 저장"""
        key = f"metrics:1min:{window_id}"
        try:
            self.client.setex(
                key,
                self.ttl,
                json.dumps(metrics)
            )
            logger.info(f"Cached 1min metrics: {key}")
        except Exception as e:
            logger.error(f"Failed to cache: {e}")

    def set_5min_metrics(self, window_id: str, metrics: Dict[str, Any]):
        """5분 메트릭 저장"""
        key = f"metrics:5min:{window_id}"
        try:
            self.client.setex(
                key,
                self.ttl * 5,  # 25분 TTL
                json.dumps(metrics)
            )
            logger.info(f"Cached 5min metrics: {key}")
        except Exception as e:
            logger.error(f"Failed to cache: {e}")

    def get_1min_metrics(self, window_id: str) -> Optional[Dict]:
        """1분 메트릭 조회"""
        key = f"metrics:1min:{window_id}"
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get metric: {e}")
            return None

    def get_all_current_metrics(self) -> Dict[str, Any]:
        """현재 모든 메트릭 조회"""
        try:
            keys_1min = self.client.keys("metrics:1min:*")
            keys_5min = self.client.keys("metrics:5min:*")

            result = {
                '1min': {},
                '5min': {},
                'timestamp': datetime.now().isoformat()
            }

            for key in keys_1min:
                data = self.client.get(key)
                if data:
                    result['1min'][key] = json.loads(data)

            for key in keys_5min:
                data = self.client.get(key)
                if data:
                    result['5min'][key] = json.loads(data)

            return result
        except Exception as e:
            logger.error(f"Failed to get all metrics: {e}")
            return {}

    def health_check(self) -> bool:
        """상태 확인"""
        try:
            self.client.ping()
            info = self.client.info()
            logger.info(
                f"Redis health: "
                f"used_memory={info.get('used_memory_human', 'N/A')}, "
                f"connected_clients={info.get('connected_clients', 'N/A')}"
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def flush_all(self):
        """모든 데이터 삭제 (테스트용)"""
        try:
            self.client.flushdb()
            logger.info("Redis database flushed")
        except Exception as e:
            logger.error(f"Flush failed: {e}")


if __name__ == "__main__":
    # 테스트
    cache = RedisCacheManager()

    # 메트릭 저장
    metrics_1min = {
        'window_id': 'test_1',
        'ctr': 16.5,
        'impressions': 1000,
        'clicks': 165
    }
    cache.set_1min_metrics('test_1', metrics_1min)

    # 메트릭 조회
    result = cache.get_1min_metrics('test_1')
    print(f"Retrieved: {result}")

    # 상태 확인
    cache.health_check()
```

#### 4-2. PostgreSQL 스키마 (25분)

**파일:** `src/postgres/schema.sql`

```sql
-- realtime 스키마 생성
CREATE SCHEMA IF NOT EXISTS realtime;

-- 1분 집계 테이블
CREATE TABLE realtime.metrics_1min (
    id SERIAL PRIMARY KEY,
    window_start BIGINT NOT NULL,
    window_end BIGINT NOT NULL,
    total_impressions INTEGER NOT NULL,
    total_clicks INTEGER NOT NULL,
    ctr NUMERIC(5, 2) NOT NULL,
    category_ctr JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_window_time (window_start, window_end)
);

-- 5분 집계 테이블
CREATE TABLE realtime.metrics_5min (
    id SERIAL PRIMARY KEY,
    window_start BIGINT NOT NULL,
    window_end BIGINT NOT NULL,
    total_impressions INTEGER NOT NULL,
    total_clicks INTEGER NOT NULL,
    ctr NUMERIC(5, 2) NOT NULL,
    device_ctr JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_window_time (window_start, window_end)
);

-- 원본 이벤트 테이블
CREATE TABLE realtime.raw_events (
    id VARCHAR(255) PRIMARY KEY,
    click INTEGER,
    hour INTEGER,
    C1 INTEGER,
    banner_pos INTEGER,
    site_id VARCHAR(255),
    site_category VARCHAR(255),
    device_type INTEGER,
    device_ip VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_hour (hour),
    INDEX idx_device_type (device_type)
);

-- 성능 최적화 인덱스
CREATE INDEX idx_metrics_1min_ctr ON realtime.metrics_1min(ctr DESC);
CREATE INDEX idx_metrics_5min_ctr ON realtime.metrics_5min(ctr DESC);
CREATE INDEX idx_events_created ON realtime.raw_events(created_at DESC);
```

#### 4-3. PostgreSQL 연결 관리자 (25분)

**파일:** `src/postgres/db_connector.py`

```python
"""
PostgreSQL 데이터베이스 연결 및 쓰기
"""

import logging
import json
from typing import Dict, Any
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class Metrics1Min(Base):
    """1분 메트릭 모델"""
    __tablename__ = 'metrics_1min'
    __table_args__ = {'schema': 'realtime'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    window_start = Column(BIGINT, nullable=False, index=True)
    window_end = Column(BIGINT, nullable=False, index=True)
    total_impressions = Column(Integer, nullable=False)
    total_clicks = Column(Integer, nullable=False)
    ctr = Column(Float, nullable=False, index=True)
    category_ctr = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Metrics5Min(Base):
    """5분 메트릭 모델"""
    __tablename__ = 'metrics_5min'
    __table_args__ = {'schema': 'realtime'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    window_start = Column(BIGINT, nullable=False, index=True)
    window_end = Column(BIGINT, nullable=False, index=True)
    total_impressions = Column(Integer, nullable=False)
    total_clicks = Column(Integer, nullable=False)
    ctr = Column(Float, nullable=False, index=True)
    device_ctr = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class RawEvent(Base):
    """원본 이벤트 모델"""
    __tablename__ = 'raw_events'
    __table_args__ = {'schema': 'realtime'}

    id = Column(String(255), primary_key=True)
    click = Column(Integer)
    hour = Column(Integer, index=True)
    c1 = Column(Integer)
    banner_pos = Column(Integer)
    site_id = Column(String(255))
    site_category = Column(String(255))
    device_type = Column(Integer, index=True)
    device_ip = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PostgreSQLConnector:
    """PostgreSQL 커넥터"""

    def __init__(
        self,
        host: str = 'postgres',
        port: int = 5432,
        database: str = 'marketing_roas',
        user: str = 'postgres',
        password: str = 'postgres'
    ):
        """초기화"""
        self.connection_string = (
            f'postgresql://{user}:{password}@{host}:{port}/{database}'
        )

        try:
            self.engine = create_engine(self.connection_string, echo=False)
            self.SessionLocal = sessionmaker(bind=self.engine)

            # 테이블 생성
            Base.metadata.create_all(self.engine)
            logger.info(f"✅ Connected to PostgreSQL {host}:{port}/{database}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    def insert_1min_metrics(self, metrics: Dict[str, Any]) -> bool:
        """1분 메트릭 저장"""
        session = self.SessionLocal()
        try:
            record = Metrics1Min(
                window_start=metrics['window_start'],
                window_end=metrics['window_end'],
                total_impressions=metrics['total_impressions'],
                total_clicks=metrics['total_clicks'],
                ctr=metrics['ctr'],
                category_ctr=json.dumps(metrics.get('category_ctr', {}))
            )
            session.add(record)
            session.commit()
            logger.info(f"Inserted 1min metrics")
            return True
        except Exception as e:
            logger.error(f"Insert error: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def insert_5min_metrics(self, metrics: Dict[str, Any]) -> bool:
        """5분 메트릭 저장"""
        session = self.SessionLocal()
        try:
            record = Metrics5Min(
                window_start=metrics['window_start'],
                window_end=metrics['window_end'],
                total_impressions=metrics['total_impressions'],
                total_clicks=metrics['total_clicks'],
                ctr=metrics['ctr'],
                device_ctr=json.dumps(metrics.get('device_ctr', {}))
            )
            session.add(record)
            session.commit()
            logger.info(f"Inserted 5min metrics")
            return True
        except Exception as e:
            logger.error(f"Insert error: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def insert_raw_event(self, event: Dict[str, Any]) -> bool:
        """원본 이벤트 저장"""
        session = self.SessionLocal()
        try:
            record = RawEvent(
                id=event['id'],
                click=event.get('click'),
                hour=event.get('hour'),
                c1=event.get('C1'),
                banner_pos=event.get('banner_pos'),
                site_id=event.get('site_id'),
                site_category=event.get('site_category'),
                device_type=event.get('device_type'),
                device_ip=event.get('device_ip')
            )
            session.add(record)
            session.commit()
            return True
        except Exception as e:
            logger.debug(f"Insert error: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def health_check(self) -> bool:
        """상태 확인"""
        session = self.SessionLocal()
        try:
            session.execute('SELECT 1')
            logger.info("✅ PostgreSQL health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
        finally:
            session.close()


if __name__ == "__main__":
    # 테스트
    db = PostgreSQLConnector()

    # 메트릭 저장
    metrics_1min = {
        'window_start': int(__import__('time').time() * 1000),
        'window_end': int(__import__('time').time() * 1000) + 60000,
        'total_impressions': 1000,
        'total_clicks': 165,
        'ctr': 16.5,
        'category_ctr': {'news': 15.5, 'sports': 17.2}
    }
    db.insert_1min_metrics(metrics_1min)

    # 상태 확인
    db.health_check()
```

#### 4-4. PostgreSQL & Redis Docker 추가 (20분)

**파일:** `docker-compose.yml` (업데이트)

```yaml
  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    environment:
      POSTGRES_DB: marketing_roas
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./src/postgres/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
    networks:
      - kafka-network
    healthcheck:
      test: pg_isready -U postgres
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (이미 Week 1에 추가됨)
  redis:
    image: redis:7.2-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - kafka-network
    healthcheck:
      test: redis-cli ping
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

**실행:**
```bash
docker-compose up -d postgres redis

# 상태 확인
docker-compose ps

# PostgreSQL 연결 테스트
docker-compose exec postgres psql -U postgres -d marketing_roas -c "SELECT schema_name FROM information_schema.schemata;"

# Redis 연결 테스트
docker-compose exec redis redis-cli PING
```

### ✅ 완료 기준

- [ ] Redis 캐시 매니저 구현 완료
- [ ] PostgreSQL 스키마 생성 완료
- [ ] DB 커넥터 구현 완료
- [ ] docker-compose.yml 업데이트 완료
- [ ] PostgreSQL 헬스체크 통과
- [ ] Redis 헬스체크 통과
- [ ] 데이터 저장/조회 테스트 성공

### 📊 산출물

```
src/redis/
├── cache_manager.py

src/postgres/
├── schema.sql
└── db_connector.py

docker-compose.yml (PostgreSQL, Redis 추가)
```

---

## 📌 Day 5 (금): Streamlit 대시보드 & 통합 테스트 (2시간)

### 목표
- Streamlit 대시보드 구축
- Redis 실시간 데이터 조회 및 시각화
- 차트 및 지표 구현
- E2E 통합 테스트

### 📋 할당 시간
| 작업 | 시간 |
|------|------|
| Streamlit 기본 구조 | 30분 |
| 차트 및 지표 | 40분 |
| 실시간 데이터 연동 | 30분 |
| E2E 테스트 | 20분 |

### 🛠️ 실습 내용

#### 5-1. Streamlit 대시보드 (40분)

**파일:** `src/streamlit/dashboard.py`

```python
"""
실시간 CTR 분석 대시보드
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from redis.cache_manager import RedisCacheManager
from postgres.db_connector import PostgreSQLConnector

# 페이지 설정
st.set_page_config(
    page_title="Ad CTR Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)


class Dashboard:
    """대시보드 클래스"""

    def __init__(self):
        """초기화"""
        try:
            self.redis = RedisCacheManager(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379))
            )
            self.db = PostgreSQLConnector()
        except Exception as e:
            st.error(f"Connection error: {e}")
            self.redis = None
            self.db = None

    def get_current_metrics(self):
        """현재 메트릭 조회"""
        if not self.redis:
            return {}
        return self.redis.get_all_current_metrics()

    def render_header(self):
        """헤더 렌더링"""
        st.title("📊 실시간 광고 CTR 분석 대시보드")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="현재 상태",
                value="🟢 LIVE",
                delta="실시간"
            )

        with col2:
            st.metric(
                label="업데이트",
                value=datetime.now().strftime("%H:%M:%S"),
                delta_color="off"
            )

        with col3:
            st.metric(
                label="데이터 소스",
                value="Kafka + Flink",
                delta_color="off"
            )

    def render_1min_metrics(self):
        """1분 메트릭 렌더링"""
        st.subheader("⏱️  1분 단위 메트릭")

        metrics = self.get_current_metrics()
        metrics_1min = metrics.get('1min', {})

        if not metrics_1min:
            st.info("아직 데이터가 없습니다.")
            return

        # 데이터 준비
        data = []
        for key, value in metrics_1min.items():
            data.append({
                'Window': key,
                'CTR': value.get('ctr', 0),
                'Impressions': value.get('total_impressions', 0),
                'Clicks': value.get('total_clicks', 0)
            })

        df = pd.DataFrame(data)

        col1, col2, col3 = st.columns(3)

        with col1:
            avg_ctr = df['CTR'].mean() if len(df) > 0 else 0
            st.metric("평균 CTR", f"{avg_ctr:.2f}%")

        with col2:
            total_impressions = df['Impressions'].sum()
            st.metric("총 노출수", f"{total_impressions:,}")

        with col3:
            total_clicks = df['Clicks'].sum()
            st.metric("총 클릭수", f"{total_clicks:,}")

        # 표 출력
        st.dataframe(df, use_container_width=True)

        # 차트
        if len(df) > 0:
            fig = px.bar(df, x='Window', y='CTR', title='Window별 CTR')
            st.plotly_chart(fig, use_container_width=True)

    def render_5min_metrics(self):
        """5분 메트릭 렌더링"""
        st.subheader("📊 5분 단위 메트릭")

        metrics = self.get_current_metrics()
        metrics_5min = metrics.get('5min', {})

        if not metrics_5min:
            st.info("아직 데이터가 없습니다.")
            return

        # 데이터 준비
        data = []
        for key, value in metrics_5min.items():
            data.append({
                'Window': key,
                'CTR': value.get('ctr', 0),
                'Impressions': value.get('total_impressions', 0),
                'Clicks': value.get('total_clicks', 0)
            })

        df = pd.DataFrame(data)

        col1, col2, col3 = st.columns(3)

        with col1:
            avg_ctr = df['CTR'].mean() if len(df) > 0 else 0
            st.metric("평균 CTR", f"{avg_ctr:.2f}%")

        with col2:
            total_impressions = df['Impressions'].sum()
            st.metric("총 노출수", f"{total_impressions:,}")

        with col3:
            total_clicks = df['Clicks'].sum()
            st.metric("총 클릭수", f"{total_clicks:,}")

        # 표 출력
        st.dataframe(df, use_container_width=True)

        # 차트
        if len(df) > 0:
            fig = px.line(df, x='Window', y='CTR', title='시간대별 CTR 추이', markers=True)
            st.plotly_chart(fig, use_container_width=True)

    def render_comparision(self):
        """1분 vs 5분 비교"""
        st.subheader("🔍 1분 vs 5분 비교")

        metrics = self.get_current_metrics()

        col1, col2 = st.columns(2)

        with col1:
            metrics_1min = metrics.get('1min', {})
            if metrics_1min:
                ctr_1min = [v.get('ctr', 0) for v in metrics_1min.values()]
                st.metric("평균 1분 CTR", f"{sum(ctr_1min)/len(ctr_1min):.2f}%" if ctr_1min else "N/A")

        with col2:
            metrics_5min = metrics.get('5min', {})
            if metrics_5min:
                ctr_5min = [v.get('ctr', 0) for v in metrics_5min.values()]
                st.metric("평균 5분 CTR", f"{sum(ctr_5min)/len(ctr_5min):.2f}%" if ctr_5min else "N/A")

    def run(self):
        """대시보드 실행"""
        self.render_header()

        tab1, tab2, tab3, tab4 = st.tabs(["1분 메트릭", "5분 메트릭", "비교", "설정"])

        with tab1:
            self.render_1min_metrics()

        with tab2:
            self.render_5min_metrics()

        with tab3:
            self.render_comparision()

        with tab4:
            st.subheader("⚙️  설정")
            st.write("**Redis 연결 상태:**")
            if self.redis and self.redis.health_check():
                st.success("✅ 정상")
            else:
                st.error("❌ 실패")

            st.write("**PostgreSQL 연결 상태:**")
            if self.db and self.db.health_check():
                st.success("✅ 정상")
            else:
                st.error("❌ 실패")

        # 자동 새로고침
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            refresh_interval = st.slider("새로고침 간격 (초)", 5, 60, 10)
        with col2:
            if st.button("🔄 지금 새로고침"):
                st.rerun()


if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.run()
```

**실행:**
```bash
streamlit run src/streamlit/dashboard.py

# 또는 특정 포트 지정
streamlit run src/streamlit/dashboard.py --server.port 8501
```

#### 5-2. Streamlit 설정 (10분)

**파일:** `src/streamlit/.streamlit/config.toml`

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[client]
toolbarMode = "minimal"
showErrorDetails = true

[server]
port = 8501
headless = true
runOnSave = true
maxUploadSize = 200
```

#### 5-3. E2E 통합 테스트 (40분)

**파일:** `scripts/week2_e2e_test.sh`

```bash
#!/bin/bash

set -e

echo "=========================================="
echo "E2E TEST: Week 2 Pipeline Validation"
echo "=========================================="

# 1️⃣  서비스 상태 확인
echo ""
echo "1️⃣  Checking all services..."
docker-compose ps

# 2️⃣  Redis 헬스 체크
echo ""
echo "2️⃣  Redis health check..."
docker-compose exec redis redis-cli PING || echo "Redis not ready"

# 3️⃣  PostgreSQL 헬스 체크
echo ""
echo "3️⃣  PostgreSQL health check..."
docker-compose exec postgres psql -U postgres -d marketing_roas -c "SELECT 1;" || echo "PostgreSQL not ready"

# 4️⃣  Flink 상태 확인
echo ""
echo "4️⃣  Flink JobManager status..."
curl -s http://localhost:8081/overview | jq '.["taskmanagers"]' || echo "Flink not ready"

# 5️⃣  Producer 실행 (테스트 데이터)
echo ""
echo "5️⃣  Running producer (1,000 messages)..."
cd src/kafka
timeout 60 python producer.py 1000 || true
cd ../../

# 6️⃣  Redis 데이터 확인
echo ""
echo "6️⃣  Checking Redis data..."
docker-compose exec redis redis-cli KEYS "metrics:*" | head -5 || echo "No metrics yet"

# 7️⃣  PostgreSQL 데이터 확인
echo ""
echo "7️⃣  Checking PostgreSQL data..."
docker-compose exec postgres psql -U postgres -d marketing_roas -c "SELECT COUNT(*) FROM realtime.metrics_1min;" || echo "No data yet"

echo ""
echo "=========================================="
echo "✅ E2E TEST COMPLETE"
echo "=========================================="
echo ""
echo "대시보드 접속: http://localhost:8501"
echo "Flink UI: http://localhost:8081"
echo "Prometheus: http://localhost:9090"
```

**실행:**
```bash
chmod +x scripts/week2_e2e_test.sh
bash scripts/week2_e2e_test.sh
```

### ✅ 완료 기준

- [ ] Streamlit 대시보드 구축 완료
- [ ] Redis 실시간 데이터 연동 완료
- [ ] PostgreSQL 데이터 조회 완료
- [ ] 차트 및 지표 표시 완료
- [ ] http://localhost:8501 접근 가능
- [ ] E2E 테스트 통과

### 📊 산출물

```
src/streamlit/
├── dashboard.py (메인 대시보드)
└── .streamlit/
    └── config.toml (설정)

scripts/
└── week2_e2e_test.sh (통합 테스트)
```

---

## 주간 마일스톤

- ✅ PyFlink 개발환경 구축 완료
- ✅ Kafka → Flink 스트리밍 연결 완료
- ✅ 1분, 5분 Window CTR 계산 완료
- ✅ Redis 캐시 저장 완료
- ✅ PostgreSQL 데이터 적재 완료
- ✅ Streamlit 실시간 대시보드 구축 완료

## 성능 지표

| 지표 | 목표 | 상태 |
|------|------|------|
| 메시지 처리 레이턴시 | < 1초 | - |
| 캐시 조회 응답시간 | < 100ms | - |
| 대시보드 갱신 주기 | 10초 | - |
| Window 메트릭 정확도 | > 99% | - |

## 위험요소 및 해결책

| 위험요소 | 영향 | 해결책 |
|---------|------|--------|
| 메모리 누수 (Flink) | 높음 | Checkpoint 용량 모니터링 |
| Redis 메모리 부족 | 높음 | TTL 정책 강화 |
| 대시보드 느린 응답 | 중간 | 캐시 최적화 |
| 데이터 손실 | 높음 | Checkpoint 및 백업 |

## 다음 주 준비사항

- [ ] Airflow 환경 구축
- [ ] dbt 모델 설계
- [ ] DLQ 재처리 로직 준비
- [ ] Monitoring/Alerting 강화

---

**Week 2 완료!** 🎉
**다음 주 목표:** Airflow 오케스트레이션 & dbt 데이터 모델링
