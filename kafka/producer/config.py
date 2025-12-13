"""
Kafka Producer Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()


class ProducerConfig:
    """Kafka Producer Configuration"""

    # Kafka Broker
    BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    TOPIC = os.getenv('KAFKA_TOPIC', 'ad_events_raw')

    # Schema Registry
    SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL', 'http://localhost:8081')
    SCHEMA_SUBJECT = f'{TOPIC}-value'

    # Producer Settings
    CLIENT_ID = os.getenv('PRODUCER_CLIENT_ID', 'ad_event_producer')
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 16384))
    LINGER_MS = int(os.getenv('LINGER_MS', 10))
    COMPRESSION_TYPE = os.getenv('COMPRESSION_TYPE', 'snappy')
    ACKS = os.getenv('ACKS', 'all')
    RETRIES = int(os.getenv('RETRIES', 3))
    RETRY_BACKOFF_MS = int(os.getenv('RETRY_BACKOFF_MS', 100))
    REQUEST_TIMEOUT_MS = int(os.getenv('REQUEST_TIMEOUT_MS', 30000))

    # Data Settings
    CSV_FILE_PATH = os.getenv(
        'CSV_FILE_PATH',
        'data/sample/train_sample_1k.csv'
    )
    BATCH_LIMIT = int(os.getenv('BATCH_LIMIT', 0))

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def get_producer_config(cls) -> dict:
        """Get producer configuration dict"""
        return {
            'bootstrap.servers': cls.BOOTSTRAP_SERVERS,
            'client.id': cls.CLIENT_ID,
            'acks': cls.ACKS,
            'retries': cls.RETRIES,
            'retry.backoff.ms': cls.RETRY_BACKOFF_MS,
            'batch.size': cls.BATCH_SIZE,
            'linger.ms': cls.LINGER_MS,
            'compression.type': cls.COMPRESSION_TYPE,
            'request.timeout.ms': cls.REQUEST_TIMEOUT_MS,
            'enable.idempotence': True,
        }

    @classmethod
    def validate(cls):
        """Validate configuration"""
        import os

        print("=" * 60)
        print("Kafka Producer Configuration")
        print("=" * 60)
        print(f"Bootstrap Servers: {cls.BOOTSTRAP_SERVERS}")
        print(f"Topic: {cls.TOPIC}")
        print(f"Schema Registry: {cls.SCHEMA_REGISTRY_URL}")
        print(f"CSV File: {cls.CSV_FILE_PATH}")
        print("=" * 60)

        if not os.path.exists(cls.CSV_FILE_PATH):
            raise FileNotFoundError(f"CSV file not found: {cls.CSV_FILE_PATH}")

        print("Configuration validated successfully")
        return True
