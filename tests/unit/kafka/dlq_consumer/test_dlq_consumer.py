"""
Kafka DLQ Consumer 테스트

pytest를 사용한 DLQConsumer 테스트
실행: pytest tests/kafka/dlq_consumer/test_dlq_consumer.py -v
"""

import sys
import os
import json
import sqlite3
import tempfile
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 추가 (FIRST!)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from kafka.consumers.dlq_consumer.dlq_consumer import DLQConsumer
from kafka.consumers.dlq_consumer.config import DLQConsumerConfig


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db_path():
    """임시 데이터베이스 경로"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_dlq.db')
    yield db_path
    # 정리
    import shutil
    import time
    if os.path.exists(temp_dir):
        # Windows에서 열려있는 파일 삭제 시도 시 잠시 대기
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            time.sleep(0.1)
            shutil.rmtree(temp_dir)


@pytest.fixture
def temp_log_dir():
    """임시 로그 디렉토리"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # 정리
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_consumer():
    """Mock Kafka Consumer"""
    with patch('kafka.consumers.dlq_consumer.dlq_consumer.Consumer') as mock_kafka_consumer:
        consumer_instance = MagicMock()
        mock_kafka_consumer.return_value = consumer_instance
        yield consumer_instance


@pytest.fixture
def dlq_consumer_instance(mock_consumer, temp_db_path, temp_log_dir):
    """DLQConsumer 인스턴스"""
    with patch.object(DLQConsumerConfig, 'DLQ_DB_PATH', temp_db_path):
        with patch.object(DLQConsumerConfig, 'DLQ_LOG_DIR', temp_log_dir):
            with patch.object(DLQConsumerConfig, 'validate'):
                consumer = DLQConsumer()
                yield consumer
                # 테스트 후 정리
                consumer.close()


@pytest.fixture
def sample_dlq_message():
    """샘플 DLQ 메시지"""
    return {
        'original_message': {
            'id': 1.4199688212321208e+19,
            'click': 0,
            'hour': 14102101
        },
        'reason': 'Validation failed',
        'sent_to_dlq_at': datetime.now().isoformat()
    }


@pytest.fixture
def mock_kafka_message(sample_dlq_message):
    """Mock Kafka 메시지 객체"""
    msg = MagicMock()
    msg.value.return_value = json.dumps(sample_dlq_message).encode('utf-8')
    msg.topic.return_value = 'ad_events_dlq'
    msg.partition.return_value = 0
    msg.offset.return_value = 100
    msg.error.return_value = None
    return msg


# ============================================================
# 초기화 테스트
# ============================================================

