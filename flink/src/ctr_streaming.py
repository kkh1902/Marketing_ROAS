# -*- coding: utf-8 -*-
"""
Flink CTR Streaming Job

실시간 광고 클릭 데이터 처리:
- Kafka에서 Avro 포맷 이벤트 수신
- 1분/5분 Tumbling Window로 CTR 집계
- 원본 이벤트 및 집계 메트릭을 PostgreSQL에 저장

데이터 흐름:
  Kafka (Avro) → Flink (파싱/변환) → PostgreSQL (저장)
"""

import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Flink
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import MapFunction, WindowFunction, SinkFunction
from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer
from pyflink.common.time import Time

# Avro
import fastavro
import io

# PostgreSQL
import psycopg2
from psycopg2.extras import execute_batch

# Config
from config import FlinkConfig

# ============================================================
# 로깅 설정
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# 데이터 모델
# ============================================================

class AdEvent:
    """
    광고 이벤트 데이터 모델

    Kafka에서 수신한 Avro 데이터를 파싱한 Python 객체
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Args:
            data: Avro 파싱 결과 (딕셔너리)
        """
        self.id = data.get('id')
        self.click = data.get('click')
        self.hour = data.get('hour')
        self.banner_pos = data.get('banner_pos')
        self.site_id = data.get('site_id')
        self.site_domain = data.get('site_domain')
        self.site_category = data.get('site_category')
        self.app_id = data.get('app_id')
        self.app_domain = data.get('app_domain')
        self.app_category = data.get('app_category')
        self.device_id = data.get('device_id')
        self.device_ip = data.get('device_ip')
        self.device_model = data.get('device_model')
        self.device_type = data.get('device_type')
        self.device_conn_type = data.get('device_conn_type')
        self.C1 = data.get('C1')
        self.C14 = data.get('C14')
        self.C15 = data.get('C15')
        self.C16 = data.get('C16')
        self.C17 = data.get('C17')
        self.C18 = data.get('C18')
        self.C19 = data.get('C19')
        self.C20 = data.get('C20')
        self.C21 = data.get('C21')
        # 윈도우 처리용 타임스탬프 (밀리초)
        self.timestamp = int(datetime.now().timestamp() * 1000)

    def __str__(self):
        return f"AdEvent(id={self.id}, click={self.click}, site_id={self.site_id})"

    def to_tuple(self):
        """PostgreSQL INSERT용 튜플로 변환"""
        return (
            self.id, self.click, self.hour, self.banner_pos,
            self.site_id, self.site_domain, self.site_category,
            self.app_id, self.app_domain, self.app_category,
            self.device_id, self.device_ip, self.device_model,
            self.device_type, self.device_conn_type,
            self.C1, self.C14, self.C15, self.C16, self.C17,
            self.C18, self.C19, self.C20, self.C21
        )


class CTRMetric:
    """
    CTR 집계 지표 데이터 모델

    Flink Window에서 집계한 결과
    """

    def __init__(self, window_start: int, window_end: int,
                 impressions: int, clicks: int):
        """
        Args:
            window_start: 윈도우 시작 시간 (밀리초)
            window_end: 윈도우 종료 시간 (밀리초)
            impressions: 노출 건수 (click=0)
            clicks: 클릭 건수 (click=1)
        """
        self.window_start = datetime.fromtimestamp(window_start / 1000)
        self.window_end = datetime.fromtimestamp(window_end / 1000)
        self.impressions = impressions
        self.clicks = clicks
        self.ctr = (clicks / impressions * 100) if impressions > 0 else 0.0

    def __str__(self):
        return (f"CTRMetric(window={self.window_start}, "
                f"impressions={self.impressions}, clicks={self.clicks}, ctr={self.ctr:.2f}%)")

    def to_tuple(self):
        """PostgreSQL INSERT용 튜플로 변환"""
        return (self.window_start, self.window_end, self.impressions, self.clicks, self.ctr)


# ============================================================
# Avro 스키마 로드
# ============================================================

def load_avro_schema(schema_file: str) -> Dict[str, Any]:
    """
    Avro 스키마 파일 로드

    Args:
        schema_file: 스키마 파일 경로

    Returns:
        Avro 스키마 (딕셔너리)
    """
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        logger.info(f"✅ Loaded Avro schema from {schema_file}")
        return schema
    except Exception as e:
        logger.error(f"❌ Failed to load schema from {schema_file}: {e}")
        raise


# ============================================================
# 이벤트 파싱 함수
# ============================================================

