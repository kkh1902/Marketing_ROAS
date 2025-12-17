"""
pytest Integration 테스트 conftest.py
Integration 테스트에서 사용할 fixtures (Kafka + PostgreSQL 필요)
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

# kafka-python 직접 import (프로젝트 kafka 폴더 충돌 회피)
try:
    # 캐시된 kafka 모듈 제거
    for key in list(sys.modules.keys()):
        if 'kafka' in key:
            del sys.modules[key]

    # site-packages 경로를 sys.path 맨 앞에 추가
    site_packages = r'C:\Users\PC\AppData\Local\Programs\Python\Python310\Lib\site-packages'
    if site_packages not in sys.path:
        sys.path.insert(0, site_packages)

    # 프로젝트 루트는 맨 뒤에
    if PROJECT_ROOT in sys.path:
        sys.path.remove(PROJECT_ROOT)
    sys.path.append(PROJECT_ROOT)

    # kafka-python import
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.admin import KafkaAdminClient
except Exception as e:
    print(f"Warning: kafka-python import failed: {e}")


# ============================================================
# Kafka Fixtures
# ============================================================

@pytest.fixture(scope="session")
def kafka_bootstrap_servers():
    """Kafka Bootstrap 서버 주소"""
    return os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')


@pytest.fixture(scope="function")
def kafka_admin_client(kafka_bootstrap_servers):
    """Kafka Admin 클라이언트"""
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=kafka_bootstrap_servers,
            request_timeout_ms=15000
        )
        yield admin_client
        admin_client.close()
    except Exception as e:
        pytest.skip(f"Kafka Admin Client not available: {e}")


@pytest.fixture(scope="function")
def kafka_producer(kafka_bootstrap_servers):
    """실제 Kafka Producer (Integration 테스트용)"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8') if isinstance(v, dict) else v,
            acks='all',
            request_timeout_ms=15000
        )
        yield producer
        producer.close()
    except Exception as e:
        pytest.skip(f"Kafka Producer not available: {e}")


@pytest.fixture(scope="function")
def kafka_consumer(kafka_bootstrap_servers):
    """실제 Kafka Consumer (Integration 테스트용)"""
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
            auto_offset_reset='earliest',
            group_id='integration-test-consumer',
            session_timeout_ms=6000,
            request_timeout_ms=15000
        )
        yield consumer
        consumer.close()
    except Exception as e:
        pytest.skip(f"Kafka Consumer not available: {e}")


# ============================================================
# PostgreSQL Fixtures
# ============================================================

@pytest.fixture(scope="session")
def postgres_config():
    """PostgreSQL 연결 설정"""
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'postgres'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }


@pytest.fixture(scope="function")
def postgres_connection(postgres_config):
    """PostgreSQL 데이터베이스 연결"""
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=postgres_config['host'],
            port=postgres_config['port'],
            database=postgres_config['database'],
            user=postgres_config['user'],
            password=postgres_config['password']
        )
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.fixture(scope="function")
def postgres_cursor(postgres_connection):
    """PostgreSQL 커서"""
    cursor = postgres_connection.cursor()
    yield cursor
    cursor.close()
    postgres_connection.commit()


# ============================================================
# Utility Fixtures
# ============================================================

@pytest.fixture(scope="function")
def temp_log_dir():
    """임시 로그 디렉토리 (테스트용)"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    # cleanup
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)


# ============================================================
# 테스트 상수
# ============================================================

# 테스트 토픽
TEST_RAW_TOPIC = "test_ad_events_raw"
TEST_RETRY_TOPIC = "test_ad_events_retry"
TEST_DLQ_TOPIC = "test_ad_events_dlq"

# 테스트 설정
TEST_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
