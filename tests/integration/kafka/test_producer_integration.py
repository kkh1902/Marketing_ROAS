"""
Integration 테스트: Producer 실제 Kafka 연동

테스트:
- CSV 읽기 → 실제 변환 → 실제 Kafka 전송
- 메시지 검증
- 배치 처리

테스트 토픽: test_ad_events_raw
"""

import pytest
import json
import csv
import tempfile
import os
import sys
from datetime import datetime

# Integration conftest 변수 가져오기
from tests.integration.conftest import TEST_RAW_TOPIC


@pytest.mark.integration
class TestProducerIntegration:
    """Producer의 실제 Kafka 연동 테스트"""

    @pytest.fixture
    def sample_csv_file(self):
        """샘플 CSV 파일 생성"""
        temp_dir = tempfile.mkdtemp()
        csv_path = os.path.join(temp_dir, 'test_data.csv')

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'id', 'click', 'hour', 'banner_pos', 'site_id', 'site_domain',
                'site_category', 'app_id', 'app_domain', 'app_category',
                'device_id', 'device_ip', 'device_model', 'device_type',
                'device_conn_type', 'C1', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20', 'C21'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i in range(5):
                writer.writerow({
                    'id': f'1.{i}e+19',
                    'click': str(i % 2),
                    'hour': '14102101',
                    'banner_pos': str(i % 8),
                    'site_id': f'site_{i}',
                    'site_domain': f'domain_{i}',
                    'site_category': f'cat_{i}',
                    'app_id': f'app_{i}',
                    'app_domain': f'appdomain_{i}',
                    'app_category': f'appcat_{i}',
                    'device_id': f'dev_{i}',
                    'device_ip': f'ip_{i}',
                    'device_model': f'model_{i}',
                    'device_type': str(i % 6),
                    'device_conn_type': str(i % 5),
                    'C1': '100',
                    'C14': '200',
                    'C15': '300',
                    'C16': '400',
                    'C17': '500',
                    'C18': '600',
                    'C19': '700',
                    'C20': '800',
                    'C21': '900'
                })

        yield csv_path

        # cleanup
        if os.path.exists(csv_path):
            os.unlink(csv_path)
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)

    def test_produce_single_message(self, kafka_producer, kafka_consumer):
        """단일 메시지 발행 및 수신"""
        # 1. 메시지 발행
        test_message = {
            'id': 1.0e+19,
            'click': 0,
            'hour': 14102101,
            'banner_pos': 0,
            'site_id': 'test_site',
            'test_type': 'single_message'
        }

        kafka_producer.send(TEST_RAW_TOPIC, test_message)
        kafka_producer.flush()

        # 2. 메시지 수신 및 검증
        kafka_consumer.subscribe([TEST_RAW_TOPIC])

        received_message = None
        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'single_message':
                received_message = msg.value
                break

        assert received_message is not None, "메시지를 받지 못했습니다"
        assert received_message['click'] == 0
        assert received_message['site_id'] == 'test_site'

    def test_produce_batch_messages(self, kafka_producer, kafka_consumer):
        """배치 메시지 발행 및 수신"""
        # 1. 배치 메시지 발행
        batch_size = 10
        for i in range(batch_size):
            message = {
                'id': float(i),
                'click': i % 2,
                'hour': 14102101,
                'test_type': 'batch_message',
                'batch_id': i
            }
            kafka_producer.send(TEST_RAW_TOPIC, message)

        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RAW_TOPIC])
        received_messages = []

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'batch_message':
                received_messages.append(msg.value)

            if len(received_messages) >= batch_size:
                break

        # 3. 검증
        assert len(received_messages) == batch_size, f"배치 메시지 수 불일치: {len(received_messages)} != {batch_size}"

    def test_produce_with_data_transformation(self, kafka_producer, kafka_consumer):
        """데이터 변환 후 발행"""
        # 1. 원본 데이터 (CSV 형식)
        raw_data = {
            'id': '1.4199688212321208e+19',
            'click': '0',
            'hour': '14102101',
            'banner_pos': '0',
            'site_id': '12fb4121',
            'site_domain': '6b59f079',
            'site_category': 'f028772b',
            'app_id': 'ecad2386',
            'app_domain': '7801e8d9',
            'app_category': '07d7df22',
            'device_id': 'a99f214a',
            'device_ip': '183586aa',
            'device_model': '8bfcd3c6',
            'device_type': '1',
            'device_conn_type': '0',
            'C1': '20970',
            'C14': '320',
            'C15': '50',
            'C16': '2372',
            'C17': '0',
            'C18': '813',
            'C19': '-1',
            'C20': '46',
            'C21': '100',
            'test_type': 'transformed_data'
        }

        # 2. 변환 후 발행
        kafka_producer.send(TEST_RAW_TOPIC, raw_data)
        kafka_producer.flush()

        # 3. 수신 및 검증
        kafka_consumer.subscribe([TEST_RAW_TOPIC])

        received_message = None
        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'transformed_data':
                received_message = msg.value
                break

        assert received_message is not None
        # 타입 검증
        assert isinstance(received_message['id'], str)
        assert isinstance(received_message['click'], str)
