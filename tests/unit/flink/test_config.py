# -*- coding: utf-8 -*-
"""
Flink 설정 테스트

설정 로드, 검증, 기본값 등을 테스트합니다.
"""

import pytest
import os
import sys
from pathlib import Path

# flink/src를 Python path에 추가
# tests/unit/flink/test_config.py 기준: ../../.. = 프로젝트 루트
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "flink" / "src"))

from config import FlinkConfig


class TestFlinkConfigKafka:
    """Kafka 설정 테스트"""

    def test_bootstrap_servers(self):
        """Kafka bootstrap servers 설정"""
        assert FlinkConfig.BOOTSTRAP_SERVERS == 'broker:29092'
        print(f"✅ Bootstrap servers: {FlinkConfig.BOOTSTRAP_SERVERS}")

    def test_kafka_topic(self):
        """Kafka 토픽 설정"""
        assert FlinkConfig.KAFKA_TOPIC_RAW == 'ad_events'
        print(f"✅ Kafka topic: {FlinkConfig.KAFKA_TOPIC_RAW}")

    def test_kafka_group_id(self):
        """Kafka consumer group ID"""
        assert FlinkConfig.KAFKA_GROUP_ID == 'flink-ctr-group'
        print(f"✅ Kafka group ID: {FlinkConfig.KAFKA_GROUP_ID}")

    def test_auto_offset_reset(self):
        """Kafka auto.offset.reset 설정"""
        assert FlinkConfig.KAFKA_AUTO_OFFSET_RESET == 'earliest'
        print(f"✅ Auto offset reset: {FlinkConfig.KAFKA_AUTO_OFFSET_RESET}")


class TestFlinkConfigSchemaRegistry:
    """Schema Registry 설정 테스트"""

    def test_schema_registry_url(self):
        """Schema Registry URL"""
        assert FlinkConfig.SCHEMA_REGISTRY_URL == 'http://schema-registry:8081'
        print(f"✅ Schema Registry URL: {FlinkConfig.SCHEMA_REGISTRY_URL}")

    def test_ad_event_schema_subject(self):
        """Ad Event 스키마 subject"""
        assert FlinkConfig.AD_EVENT_SCHEMA_SUBJECT == 'ad_events-value'
        print(f"✅ Ad Event schema subject: {FlinkConfig.AD_EVENT_SCHEMA_SUBJECT}")

    def test_ad_event_schema_file_exists(self):
        """Ad Event 스키마 파일이 존재하는지 확인"""
        schema_file = Path(FlinkConfig.AD_EVENT_SCHEMA_FILE)
        assert schema_file.exists(), f"Schema file not found: {schema_file}"
        print(f"✅ Ad Event schema file exists: {schema_file}")

    def test_ctr_metric_schema_file_exists(self):
        """CTR Metric 스키마 파일이 존재하는지 확인"""
        schema_file = Path(FlinkConfig.CTR_METRIC_SCHEMA_FILE)
        assert schema_file.exists(), f"Schema file not found: {schema_file}"
        print(f"✅ CTR Metric schema file exists: {schema_file}")


class TestFlinkConfigPostgreSQL:
    """PostgreSQL 설정 테스트"""

    def test_postgres_host(self):
        """PostgreSQL host"""
        assert FlinkConfig.POSTGRES_HOST == 'postgres'
        print(f"✅ PostgreSQL host: {FlinkConfig.POSTGRES_HOST}")

    def test_postgres_port(self):
        """PostgreSQL port"""
        assert FlinkConfig.POSTGRES_PORT == 5432
        print(f"✅ PostgreSQL port: {FlinkConfig.POSTGRES_PORT}")

    def test_postgres_db(self):
        """PostgreSQL database"""
        assert FlinkConfig.POSTGRES_DB == 'my-app-db'
        print(f"✅ PostgreSQL DB: {FlinkConfig.POSTGRES_DB}")

    def test_postgres_user(self):
        """PostgreSQL user"""
        assert FlinkConfig.POSTGRES_USER == 'admin'
        print(f"✅ PostgreSQL user: {FlinkConfig.POSTGRES_USER}")

    def test_postgres_jdbc_url(self):
        """PostgreSQL JDBC URL"""
        expected_url = 'jdbc:postgresql://postgres:5432/my-app-db'
        assert FlinkConfig.POSTGRES_JDBC_URL == expected_url
        print(f"✅ PostgreSQL JDBC URL: {FlinkConfig.POSTGRES_JDBC_URL}")

    def test_postgres_table_names(self):
        """PostgreSQL 테이블 이름들"""
        assert FlinkConfig.PG_TABLE_RAW_EVENTS == 'realtime.ad_events'
        assert FlinkConfig.PG_TABLE_METRICS_1MIN == 'realtime.ctr_metrics_1min'
        assert FlinkConfig.PG_TABLE_METRICS_5MIN == 'realtime.ctr_metrics_5min'
        print("✅ All PostgreSQL table names configured")


