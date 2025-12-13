"""
Kafka Retry Consumer 설정
"""

import os
from dotenv import load_dotenv

load_dotenv()


class RetryConsumerConfig:
    """Kafka Retry Consumer 설정"""

    # Kafka Broker
    BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    TOPIC = os.getenv('KAFKA_RETRY_TOPIC', 'ad_events_retry')
    GROUP_ID = os.getenv('RETRY_CONSUMER_GROUP_ID', 'retry_consumer_group')

    # Consumer 설정
    AUTO_OFFSET_RESET = os.getenv('AUTO_OFFSET_RESET', 'earliest')
    ENABLE_AUTO_COMMIT = os.getenv('ENABLE_AUTO_COMMIT', 'true').lower() == 'true'
    SESSION_TIMEOUT_MS = int(os.getenv('SESSION_TIMEOUT_MS', 30000))
    MAX_POLL_RECORDS = int(os.getenv('MAX_POLL_RECORDS', 500))
    ISOLATION_LEVEL = os.getenv('ISOLATION_LEVEL', 'read_committed')

    # 재시도 설정
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    RETRY_BACKOFF_MS = int(os.getenv('RETRY_BACKOFF_MS', 1000))
    RETRY_BACKOFF_MAX_MS = int(os.getenv('RETRY_BACKOFF_MAX_MS', 32000))

    # Dead Letter Topic
    DLQ_TOPIC = os.getenv('KAFKA_DLQ_TOPIC', 'ad_events_dlq')

    # 로깅
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def get_consumer_config(cls) -> dict:
        """Consumer 설정 딕셔너리 반환"""
        return {
            'bootstrap.servers': cls.BOOTSTRAP_SERVERS,
            'group.id': cls.GROUP_ID,
            'auto.offset.reset': cls.AUTO_OFFSET_RESET,
            'enable.auto.commit': cls.ENABLE_AUTO_COMMIT,
            'session.timeout.ms': cls.SESSION_TIMEOUT_MS,
            'max.poll.records': cls.MAX_POLL_RECORDS,
            'isolation.level': cls.ISOLATION_LEVEL,
        }

    @classmethod
    def validate(cls):
        """설정 검증"""
        print("=" * 60)
        print("Kafka Retry Consumer 설정")
        print("=" * 60)
        print(f"Bootstrap Servers: {cls.BOOTSTRAP_SERVERS}")
        print(f"Topic: {cls.TOPIC}")
        print(f"Group ID: {cls.GROUP_ID}")
        print(f"최대 재시도 횟수: {cls.MAX_RETRIES}")
        print(f"DLQ Topic: {cls.DLQ_TOPIC}")
        print("=" * 60)

        print("설정 검증 완료")
        return True
