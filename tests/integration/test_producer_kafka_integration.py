"""
Integration 테스트: Producer - Kafka 연동

테스트:
- CSV 읽기 → Kafka 발행
- Kafka에서 메시지 수신 확인
- 배치 메시지 발행
"""

import pytest
import json
import csv
import tempfile
import os
from tests.integration.conftest import TEST_RAW_TOPIC


@pytest.mark.integration
class TestProducerKafkaIntegration:
    """Producer의 Kafka 연동 테스트"""

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
        """단일 메시지 Kafka 발행 및 수신"""
        test_message = {
            'id': 1.0e+19,
            'click': 0,
            'hour': 14102101,
            'banner_pos': 0,
            'site_id': 'test_site',
            'test_type': 'single_message'
        }

        # 1. 메시지 발행
        kafka_producer.send(TEST_RAW_TOPIC, test_message)
        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RAW_TOPIC])
        received_message = None

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'single_message':
                received_message = msg.value
                break

        # 3. 검증
        assert received_message is not None, "메시지를 수신하지 못했습니다"
        assert received_message['id'] == 1.0e+19
        assert received_message['click'] == 0
        assert received_message['site_id'] == 'test_site'

    def test_produce_batch_messages(self, kafka_producer, kafka_consumer):
        """배치 메시지 Kafka 발행 및 수신"""
        batch_size = 10

        # 1. 배치 메시지 발행
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
        assert len(received_messages) == batch_size, f"배치 크기 불일치: {len(received_messages)} != {batch_size}"

        # 각 메시지가 올바른 batch_id를 가지고 있는지 확인
        for i, msg in enumerate(received_messages):
            assert msg['batch_id'] == i
            assert msg['click'] == i % 2

    def test_produce_csv_data(self, kafka_producer, kafka_consumer, sample_csv_file):
        """CSV 파일 읽기 후 Kafka 발행"""
        # 1. CSV 파일 읽기 및 발행
        with open(sample_csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['test_type'] = 'csv_data'
                kafka_producer.send(TEST_RAW_TOPIC, row)

        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RAW_TOPIC])
        received_messages = []

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'csv_data':
                received_messages.append(msg.value)

            if len(received_messages) >= 5:
                break

        # 3. 검증
        assert len(received_messages) == 5, f"CSV 데이터 수신 실패: {len(received_messages)} != 5"

        # 첫 번째 메시지 필드 확인
        first_msg = received_messages[0]
        assert 'id' in first_msg
        assert 'click' in first_msg
        assert 'hour' in first_msg
        assert 'site_id' in first_msg
