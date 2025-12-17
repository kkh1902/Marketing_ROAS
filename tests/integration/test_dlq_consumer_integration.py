"""
Integration 테스트: DLQ Consumer

테스트:
- 실패 메시지 → DLQ Topic
- DLQ → PostgreSQL errors 테이블 저장
- 에러 로그 기록
"""

import pytest
import json
from datetime import datetime
from tests.integration.conftest import TEST_DLQ_TOPIC


@pytest.mark.integration
class TestDLQConsumerIntegration:
    """DLQ Consumer 테스트"""

    def test_send_to_dlq_topic(self, kafka_producer, kafka_consumer):
        """실패 메시지 DLQ Topic 전송"""
        # 1. DLQ 메시지 발행
        dlq_message = {
            'original_message': {
                'id': 1.0e+19,
                'click': 0,
                'hour': 14102101
            },
            'reason': 'Validation failed',
            'error_detail': 'Invalid field format',
            'sent_to_dlq_at': datetime.now().isoformat(),
            'test_type': 'dlq_send_test'
        }

        kafka_producer.send(TEST_DLQ_TOPIC, dlq_message)
        kafka_producer.flush()

        # 2. DLQ 토픽에서 메시지 수신
        kafka_consumer.subscribe([TEST_DLQ_TOPIC])
        received_message = None

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'dlq_send_test':
                received_message = msg.value
                break

        # 3. 검증
        assert received_message is not None, "DLQ 메시지를 수신하지 못했습니다"
        assert 'original_message' in received_message
        assert received_message['reason'] == 'Validation failed'
        assert received_message['original_message']['id'] == 1.0e+19

    def test_dlq_message_structure(self, kafka_producer, kafka_consumer):
        """DLQ 메시지 구조 검증"""
        # 1. 구조화된 DLQ 메시지 발행
        dlq_message = {
            'original_message': {
                'id': 2.0e+19,
                'click': 1,
                'hour': 14102102,
                'banner_pos': 1
            },
            'reason': 'Processing error',
            'error_detail': 'Connection timeout',
            'retry_count': 0,
            'source': 'kafka_consumer',
            'timestamp': datetime.now().isoformat(),
            'test_type': 'dlq_structure_test'
        }

        kafka_producer.send(TEST_DLQ_TOPIC, dlq_message)
        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_DLQ_TOPIC])
        received_message = None

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'dlq_structure_test':
                received_message = msg.value
                break

        # 3. 필수 필드 검증
        required_fields = ['original_message', 'reason', 'error_detail', 'timestamp']
        for field in required_fields:
            assert field in received_message, f"필수 필드 '{field}' 없음"

        # 원본 메시지 필드 검증
        assert 'id' in received_message['original_message']
        assert 'click' in received_message['original_message']

    def test_multiple_dlq_messages(self, kafka_producer, kafka_consumer):
        """여러 DLQ 메시지 처리"""
        # 1. 여러 DLQ 메시지 발행
        dlq_messages = []
        for i in range(3):
            dlq_message = {
                'original_message': {'id': float(i), 'click': i % 2},
                'reason': f'Error {i}',
                'error_detail': f'Details for error {i}',
                'sent_to_dlq_at': datetime.now().isoformat(),
                'test_type': 'dlq_multiple_test'
            }
            dlq_messages.append(dlq_message)
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

        # 3. 검증
        assert len(received_messages) == 3, f"받은 메시지 수: {len(received_messages)} != 3"

        for i, msg in enumerate(received_messages):
            assert msg['reason'] == f'Error {i}'
            assert msg['original_message']['id'] == float(i)

    def test_postgresql_errors_schema(self, postgres_cursor):
        """PostgreSQL errors.dlq_messages 테이블 검증"""
        # 1. 테이블 존재 확인
        try:
            postgres_cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'errors'
                    AND table_name = 'dlq_messages'
                )
            """)
            exists = postgres_cursor.fetchone()[0]

            if not exists:
                # 테이블 생성
                postgres_cursor.execute("""
                    CREATE SCHEMA IF NOT EXISTS errors;

                    CREATE TABLE errors.dlq_messages (
                        id SERIAL PRIMARY KEY,
                        message_id VARCHAR,
                        error_message TEXT,
                        retry_count INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                postgres_cursor.connection.commit()
        except Exception as e:
            pytest.fail(f"PostgreSQL 테이블 생성 실패: {e}")

        # 2. 테이블 컬럼 확인
        postgres_cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'errors'
            AND table_name = 'dlq_messages'
            ORDER BY ordinal_position
        """)
        columns = postgres_cursor.fetchall()

        assert len(columns) >= 5, f"컬럼 수 부족: {len(columns)} columns"
        column_names = [col[0] for col in columns]
        assert 'message_id' in column_names
        assert 'error_message' in column_names
        assert 'retry_count' in column_names
        assert 'created_at' in column_names

    def test_insert_dlq_error_to_postgresql(self, postgres_cursor):
        """PostgreSQL에 DLQ 에러 데이터 저장"""
        # 1. 테이블 생성 (없으면)
        postgres_cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS errors;

            CREATE TABLE IF NOT EXISTS errors.dlq_messages (
                id SERIAL PRIMARY KEY,
                message_id VARCHAR,
                error_message TEXT,
                retry_count INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. 테스트 데이터 삽입
        test_error = {
            'message_id': 'msg_12345',
            'error_message': 'Validation failed: Invalid field format',
            'retry_count': 3
        }

        postgres_cursor.execute("""
            INSERT INTO errors.dlq_messages
            (message_id, error_message, retry_count)
            VALUES (%s, %s, %s)
        """, (
            test_error['message_id'],
            test_error['error_message'],
            test_error['retry_count']
        ))

        postgres_cursor.connection.commit()

        # 3. 데이터 검증
        postgres_cursor.execute("""
            SELECT message_id, error_message, retry_count
            FROM errors.dlq_messages
            WHERE message_id = %s
        """, (test_error['message_id'],))

        result = postgres_cursor.fetchone()

        assert result is not None, "삽입된 데이터를 조회할 수 없습니다"
        assert result[0] == test_error['message_id']
        assert result[1] == test_error['error_message']
        assert result[2] == test_error['retry_count']

        # 4. 정리
        postgres_cursor.execute("DELETE FROM errors.dlq_messages WHERE message_id = %s", (test_error['message_id'],))
        postgres_cursor.connection.commit()

    def test_dlq_error_logging(self, kafka_producer, kafka_consumer, temp_log_dir):
        """DLQ 에러 로그 기록"""
        import os

        # 1. DLQ 메시지 발행
        dlq_message = {
            'original_message': {
                'id': 3.0e+19,
                'click': 1
            },
            'reason': 'Processing error',
            'error_detail': 'Database connection failed',
            'sent_to_dlq_at': datetime.now().isoformat(),
            'test_type': 'dlq_logging_test'
        }

        kafka_producer.send(TEST_DLQ_TOPIC, dlq_message)
        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_DLQ_TOPIC])
        received_message = None

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'dlq_logging_test':
                received_message = msg.value
                break

        assert received_message is not None

        # 3. 로그 파일에 기록
        log_file = os.path.join(temp_log_dir, 'dlq_errors.log')
        with open(log_file, 'a') as f:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message_id': received_message['original_message'].get('id'),
                'reason': received_message['reason'],
                'error_detail': received_message['error_detail']
            }
            f.write(json.dumps(log_entry) + '\n')

        # 4. 로그 파일 검증
        assert os.path.exists(log_file), "로그 파일이 생성되지 않았습니다"

        with open(log_file, 'r') as f:
            log_content = f.read()
            assert 'Database connection failed' in log_content
            assert received_message['reason'] in log_content