class TestFlinkConfigFlink:
    """Flink 실행 설정 테스트"""

    def test_parallelism(self):
        """병렬처리 수준"""
        assert FlinkConfig.PARALLELISM == 4
        print(f"✅ Parallelism: {FlinkConfig.PARALLELISM}")

    def test_checkpoint_interval(self):
        """Checkpoint 간격"""
        assert FlinkConfig.CHECKPOINT_INTERVAL == 60000  # 60초
        print(f"✅ Checkpoint interval: {FlinkConfig.CHECKPOINT_INTERVAL}ms")

    def test_checkpoint_timeout(self):
        """Checkpoint 타임아웃"""
        assert FlinkConfig.CHECKPOINT_TIMEOUT == 600000  # 10분
        print(f"✅ Checkpoint timeout: {FlinkConfig.CHECKPOINT_TIMEOUT}ms")

    def test_min_pause_between_checkpoints(self):
        """Checkpoint 최소 간격"""
        assert FlinkConfig.MIN_PAUSE_BETWEEN_CHECKPOINTS == 30000  # 30초
        print(f"✅ Min pause between checkpoints: {FlinkConfig.MIN_PAUSE_BETWEEN_CHECKPOINTS}ms")


class TestFlinkConfigWindowing:
    """Window 설정 테스트"""

    def test_window_size_1min(self):
        """1분 Window 크기"""
        assert FlinkConfig.WINDOW_SIZE_1MIN == 60000  # 60초
        print(f"✅ 1min window size: {FlinkConfig.WINDOW_SIZE_1MIN}ms")

    def test_window_size_5min(self):
        """5분 Window 크기"""
        assert FlinkConfig.WINDOW_SIZE_5MIN == 300000  # 300초
        print(f"✅ 5min window size: {FlinkConfig.WINDOW_SIZE_5MIN}ms")

    def test_watermark_delay(self):
        """Watermark 지연 시간"""
        assert FlinkConfig.WATERMARK_DELAY == 10000  # 10초
        print(f"✅ Watermark delay: {FlinkConfig.WATERMARK_DELAY}ms")


class TestFlinkConfigSink:
    """Sink 설정 테스트"""

    def test_batch_size(self):
        """배치 크기"""
        assert FlinkConfig.BATCH_SIZE == 1000
        print(f"✅ Batch size: {FlinkConfig.BATCH_SIZE}")

    def test_batch_interval_ms(self):
        """배치 간격"""
        assert FlinkConfig.BATCH_INTERVAL_MS == 5000  # 5초
        print(f"✅ Batch interval: {FlinkConfig.BATCH_INTERVAL_MS}ms")

    def test_max_retries(self):
        """최대 재시도 횟수"""
        assert FlinkConfig.MAX_RETRIES == 3
        print(f"✅ Max retries: {FlinkConfig.MAX_RETRIES}")


class TestFlinkConfigValidation:
    """설정 검증 테스트"""

    def test_validate_success(self):
        """설정 검증 성공"""
        result = FlinkConfig.validate()
        assert result is True
        print("✅ Configuration validation passed")

    def test_print_config(self, capsys):
        """설정 출력 (로깅)"""
        FlinkConfig.print_config()
        captured = capsys.readouterr()

        assert "FLINK CONFIGURATION" in captured.out
        assert "Kafka Broker" in captured.out
        assert "PostgreSQL" in captured.out
        print("✅ Configuration printed successfully")


class TestFlinkConfigIntegration:
    """통합 설정 테스트"""

    def test_all_required_configs_exist(self):
        """모든 필수 설정이 존재하는지 확인"""
        required_attributes = [
            'BOOTSTRAP_SERVERS',
            'KAFKA_TOPIC_RAW',
            'KAFKA_GROUP_ID',
            'SCHEMA_REGISTRY_URL',
            'POSTGRES_HOST',
            'POSTGRES_DB',
            'POSTGRES_USER',
            'PARALLELISM',
            'CHECKPOINT_INTERVAL',
            'WINDOW_SIZE_1MIN',
            'WINDOW_SIZE_5MIN',
        ]

        for attr in required_attributes:
            assert hasattr(FlinkConfig, attr), f"Missing config: {attr}"

        print(f"✅ All {len(required_attributes)} required configurations exist")

    def test_config_consistency(self):
        """설정의 일관성 확인"""
        # Window size는 양수여야 함
        assert FlinkConfig.WINDOW_SIZE_1MIN > 0
        assert FlinkConfig.WINDOW_SIZE_5MIN > 0
        assert FlinkConfig.WINDOW_SIZE_5MIN > FlinkConfig.WINDOW_SIZE_1MIN

        # Checkpoint 타임아웃은 간격보다 커야 함
        assert FlinkConfig.CHECKPOINT_TIMEOUT > FlinkConfig.CHECKPOINT_INTERVAL

        # 병렬처리 수준은 양수여야 함
        assert FlinkConfig.PARALLELISM > 0

        print("✅ Configuration consistency verified")