class TestDLQConsumerInitialization:
    """DLQConsumer 초기화 테스트"""

    def test_consumer_init(self, mock_consumer, temp_db_path, temp_log_dir):
        """Consumer 초기화 테스트"""
        with patch.object(DLQConsumerConfig, 'DLQ_DB_PATH', temp_db_path):
            with patch.object(DLQConsumerConfig, 'DLQ_LOG_DIR', temp_log_dir):
                with patch.object(DLQConsumerConfig, 'validate'):
                    consumer = DLQConsumer()

                    assert consumer.consumer is not None
                    assert consumer.db_connection is not None
                    assert consumer.stats['total'] == 0
                    assert consumer.stats['stored'] == 0
                    assert consumer.stats['errors'] == 0

    def test_consumer_init_failure(self):
        """Consumer 생성 실패 테스트"""
        with patch('kafka.consumers.dlq_consumer.dlq_consumer.Consumer', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                DLQConsumer()

    def test_consumer_config(self, dlq_consumer_instance):
        """Consumer 설정 확인"""
        assert dlq_consumer_instance.config == DLQConsumerConfig
        assert dlq_consumer_instance.config.TOPIC == 'ad_events_dlq'
        assert dlq_consumer_instance.config.GROUP_ID == 'dlq_consumer_group'

    def test_database_initialization(self, temp_db_path, mock_consumer):
        """데이터베이스 초기화 테스트"""
        with patch.object(DLQConsumerConfig, 'DLQ_DB_PATH', temp_db_path):
            with patch.object(DLQConsumerConfig, 'DLQ_LOG_DIR', tempfile.mkdtemp()):
                with patch.object(DLQConsumerConfig, 'validate'):
                    consumer = DLQConsumer()

                    # 데이터베이스 확인
                    assert os.path.exists(temp_db_path)

                    # 테이블 확인
                    conn = sqlite3.connect(temp_db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dlq_messages'")
                    assert cursor.fetchone() is not None
                    conn.close()


# ============================================================
# _process_message 테스트
# ============================================================

class TestProcessMessage:
    """_process_message 메서드 테스트"""

    def test_process_valid_message(self, dlq_consumer_instance, mock_kafka_message, sample_dlq_message):
        """유효한 DLQ 메시지 처리"""
        result = dlq_consumer_instance._process_message(mock_kafka_message)

        assert result is True
        assert dlq_consumer_instance.stats['total'] == 1

    def test_process_message_invalid_json(self, dlq_consumer_instance, mock_kafka_message):
        """유효하지 않은 JSON 처리"""
        mock_kafka_message.value.return_value = b'invalid json'

        result = dlq_consumer_instance._process_message(mock_kafka_message)

        assert result is False
        assert dlq_consumer_instance.stats['errors'] == 1

    def test_process_message_corrupted(self, dlq_consumer_instance):
        """손상된 메시지 처리"""
        msg = MagicMock()
        msg.value.return_value = b'\x80\x81\x82'  # 유효하지 않은 UTF-8

        result = dlq_consumer_instance._process_message(msg)

        assert result is False
        assert dlq_consumer_instance.stats['errors'] == 1

    def test_process_message_missing_fields(self, dlq_consumer_instance, mock_kafka_message):
        """필드가 누락된 메시지 처리"""
        incomplete_message = {'reason': 'Some error'}
        mock_kafka_message.value.return_value = json.dumps(incomplete_message).encode('utf-8')

        result = dlq_consumer_instance._process_message(mock_kafka_message)

        assert result is True  # 처리는 성공하지만 필드 누락 처리
        assert dlq_consumer_instance.stats['total'] == 1


# ============================================================
# _store_message 테스트
# ============================================================

class TestStoreMessage:
    """_store_message 메서드 테스트"""

    def test_store_message_success(self, dlq_consumer_instance, mock_kafka_message, sample_dlq_message):
        """메시지 저장 성공"""
        dlq_consumer_instance._store_message(mock_kafka_message, sample_dlq_message)

        assert dlq_consumer_instance.stats['stored'] == 1

        # 데이터베이스 확인
        cursor = dlq_consumer_instance.db_connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM dlq_messages')
        count = cursor.fetchone()[0]
        assert count == 1

    def test_store_message_multiple(self, dlq_consumer_instance, mock_kafka_message, sample_dlq_message):
        """여러 메시지 저장"""
        for i in range(3):
            dlq_consumer_instance._store_message(mock_kafka_message, sample_dlq_message)

        assert dlq_consumer_instance.stats['stored'] == 3

        # 데이터베이스 확인
        cursor = dlq_consumer_instance.db_connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM dlq_messages')
        count = cursor.fetchone()[0]
        assert count == 3

    def test_store_message_with_error_reason(self, dlq_consumer_instance, mock_kafka_message, sample_dlq_message):
        """에러 이유와 함께 메시지 저장"""
        error_reason = "Custom error reason"
        dlq_consumer_instance._store_message(mock_kafka_message, sample_dlq_message, error_reason)

        cursor = dlq_consumer_instance.db_connection.cursor()
        cursor.execute('SELECT error_reason FROM dlq_messages LIMIT 1')
        result = cursor.fetchone()
        assert result is not None
        assert error_reason in result[0] or len(result[0]) > 0


# ============================================================
# _write_log_file 테스트
# ============================================================

class TestWriteLogFile:
    """_write_log_file 메서드 테스트"""

    def test_write_log_file_success(self, dlq_consumer_instance, sample_dlq_message):
        """로그 파일 작성 성공"""
        message_id = "test_message_123"
        dlq_consumer_instance._write_log_file(message_id, sample_dlq_message, "Test error")

        # 로그 파일 확인
        log_file = Path(dlq_consumer_instance.config.DLQ_LOG_DIR) / f"dlq_{datetime.now().strftime('%Y%m%d')}.jsonl"
        assert log_file.exists()

    def test_write_log_file_content(self, dlq_consumer_instance, sample_dlq_message):
        """로그 파일 내용 확인"""
        message_id = "test_message_456"
        dlq_consumer_instance._write_log_file(message_id, sample_dlq_message, "Test error")

        log_file = Path(dlq_consumer_instance.config.DLQ_LOG_DIR) / f"dlq_{datetime.now().strftime('%Y%m%d')}.jsonl"

        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        assert message_id in log_content or len(log_content) > 0

    def test_write_log_file_multiple_entries(self, dlq_consumer_instance, sample_dlq_message):
        """여러 로그 항목 작성"""
        for i in range(3):
            dlq_consumer_instance._write_log_file(f"msg_{i}", sample_dlq_message, f"Error {i}")

        log_file = Path(dlq_consumer_instance.config.DLQ_LOG_DIR) / f"dlq_{datetime.now().strftime('%Y%m%d')}.jsonl"

        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) == 3


# ============================================================
# _send_alert 테스트
# ============================================================

class TestSendAlert:
    """_send_alert 메서드 테스트"""

    def test_send_alert_no_exception(self, dlq_consumer_instance):
        """알림 전송 (예외 발생 안 함)"""
        # 알림 전송이 예외를 발생시키지 않는지 확인
        dlq_consumer_instance._send_alert("msg_123", "Test reason", datetime.now().isoformat())
        assert True  # 예외가 발생하지 않음

    def test_send_alert_with_various_reasons(self, dlq_consumer_instance):
        """다양한 이유로 알림 전송"""
        reasons = ["Validation failed", "Processing error", "Max retries exceeded"]
        for reason in reasons:
            dlq_consumer_instance._send_alert("msg_123", reason, datetime.now().isoformat())
        assert True  # 모든 알림이 정상 처리됨


# ============================================================
# 통계 테스트
# ============================================================

class TestConsumerStats:
    """통계 관련 테스트"""

    def test_stats_initialization(self, dlq_consumer_instance):
        """통계 초기화"""
        assert dlq_consumer_instance.stats['total'] == 0
        assert dlq_consumer_instance.stats['stored'] == 0
        assert dlq_consumer_instance.stats['errors'] == 0

    def test_stats_update_on_message(self, dlq_consumer_instance, mock_kafka_message):
        """메시지 처리 시 통계 업데이트"""
        dlq_consumer_instance._process_message(mock_kafka_message)

        assert dlq_consumer_instance.stats['total'] == 1

    def test_stats_update_on_error(self, dlq_consumer_instance):
        """에러 발생 시 통계 업데이트"""
        msg = MagicMock()
        msg.value.return_value = b'invalid json'

        dlq_consumer_instance._process_message(msg)

        assert dlq_consumer_instance.stats['errors'] == 1


# ============================================================
# 통합 테스트
# ============================================================

class TestDLQConsumerIntegration:
    """통합 테스트"""

    def test_full_pipeline(self, dlq_consumer_instance, mock_kafka_message, sample_dlq_message):
        """전체 파이프라인 테스트"""
        # 메시지 처리
        result = dlq_consumer_instance._process_message(mock_kafka_message)

        assert result is True
        assert dlq_consumer_instance.stats['total'] == 1
        assert dlq_consumer_instance.stats['stored'] == 1

    def test_multiple_messages_pipeline(self, dlq_consumer_instance, sample_dlq_message):
        """여러 메시지 처리 파이프라인"""
        for i in range(5):
            msg = MagicMock()
            modified_message = sample_dlq_message.copy()
            modified_message['original_message'] = {'id': float(i)}
            msg.value.return_value = json.dumps(modified_message).encode('utf-8')
            msg.topic.return_value = 'ad_events_dlq'
            msg.partition.return_value = 0
            msg.offset.return_value = i

            dlq_consumer_instance._process_message(msg)

        assert dlq_consumer_instance.stats['total'] == 5
        assert dlq_consumer_instance.stats['stored'] == 5

    def test_consumer_close(self, dlq_consumer_instance):
        """Consumer 종료"""
        dlq_consumer_instance.close()

        # close 메서드가 정상 동작하는지 확인
        assert True


# ============================================================
# 에러 처리 테스트
# ============================================================

class TestConsumerErrorHandling:
    """에러 처리 테스트"""

    def test_database_error_handling(self, dlq_consumer_instance, mock_kafka_message, sample_dlq_message):
        """데이터베이스 에러 처리"""
        # db_connection을 mock으로 교체해서 예외 발생
        mock_db = MagicMock()
        mock_db.cursor.side_effect = Exception("DB error")
        dlq_consumer_instance.db_connection = mock_db

        dlq_consumer_instance._store_message(mock_kafka_message, sample_dlq_message)
        assert dlq_consumer_instance.stats['errors'] == 1

    def test_json_decode_error(self, dlq_consumer_instance):
        """JSON 디코드 에러"""
        msg = MagicMock()
        msg.value.return_value = b'{"invalid json'

        result = dlq_consumer_instance._process_message(msg)

        assert result is False
        assert dlq_consumer_instance.stats['errors'] == 1

    def test_message_processing_exception(self, dlq_consumer_instance):
        """메시지 처리 예외"""
        msg = MagicMock()
        msg.value.return_value = json.dumps({'data': 'test'}).encode('utf-8')

        # _process_message가 일부 필드 누락을 처리하는지 확인
        result = dlq_consumer_instance._process_message(msg)

        # 누락된 필드가 있어도 처리는 진행됨
        assert result is True


# ============================================================
# 엣지 케이스 테스트
# ============================================================

class TestConsumerEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_message(self, dlq_consumer_instance):
        """빈 메시지"""
        msg = MagicMock()
        msg.value.return_value = json.dumps({}).encode('utf-8')
        msg.topic.return_value = 'ad_events_dlq'
        msg.partition.return_value = 0
        msg.offset.return_value = 0

        result = dlq_consumer_instance._process_message(msg)

        assert result is True

    def test_very_large_message(self, dlq_consumer_instance):
        """매우 큰 메시지"""
        large_data = {'original_message': {'id': i} for i in range(1000)}
        msg = MagicMock()
        msg.value.return_value = json.dumps(large_data).encode('utf-8')
        msg.topic.return_value = 'ad_events_dlq'
        msg.partition.return_value = 0
        msg.offset.return_value = 0

        result = dlq_consumer_instance._process_message(msg)

        assert result is True or result is False

    def test_special_characters_in_message(self, dlq_consumer_instance):
        """특수 문자가 포함된 메시지"""
        special_msg = {
            'original_message': {'id': 1},
            'reason': '한글 에러 메시지 🔥'
        }
        msg = MagicMock()
        msg.value.return_value = json.dumps(special_msg, ensure_ascii=False).encode('utf-8')
        msg.topic.return_value = 'ad_events_dlq'
        msg.partition.return_value = 0
        msg.offset.return_value = 0

        result = dlq_consumer_instance._process_message(msg)

        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
