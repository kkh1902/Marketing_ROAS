"""
pytest Integration 테스트 conftest.py
Integration 테스트에서 사용할 fixtures (Kafka 서버 필요)
테스트 토픽: test_ad_events_raw, test_ad_events_retry, test_ad_events_dlq
"""

import pytest
import os
import sys
import json
import tempfile
import time
from pathlib import Path

# 프로젝트 루트 경로
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session")
def kafka_bootstrap_servers():
    """Kafka Bootstrap 서버 주소"""
    return os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')


@pytest.fixture(scope="function")
def kafka_admin_client(kafka_bootstrap_servers):
    """Kafka Admin 클라이언트"""
    try:
        from kafka.admin import KafkaAdminClient
        admin_client = KafkaAdminClient(
            bootstrap_servers=kafka_bootstrap_servers,
            request_timeout_ms=5000
        )
        yield admin_client
        admin_client.close()
    except Exception as e:
        pytest.skip(f"Kafka not available: {e}")


@pytest.fixture(scope="function")
def kafka_producer(kafka_bootstrap_servers):
    """실제 Kafka Producer (Integration 테스트용)"""
    try:
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8') if isinstance(v, dict) else v,
            acks='all',
            request_timeout_ms=5000
        )
        yield producer
        producer.close()
    except Exception as e:
        pytest.skip(f"Kafka Producer not available: {e}")


@pytest.fixture(scope="function")
def kafka_consumer(kafka_bootstrap_servers):
    """실제 Kafka Consumer (Integration 테스트용)"""
    try:
        from kafka import KafkaConsumer

        consumer = KafkaConsumer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
            auto_offset_reset='earliest',
            group_id='integration-test-consumer',
            session_timeout_ms=10000,
            request_timeout_ms=5000
        )
        yield consumer
        consumer.close()
    except Exception as e:
        pytest.skip(f"Kafka Consumer not available: {e}")


@pytest.fixture(scope="function")
def temp_db():
    """임시 SQLite 데이터베이스 (DLQ Consumer 테스트용)"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_dlq.db')

    yield db_path

    # cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def temp_log_dir():
    """임시 로그 디렉토리 (DLQ Consumer 테스트용)"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    # cleanup
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)


# 테스트 토픽 상수
TEST_RAW_TOPIC = "test_ad_events_raw"
TEST_RETRY_TOPIC = "test_ad_events_retry"
TEST_DLQ_TOPIC = "test_ad_events_dlq"

# 테스트 설정
TEST_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