class AvroDeserializer(MapFunction):
    """Avro 바이트를 AdEvent로 변환"""

    def __init__(self):
        self.ad_event_schema = None

    def open(self, runtime_context):
        """Flink에서 함수 초기화 시 호출"""
        self.ad_event_schema = load_avro_schema(FlinkConfig.AD_EVENT_SCHEMA_FILE)

    def map(self, value):
        """
        Kafka 메시지 (Avro 바이트)를 AdEvent로 변환

        Args:
            value: Avro 인코딩된 바이트

        Returns:
            AdEvent 객체
        """
        try:
            # Avro 바이트 디코딩
            bytes_reader = io.BytesIO(value)
            reader = fastavro.reader(bytes_reader, reader_schema=self.ad_event_schema)
            record = next(reader)

            # AdEvent 객체 생성
            event = AdEvent(record)
            logger.debug(f"✅ Parsed: {event}")
            return event

        except Exception as e:
            logger.error(f"❌ Failed to parse Avro message: {e}")
            raise


# ============================================================
# Kafka Consumer 설정
# ============================================================

def setup_kafka_consumer() -> FlinkKafkaConsumer:
    """
    Kafka Consumer 설정 (Avro 포맷)

    Returns:
        FlinkKafkaConsumer 객체
    """
    kafka_config = {
        'bootstrap.servers': FlinkConfig.BOOTSTRAP_SERVERS,
        'group.id': FlinkConfig.KAFKA_GROUP_ID,
        'auto.offset.reset': FlinkConfig.KAFKA_AUTO_OFFSET_RESET,
    }

    # SimpleStringSchema 사용 (Avro 바이트를 직접 처리)
    consumer = FlinkKafkaConsumer(
        FlinkConfig.KAFKA_TOPIC_RAW,
        SimpleStringSchema(),  # 바이트 수신
        kafka_config
    )

    logger.info(f"✅ Kafka Consumer configured: {FlinkConfig.KAFKA_TOPIC_RAW}")
    return consumer


# ============================================================
# Window 집계 함수
# ============================================================

class CTRWindow(WindowFunction):
    """
    1분 또는 5분 Window에서 CTR 계산

    입력: 윈도우 내 모든 AdEvent
    출력: CTRMetric (1개)
    """

    def apply(self, key, window, elements):
        """
        Window 집계 함수

        Args:
            key: Group 키 (현재는 사용 안 함)
            window: 윈도우 메타데이터
            elements: 윈도우 내 모든 AdEvent

        Yields:
            CTRMetric
        """
        # 이벤트 수집
        events = list(elements)

        # 집계 계산
        impressions = sum(1 for e in events if e.click == 0)
        clicks = sum(1 for e in events if e.click == 1)

        # 메트릭 생성
        metric = CTRMetric(
            window_start=window.get_start(),
            window_end=window.get_end(),
            impressions=impressions,
            clicks=clicks
        )

        logger.info(f"📊 Window Result: {metric}")
        yield metric


# ============================================================
# PostgreSQL Sink 함수
# ============================================================

class PostgreSQLRawEventsSink(SinkFunction):
    """원본 이벤트를 PostgreSQL (realtime.ad_events)에 저장"""

    def __init__(self):
        self.conn = None
        self.batch = []

    def invoke(self, value: AdEvent, context=None):
        """
        각 이벤트를 처리하고 배치에 추가

        Args:
            value: AdEvent 객체
            context: Flink 컨텍스트 (선택)
        """
        if self.conn is None:
            self._connect()

        try:
            # 배치에 추가
            self.batch.append(value.to_tuple())

            # 배치 크기에 도달하면 INSERT
            if len(self.batch) >= FlinkConfig.BATCH_SIZE:
                self._flush()

        except Exception as e:
            logger.error(f"❌ Error adding event to batch: {e}")

    def _connect(self):
        """PostgreSQL 연결 초기화"""
        try:
            self.conn = psycopg2.connect(
                host=FlinkConfig.POSTGRES_HOST,
                port=FlinkConfig.POSTGRES_PORT,
                database=FlinkConfig.POSTGRES_DB,
                user=FlinkConfig.POSTGRES_USER,
                password=FlinkConfig.POSTGRES_PASSWORD
            )
            logger.info(f"✅ PostgreSQL connected: {FlinkConfig.POSTGRES_HOST}")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            raise

    def _flush(self):
        """배치 데이터를 PostgreSQL에 INSERT"""
        if not self.batch or self.conn is None:
            return

        try:
            sql = f"""
                INSERT INTO {FlinkConfig.PG_TABLE_RAW_EVENTS}
                (id, click, hour, banner_pos, site_id, site_domain, site_category,
                 app_id, app_domain, app_category, device_id, device_ip, device_model,
                 device_type, device_conn_type, C1, C14, C15, C16, C17, C18, C19, C20, C21)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            with self.conn.cursor() as cursor:
                execute_batch(cursor, sql, self.batch)

            self.conn.commit()
            logger.info(f"✅ Inserted {len(self.batch)} raw events to PostgreSQL")
            self.batch = []

        except Exception as e:
            logger.error(f"❌ PostgreSQL INSERT failed: {e}")
            if self.conn:
                self.conn.rollback()

    def finish(self):
        """마지막 배치 플러시 및 연결 종료"""
        try:
            self._flush()
            if self.conn:
                self.conn.close()
            logger.info("✅ PostgreSQL connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing PostgreSQL: {e}")


class PostgreSQLMetricsSink(SinkFunction):
    """집계 메트릭을 PostgreSQL (realtime.ctr_metrics_*min)에 저장"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.conn = None

    def invoke(self, value: CTRMetric, context=None):
        """
        메트릭을 PostgreSQL에 INSERT

        Args:
            value: CTRMetric 객체
            context: Flink 컨텍스트 (선택)
        """
        if self.conn is None:
            self._connect()

        try:
            sql = f"""
                INSERT INTO {self.table_name}
                (window_start, window_end, impressions, clicks, ctr)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """

            if self.conn:
                with self.conn.cursor() as cursor:
                    cursor.execute(sql, value.to_tuple())

                self.conn.commit()
                logger.info(f"✅ Inserted metric to {self.table_name}: {value}")

        except Exception as e:
            logger.error(f"❌ PostgreSQL INSERT failed: {e}")
            if self.conn:
                self.conn.rollback()

    def _connect(self):
        """PostgreSQL 연결 초기화"""
        try:
            self.conn = psycopg2.connect(
                host=FlinkConfig.POSTGRES_HOST,
                port=FlinkConfig.POSTGRES_PORT,
                database=FlinkConfig.POSTGRES_DB,
                user=FlinkConfig.POSTGRES_USER,
                password=FlinkConfig.POSTGRES_PASSWORD
            )
            logger.info(f"✅ PostgreSQL connected for metrics: {self.table_name}")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            raise

    def finish(self):
        """연결 종료"""
        try:
            if self.conn:
                self.conn.close()
            logger.info(f"✅ PostgreSQL connection closed for {self.table_name}")
        except Exception as e:
            logger.error(f"❌ Error closing PostgreSQL: {e}")


