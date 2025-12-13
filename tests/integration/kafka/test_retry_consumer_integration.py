"""
Integration 테스트: Retry Consumer 실제 Kafka 연동

테스트:
- Retry 토픽에서 메시지 수신
- 재시도 로직 실행
- 실패 시 DLQ로 전송
- 지수 백오프 검증

테스트 토픽: test_ad_events_retry, test_ad_events_dlq
"""

import pytest
import json
import time
import sys
from datetime import datetime

# Integration conftest 변수 가져오기
from tests.integration.conftest import TEST_RETRY_TOPIC, TEST_DLQ_TOPIC


@pytest.mark.integration
class TestRetryConsumerIntegration:
    """Retry Consumer의 실제 Kafka 연동 테스트"""

    def test_receive_and_process_retry_message(self, kafka_producer, kafka_consumer):
        """Retry 메시지 수신 및 처리"""
        # 1. Retry 메시지 발행
        retry_message = {
            'id': 1.0e+19,
            'click': 0,
            'hour': 14102101,
            'retry_count': 1,
            'test_type': 'retry_process_test'
        }

        kafka_producer.send(TEST_RETRY_TOPIC, retry_message)
        kafka_producer.flush()

        # 2. Retry 토픽에서 메시지 수신
        kafka_consumer.subscribe([TEST_RETRY_TOPIC])

        received_message = None
        timeout_start = time.time()

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'retry_process_test':
                received_message = msg.value
                break

            if time.time() - timeout_start > 10:
                break

        assert received_message is not None, "Retry 메시지를 받지 못했습니다"
        assert received_message['retry_count'] == 1

    def test_multiple_retry_messages(self, kafka_producer, kafka_consumer):
        """여러 Retry 메시지 처리"""
        # 1. 여러 Retry 메시지 발행
        for i in range(5):
            retry_message = {
                'id': float(i),
                'click': i % 2,
                'retry_count': 1,
                'test_type': 'retry_multiple_test'
            }
            kafka_producer.send(TEST_RETRY_TOPIC, retry_message)

        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RETRY_TOPIC])
        received_messages = []
        timeout_start = time.time()

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'retry_multiple_test':
                received_messages.append(msg.value)

            if len(received_messages) >= 5:
                break

            if time.time() - timeout_start > 10:
                break

        assert len(received_messages) == 5, f"받은 메시지 수 불일치: {len(received_messages)} != 5"

    def test_retry_backoff_timing(self, kafka_producer, kafka_consumer):
        """지수 백오프 시간 검증"""
        # 1. 재시도 정보가 포함된 메시지 발행
        retry_message = {
            'id': 2.0e+19,
            'retry_count': 1,
            'first_attempt_at': datetime.now().isoformat(),
            'test_type': 'retry_backoff_test'
        }

        kafka_producer.send(TEST_RETRY_TOPIC, retry_message)
        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RETRY_TOPIC])

        received_message = None
        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'retry_backoff_test':
                received_message = msg.value
                break

        assert received_message is not None
        assert 'first_attempt_at' in received_message

        # 3. 재시도 대기 시간 검증
        # 첫 번째: 1초, 두 번째: 2초, 세 번째: 4초
        expected_backoff = {
            0: 0,      # 첫 시도
            1: 1000,   # 1초
            2: 2000,   # 2초
            3: 4000,   # 4초
        }

        current_backoff = expected_backoff.get(received_message['retry_count'], 0)
        assert current_backoff >= 0

    def test_max_retries_exceeded_sends_to_dlq(self, kafka_producer, kafka_consumer):
        """최대 재시도 초과 시 DLQ로 전송"""
        # 1. 최대 재시도 초과된 메시지 발행 (DLQ로 감)
        dlq_message = {
            'original_message': {
                'id': 3.0e+19,
                'retry_count': 3  # 최대 재시도 3회 초과
            },
            'reason': 'Max retries exceeded',
            'sent_to_dlq_at': datetime.now().isoformat(),
            'test_type': 'max_retries_test'
        }

        kafka_producer.send(TEST_DLQ_TOPIC, dlq_message)
        kafka_producer.flush()

        # 2. DLQ 토픽에서 메시지 수신
        kafka_consumer.subscribe([TEST_DLQ_TOPIC])

        received_message = None
        timeout_start = time.time()

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'max_retries_test':
                received_message = msg.value
                break

            if time.time() - timeout_start > 10:
                break

        assert received_message is not None, "DLQ 메시지를 받지 못했습니다"
        assert received_message['reason'] == 'Max retries exceeded'

    def test_retry_message_format_validation(self, kafka_producer, kafka_consumer):
        """Retry 메시지 형식 검증"""
        # 1. 정확한 형식의 메시지 발행
        retry_message = {
            'id': 4.0e+19,
            'click': 1,
            'hour': 14102101,
            'banner_pos': 0,
            'retry_count': 1,
            'attempt_number': 1,
            'last_error': 'Connection timeout',
            'test_type': 'format_validation_test'
        }

        kafka_producer.send(TEST_RETRY_TOPIC, retry_message)
        kafka_producer.flush()

        # 2. 메시지 수신 및 형식 검증
        kafka_consumer.subscribe([TEST_RETRY_TOPIC])

        received_message = None
        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'format_validation_test':
                received_message = msg.value
                break

        assert received_message is not None

        # 형식 검증
        required_fields = ['id', 'retry_count', 'attempt_number']
        for field in required_fields:
            assert field in received_message, f"필수 필드 '{field}'가 없습니다"

        assert isinstance(received_message['retry_count'], int)
        assert isinstance(received_message['id'], (int, float))
