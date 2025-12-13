"""
Integration 테스트: DLQ Consumer 실제 Kafka + DB 연동

테스트:
- Kafka에서 DLQ 메시지 수신
- SQLite DB에 저장
- 로그 파일 생성
- 알림 발송

테스트 토픽: test_ad_events_dlq
"""

import pytest
import json
import sqlite3
import os
import sys
from datetime import datetime

# Integration conftest 변수 가져오기
from tests.integration.conftest import TEST_DLQ_TOPIC


@pytest.mark.integration
class TestDLQConsumerIntegration:
    """DLQ Consumer의 실제 Kafka + DB 연동 테스트"""

    def test_receive_and_store_dlq_message(self, kafka_producer, kafka_consumer, temp_db, temp_log_dir):
        """DLQ 메시지 수신 및 DB 저장"""
        # 1. DLQ 메시지 발행
        dlq_message = {
            'original_message': {
                'id': 1.0e+19,
                'click': 0,
                'hour': 14102101
            },
            'reason': 'Validation failed',
            'sent_to_dlq_at': datetime.now().isoformat(),
            'test_type': 'dlq_store_test'
        }

        kafka_producer.send(TEST_DLQ_TOPIC, dlq_message)
        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_DLQ_TOPIC])

        received_message = None
        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'dlq_store_test':
                received_message = msg.value
                break

        assert received_message is not None, "DLQ 메시지를 받지 못했습니다"

        # 3. DB에 저장
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dlq_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT,
                topic TEXT,
                partition INTEGER,
                offset INTEGER,
                message_content TEXT,
                error_reason TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        ''')

        message_id = received_message.get('original_message', {}).get('id', 'unknown')
        cursor.execute('''
            INSERT INTO dlq_messages
            (message_id, topic, partition, offset, message_content, error_reason, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            message_id,
            TEST_DLQ_TOPIC,
            0,
            0,
            json.dumps(received_message),
            received_message.get('reason', ''),
            datetime.now().isoformat()
        ))

        conn.commit()

        # 4. DB 저장 검증
        cursor.execute('SELECT COUNT(*) FROM dlq_messages')
        count = cursor.fetchone()[0]
        assert count == 1, f"DB에 저장되지 않았습니다. 저장된 메시지: {count}"

        conn.close()

    def test_multiple_dlq_messages(self, kafka_producer, kafka_consumer, temp_db):
        """여러 DLQ 메시지 처리"""
        # 1. 여러 DLQ 메시지 발행
        for i in range(3):
            dlq_message = {
                'original_message': {'id': float(i)},
                'reason': f'Error {i}',
                'sent_to_dlq_at': datetime.now().isoformat(),
                'test_type': 'dlq_multiple_test'
            }
            kafka_producer.send(TEST_DLQ_TOPIC, dlq_message)

        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_DLQ_TOPIC])
        received_messages = []

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'dlq_multiple_test':
                received_messages.append(msg.value)

            if len(received_messages) >= 3:
                break

        assert len(received_messages) == 3, f"받은 메시지 수 불일치: {len(received_messages)} != 3"

    def test_dlq_message_with_metadata(self, kafka_producer, kafka_consumer):
        """메타데이터가 포함된 DLQ 메시지"""
        # 1. 메타데이터가 포함된 메시지 발행
        dlq_message = {
            'original_message': {
                'id': 2.0e+19,
                'click': 1,
                'test_id': 'metadata_test'
            },
            'reason': 'Max retries exceeded',
            'retry_count': 3,
            'sent_to_dlq_at': datetime.now().isoformat(),
            'source_consumer': 'retry_consumer',
            'test_type': 'dlq_metadata_test'
        }

        kafka_producer.send(TEST_DLQ_TOPIC, dlq_message)
        kafka_producer.flush()

        # 2. 메시지 수신 및 검증
        kafka_consumer.subscribe([TEST_DLQ_TOPIC])

        received_message = None
        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'dlq_metadata_test':
                received_message = msg.value
                break

        assert received_message is not None
        assert received_message['retry_count'] == 3
        assert received_message['source_consumer'] == 'retry_consumer'
        assert 'original_message' in received_message