# ============================================================
# 메인 실행
# ============================================================

def main():
    """Flink CTR 스트리밍 작업 메인 함수"""

    try:
        # 설정 검증
        FlinkConfig.validate()
        FlinkConfig.print_config()
        logger.info("✅ Configuration validated")

    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        return 1

    try:
        # StreamExecutionEnvironment 초기화
        env = StreamExecutionEnvironment.get_execution_environment()
        env.set_parallelism(FlinkConfig.PARALLELISM)

        # Checkpoint 설정 (Flink 1.17.1)
        # enable_checkpointing(interval_ms)로 설정
        env.enable_checkpointing(FlinkConfig.CHECKPOINT_INTERVAL)

        logger.info("✅ StreamExecutionEnvironment initialized")
        logger.info(f"   Parallelism: {FlinkConfig.PARALLELISM}")
        logger.info(f"   Checkpoint Interval: {FlinkConfig.CHECKPOINT_INTERVAL}ms")

        # Kafka Consumer 설정
        kafka_consumer = setup_kafka_consumer()

        # 데이터 스트림 생성 및 Avro 디코딩
        kafka_stream = env.add_source(kafka_consumer)
        logger.info("✅ Kafka source added")

        # Avro 디코딩
        parsed_stream = kafka_stream.map(AvroDeserializer())
        logger.info("✅ Avro deserialization pipeline configured")

        # 원본 이벤트를 PostgreSQL에 저장 (병렬 처리)
        parsed_stream.add_sink(PostgreSQLRawEventsSink())
        logger.info("✅ Raw events sink configured")

        # 1분 Window 집계
        ctr_1min_stream = (
            parsed_stream
            .key_by(lambda e: "default_key")  # 모든 이벤트를 같은 윈도우로
            .window(TumblingEventTimeWindows.of(Time.milliseconds(FlinkConfig.WINDOW_SIZE_1MIN)))
            .apply(CTRWindow())
        )
        ctr_1min_stream.add_sink(PostgreSQLMetricsSink(FlinkConfig.PG_TABLE_METRICS_1MIN))
        logger.info("✅ 1min window aggregation configured")

        # 5분 Window 집계
        ctr_5min_stream = (
            parsed_stream
            .key_by(lambda e: "default_key")
            .window(TumblingEventTimeWindows.of(Time.milliseconds(FlinkConfig.WINDOW_SIZE_5MIN)))
            .apply(CTRWindow())
        )
        ctr_5min_stream.add_sink(PostgreSQLMetricsSink(FlinkConfig.PG_TABLE_METRICS_5MIN))
        logger.info("✅ 5min window aggregation configured")

        # 작업 실행
        logger.info("=" * 60)
        logger.info("Starting Flink CTR Streaming Job...")
        logger.info("=" * 60)

        env.execute("Flink CTR Streaming Job")
        logger.info("✅ Job completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"❌ Job failed: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
