# -*- coding: utf-8 -*-
"""
Flink Configuration
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class FlinkConfig:
    """Flink Configuration"""

    # ============================================================
    # Kafka Configuration
    # ============================================================
    BOOTSTRAP_SERVERS = 'broker:29092'
    KAFKA_TOPIC_RAW = 'ad_events'  # Kafka 토픽명
    KAFKA_GROUP_ID = 'flink-ctr-group'
    KAFKA_AUTO_OFFSET_RESET = 'earliest'  # earliest or latest

    # ============================================================
    # Schema Registry Configuration (Avro)
    # ============================================================
    SCHEMA_REGISTRY_URL = 'http://schema-registry:8081'
    AD_EVENT_SCHEMA_SUBJECT = 'ad_events-value'  # Schema Registry subject
    CTR_METRIC_SCHEMA_SUBJECT = 'ctr_metrics-value'

    # ============================================================
    # PostgreSQL Configuration
    # ============================================================
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'my-app-db')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'admin')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'admin')

    # PostgreSQL JDBC 연결 문자열
    POSTGRES_JDBC_URL = f'jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    POSTGRES_JDBC_DRIVER = 'org.postgresql.Driver'

    # ============================================================
    # PostgreSQL 테이블 이름
    # ============================================================
    PG_TABLE_RAW_EVENTS = 'realtime.ad_events'
    PG_TABLE_METRICS_1MIN = 'realtime.ctr_metrics_1min'
    PG_TABLE_METRICS_5MIN = 'realtime.ctr_metrics_5min'

    # ============================================================
    # Flink Settings
    # ============================================================
    PARALLELISM = 4  # Task Manager 병렬처리 수준
    CHECKPOINT_INTERVAL = 60000  # 60 seconds
    CHECKPOINT_TIMEOUT = 600000  # 10 minutes
    MIN_PAUSE_BETWEEN_CHECKPOINTS = 30000  # 30 seconds

    # ============================================================
    # Windowing Configuration
    # ============================================================
    WINDOW_SIZE_1MIN = 60000  # 1분 (밀리초)
    WINDOW_SIZE_5MIN = 300000  # 5분 (밀리초)
    WATERMARK_DELAY = 10000  # 10초 (지연 처리용)

    # ============================================================
    # Sink Configuration
    # ============================================================
    BATCH_SIZE = 1000  # 배치 크기 (원본 이벤트)
    BATCH_INTERVAL_MS = 5000  # 5초
    MAX_RETRIES = 3  # 재시도 횟수

    # ============================================================
    # Avro Schema 파일 경로
    # ============================================================
    SCHEMA_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/schemas'
    AD_EVENT_SCHEMA_FILE = f'{SCHEMA_DIR}/ad_event.avsc'
    CTR_METRIC_SCHEMA_FILE = f'{SCHEMA_DIR}/ctr_metric.avsc'

    @staticmethod
    def validate():
        """Validate all required configurations"""
        required_configs = {
            'BOOTSTRAP_SERVERS': FlinkConfig.BOOTSTRAP_SERVERS,
            'KAFKA_TOPIC_RAW': FlinkConfig.KAFKA_TOPIC_RAW,
            'KAFKA_GROUP_ID': FlinkConfig.KAFKA_GROUP_ID,
            'SCHEMA_REGISTRY_URL': FlinkConfig.SCHEMA_REGISTRY_URL,
            'POSTGRES_HOST': FlinkConfig.POSTGRES_HOST,
            'POSTGRES_DB': FlinkConfig.POSTGRES_DB,
            'POSTGRES_USER': FlinkConfig.POSTGRES_USER,
        }

        missing_configs = [key for key, value in required_configs.items() if not value]
        if missing_configs:
            raise ValueError(f"Missing required configurations: {', '.join(missing_configs)}")

        return True

    @staticmethod
    def print_config():
        """Print configuration for debugging"""
        print("=" * 60)
        print("FLINK CONFIGURATION")
        print("=" * 60)
        print(f"Kafka Broker: {FlinkConfig.BOOTSTRAP_SERVERS}")
        print(f"Kafka Topic: {FlinkConfig.KAFKA_TOPIC_RAW}")
        print(f"Schema Registry: {FlinkConfig.SCHEMA_REGISTRY_URL}")
        print(f"PostgreSQL: {FlinkConfig.POSTGRES_HOST}:{FlinkConfig.POSTGRES_PORT}/{FlinkConfig.POSTGRES_DB}")
        print(f"Parallelism: {FlinkConfig.PARALLELISM}")
        print("=" * 60)
