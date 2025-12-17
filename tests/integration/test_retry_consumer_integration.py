"""
Integration 테스트: Retry Consumer

테스트:
- Retry Topic 메시지 수신
- 지수 백오프 재시도 (1초, 2초, 4초)
- 최대 재시도 초과 → DLQ 전송
"""

import pytest
import time
from datetime import datetime
from tests.integration.conftest import TEST_RETRY_TOPIC, TEST_DLQ_TOPIC


@pytest.mark.integration
class TestRetryConsumerIntegration:
    """Retry Consumer 테스트"""

    def test_receive_retry_message(self, kafka_producer, kafka_consumer):
        """Retry Topic 메시지 수신"""
        # 1. Retry 메시지 발행
        retry_message = {
            'id': 1.0e+19,
            'click': 0,
            'hour': 14102101,
            'retry_count': 1,
            'test_type': 'retry_receive_test'
        }

        kafka_producer.send(TEST_RETRY_TOPIC, retry_message)
        kafka_producer.flush()

        # 2. Retry 토픽에서 메시지 수신
        kafka_consumer.subscribe([TEST_RETRY_TOPIC])
        received_message = None

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'retry_receive_test':
                received_message = msg.value
                break

        # 3. 검증
        assert received_message is not None, "Retry 메시지를 수신하지 못했습니다"
        assert received_message['retry_count'] == 1
        assert received_message['id'] == 1.0e+19

    def test_multiple_retry_messages(self, kafka_producer, kafka_consumer):
        """여러 Retry 메시지 처리"""
        # 1. 여러 Retry 메시지 발행
        retry_count = 5
        for i in range(retry_count):
            retry_message = {
                'id': float(i),
                'click': i % 2,
                'hour': 14102101,
                'retry_count': 1,
                'attempt_number': 1,
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

            if len(received_messages) >= retry_count:
                break

            if time.time() - timeout_start > 10:
                break

        # 3. 검증
        assert len(received_messages) == retry_count, f"받은 메시지 수: {len(received_messages)} != {retry_count}"

    def test_exponential_backoff_timing(self, kafka_producer, kafka_consumer):
        """지수 백오프 타이밍 검증"""
        # 1. 재시도 정보가 포함된 메시지 발행
        backoff_timings = {
            0: 0,      # 첫 시도 (대기 없음)
            1: 1000,   # 첫 재시도 (1초)
            2: 2000,   # 두 번째 재시도 (2초)
            3: 4000,   # 세 번째 재시도 (4초)
        }

        for attempt in range(4):
            retry_message = {
                'id': 1.0e+19,
                'click': 0,
                'hour': 14102101,
                'retry_count': attempt,
                'attempt_number': attempt,
                'first_attempt_at': datetime.now().isoformat(),
                'last_retry_at': datetime.now().isoformat() if attempt > 0 else None,
                'expected_backoff_ms': backoff_timings[attempt],
                'test_type': 'backoff_timing_test'
            }

            kafka_producer.send(TEST_RETRY_TOPIC, retry_message)

        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RETRY_TOPIC])
        received_messages = []

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'backoff_timing_test':
                received_messages.append(msg.value)

            if len(received_messages) >= 4:
                break

        # 3. 백오프 타이밍 검증
        assert len(received_messages) == 4
        for msg in received_messages:
            attempt = msg['attempt_number']
            expected_backoff = backoff_timings[attempt]
            assert msg['expected_backoff_ms'] == expected_backoff

    def test_retry_message_format(self, kafka_producer, kafka_consumer):
        """Retry 메시지 형식 검증"""
        # 1. 정확한 형식의 메시지 발행
        retry_message = {
            'id': 2.0e+19,
            'click': 1,
            'hour': 14102101,
            'banner_pos': 0,
            'site_id': 'test_site',
            'retry_count': 1,
            'attempt_number': 1,
            'last_error': 'Connection timeout',
            'first_attempt_at': datetime.now().isoformat(),
            'test_type': 'format_validation_test'
        }

        kafka_producer.send(TEST_RETRY_TOPIC, retry_message)
        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RETRY_TOPIC])
        received_message = None

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'format_validation_test':
                received_message = msg.value
                break

        # 3. 필수 필드 검증
        required_fields = ['id', 'retry_count', 'attempt_number', 'last_error']
        for field in required_fields:
            assert field in received_message, f"필수 필드 '{field}' 없음"

        # 데이터 타입 검증
        assert isinstance(received_message['id'], (int, float))
        assert isinstance(received_message['retry_count'], int)
        assert isinstance(received_message['attempt_number'], int)
        assert isinstance(received_message['last_error'], str)

    def test_max_retries_exceeded_to_dlq(self, kafka_producer, kafka_consumer):
        """최대 재시도 초과 → DLQ 전송"""
        max_retries = 3

        # 1. 최대 재시도 횟수를 초과한 메시지를 DLQ로 전송
        dlq_message = {
            'original_message': {
                'id': 3.0e+19,
                'click': 1,
                'hour': 14102101
            },
            'reason': 'Max retries exceeded',
            'retry_count': max_retries,
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

        # 3. 검증
        assert received_message is not None, "DLQ 메시지를 수신하지 못했습니다"
        assert received_message['reason'] == 'Max retries exceeded'
        assert received_message['retry_count'] == max_retries

    def test_retry_to_raw_topic_on_success(self, kafka_producer, kafka_consumer):
        """재시도 성공 → raw topic으로 재전송"""
        from tests.integration.conftest import TEST_RAW_TOPIC

        # 1. 성공적으로 처리된 메시지를 raw topic으로 전송
        recovered_message = {
            'id': 4.0e+19,
            'click': 0,
            'hour': 14102101,
            'banner_pos': 2,
            'site_id': 'test_site',
            'was_retried': True,
            'retry_count': 2,
            'test_type': 'retry_recovery_test'
        }

        kafka_producer.send(TEST_RAW_TOPIC, recovered_message)
        kafka_producer.flush()

        # 2. raw topic에서 메시지 수신
        kafka_consumer.subscribe([TEST_RAW_TOPIC])
        received_message = None

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'retry_recovery_test':
                received_message = msg.value
                break

        # 3. 검증
        assert received_message is not None, "복구된 메시지를 수신하지 못했습니다"
        assert received_message['was_retried'] is True
        assert received_message['retry_count'] == 2

    def test_retry_counter_increment(self, kafka_producer, kafka_consumer):
        """재시도 횟수 증가 검증"""
        # 1. 증가하는 retry_count를 가진 메시지 발행
        for attempt in range(1, 4):
            retry_message = {
                'id': 5.0e+19,
                'click': 1,
                'hour': 14102101,
                'retry_count': attempt,
                'attempt_number': attempt,
                'test_type': 'retry_counter_test'
            }
            kafka_producer.send(TEST_RETRY_TOPIC, retry_message)

        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RETRY_TOPIC])
        received_messages = []

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'retry_counter_test':
                received_messages.append(msg.value)

            if len(received_messages) >= 3:
                break

        # 3. 검증 - retry_count가 증가하는지 확인
        assert len(received_messages) == 3
        for i, msg in enumerate(received_messages, 1):
            assert msg['retry_count'] == i, f"retry_count 불일치: {msg['retry_count']} != {i}"
            assert msg['attempt_number'] == i

    def test_retry_error_tracking(self, kafka_producer, kafka_consumer):
        """재시도 에러 추적"""
        # 1. 에러 정보가 포함된 Retry 메시지 발행
        retry_message = {
            'id': 6.0e+19,
            'click': 0,
            'hour': 14102101,
            'retry_count': 2,
            'attempt_number': 2,
            'last_error': 'Connection timeout',
            'error_history': [
                'Connection refused',
                'Connection timeout'
            ],
            'test_type': 'retry_error_tracking_test'
        }

        kafka_producer.send(TEST_RETRY_TOPIC, retry_message)
        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RETRY_TOPIC])
        received_message = None

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'retry_error_tracking_test':
                received_message = msg.value
                break

        # 3. 검증
        assert received_message is not None
        assert 'last_error' in received_message
        assert received_message['last_error'] == 'Connection timeout'
        assert 'error_history' in received_message
        assert len(received_message['error_history']) == 2
        assert received_message['error_history'][0] == 'Connection refused'
        assert received_message['error_history'][1] == 'Connection timeout'
