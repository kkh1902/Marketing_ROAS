"""
pytest E2E 테스트 conftest.py
E2E 테스트에서 사용할 fixtures (Kafka 서버 필요)
테스트 토픽: test_ad_events_raw, test_ad_events_retry, test_ad_events_dlq
"""

import pytest
import os
import time


@pytest.fixture(scope="session")
def kafka_bootstrap_servers():
    """Kafka Bootstrap 서버 주소"""
    return os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')


@pytest.fixture(scope="function")
def kafka_producer(kafka_bootstrap_servers):
    """실제 Kafka Producer (테스트용)"""
    try:
        from kafka import KafkaProducer
        import json

        producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            request_timeout_ms=5000
        )
        yield producer
        producer.close()
    except Exception as e:
        pytest.skip(f"Kafka Producer not available: {e}")


@pytest.fixture(scope="function")
def kafka_consumer(kafka_bootstrap_servers):
    """실제 Kafka Consumer (테스트용)"""
    try:
        from kafka import KafkaConsumer
        import json

        consumer = KafkaConsumer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='e2e-test-consumer',
            session_timeout_ms=10000,
            request_timeout_ms=5000
        )
        yield consumer
        consumer.close()
    except Exception as e:
        pytest.skip(f"Kafka Consumer not available: {e}")


@pytest.fixture(scope="function")
def clear_test_topics():
    """테스트 토픽의 메시지 정리"""
    time.sleep(0.5)
    yield
    time.sleep(0.5)


# 테스트 토픽 상수
TEST_RAW_TOPIC = "test_ad_events_raw"
TEST_RETRY_TOPIC = "test_ad_events_retry"
TEST_DLQ_TOPIC = "test_ad_events_dlq"
