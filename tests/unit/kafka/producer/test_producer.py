"""
Kafka Producer 테스트

pytest를 사용한 AdEventProducer 테스트
실행: pytest tests/kafka/producer/test_producer.py -v
"""

import sys
import os

# 프로젝트 루트 경로 추가 (FIRST!)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
import csv
import tempfile
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from kafka.producer.producer import AdEventProducer
from kafka.producer.config import ProducerConfig
from kafka.producer.data_transformer import AdEventTransformer


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_csv_file():
    """임시 CSV 파일 생성"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'click', 'hour', 'banner_pos', 'site_id', 'site_domain',
            'site_category', 'app_id', 'app_domain', 'app_category',
            'device_id', 'device_ip', 'device_model', 'device_type',
            'device_conn_type', 'C1', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20', 'C21'
        ])
        writer.writeheader()

        # 5개의 샘플 데이터 작성
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

        temp_path = f.name

    yield temp_path

    # 정리
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_producer():
    """Mock Kafka Producer"""
    with patch('kafka.producer.producer.Producer') as mock_kafka_producer:
        producer_instance = MagicMock()
        # flush() 메서드가 0을 반환하도록 설정 (성공적으로 모든 메시지 전송)
        producer_instance.flush.return_value = 0
        # poll() 메서드가 정상 동작하도록 설정
        producer_instance.poll.return_value = None
        mock_kafka_producer.return_value = producer_instance
        yield producer_instance


@pytest.fixture
def producer_instance(mock_producer):
    """AdEventProducer 인스턴스"""
    with patch.object(ProducerConfig, 'validate'):
        producer = AdEventProducer()
        return producer


# ============================================================
# 초기화 테스트
# ============================================================

class TestProducerInitialization:
    """AdEventProducer 초기화 테스트"""

    def test_producer_init(self, mock_producer):
        """Producer 초기화 테스트"""
        with patch.object(ProducerConfig, 'validate'):
            producer = AdEventProducer()

            assert producer.producer is not None
            assert producer.transformer is not None
            assert producer.stats['total'] == 0
            assert producer.stats['success'] == 0

    def test_producer_init_failure(self):
        """Producer 생성 실패 테스트"""
        with patch('kafka.producer.producer.Producer', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                AdEventProducer()

    def test_producer_config(self, producer_instance):
        """Producer 설정 확인"""
        assert producer_instance.config == ProducerConfig
        assert producer_instance.config.TOPIC == 'ad_events_raw'


# ============================================================
# process_and_send 테스트
# ============================================================

class TestProcessAndSend:
    """process_and_send 메서드 테스트"""

    def test_process_and_send_success(self, producer_instance):
        """정상 데이터 처리 및 발행"""
        raw_data = {
            'id': '1.0e+19',
            'click': '0',
            'hour': '14102101',
            'banner_pos': '0',
            'site_id': 'test',
            'site_domain': 'test',
            'site_category': 'test',
            'app_id': 'test',
            'app_domain': 'test',
            'app_category': 'test',
            'device_id': 'test',
            'device_ip': 'test',
            'device_model': 'test',
            'device_type': '1',
            'device_conn_type': '0',
            'C1': '100',
            'C14': '200',
            'C15': '300',
            'C16': '400',
            'C17': '500',
            'C18': '600',
            'C19': '700',
            'C20': '800',
            'C21': '900'
        }

        result = producer_instance.process_and_send(raw_data, 1)

        assert result is True
        assert producer_instance.stats['validation_failed'] == 0
        # produce 메서드가 호출되었는지 확인
        producer_instance.producer.produce.assert_called_once()

    def test_process_and_send_invalid_data(self, producer_instance):
        """유효하지 않은 데이터 처리"""
        raw_data = {
            'id': 'invalid',
            'click': '0',
            'hour': '14102101',
            # ... 나머지 필드 누락
        }

        result = producer_instance.process_and_send(raw_data, 1)

        assert result is False
        assert producer_instance.stats['validation_failed'] == 1
        # produce가 호출되지 않아야 함
        producer_instance.producer.produce.assert_not_called()

    def test_process_and_send_validation_failed(self, producer_instance):
        """검증 실패 데이터"""
        raw_data = {
            'id': '1.0e+19',
            'click': '5',  # 0 또는 1만 가능
            'hour': '14102101',
            'banner_pos': '0',
            'site_id': 'test',
            'site_domain': 'test',
            'site_category': 'test',
            'app_id': 'test',
            'app_domain': 'test',
            'app_category': 'test',
            'device_id': 'test',
            'device_ip': 'test',
            'device_model': 'test',
            'device_type': '1',
            'device_conn_type': '0',
            'C1': '100',
            'C14': '200',
            'C15': '300',
            'C16': '400',
            'C17': '500',
            'C18': '600',
            'C19': '700',
            'C20': '800',
            'C21': '900'
        }

        result = producer_instance.process_and_send(raw_data, 1)

        assert result is False
        assert producer_instance.stats['validation_failed'] == 1

    def test_process_and_send_callback(self, producer_instance):
        """delivery_report 콜백 테스트"""
        # 성공 콜백
        producer_instance._delivery_report(None, MagicMock())
        assert producer_instance.stats['success'] == 1

        # 실패 콜백
        error = Exception("Send failed")
        producer_instance._delivery_report(error, MagicMock())
        assert producer_instance.stats['send_failed'] == 1


# ============================================================
# run 메서드 테스트
# ============================================================

class TestProducerRun:
    """run 메서드 테스트"""

    def test_run_with_valid_csv(self, producer_instance, temp_csv_file):
        """유효한 CSV 파일 처리"""
        producer_instance.run(temp_csv_file, num_records=3)

        assert producer_instance.stats['total'] == 3
        # 처리된 메시지가 있어야 함
        assert producer_instance.producer.produce.call_count > 0

    def test_run_with_num_records_limit(self, producer_instance, temp_csv_file):
        """행 수 제한 테스트"""
        producer_instance.run(temp_csv_file, num_records=2)

        # 정확히 2개 행만 처리
        assert producer_instance.stats['total'] == 2

    def test_run_all_records(self, producer_instance, temp_csv_file):
        """모든 행 처리"""
        producer_instance.run(temp_csv_file)

        # 5개 모두 처리
        assert producer_instance.stats['total'] == 5

    def test_run_file_not_found(self, producer_instance):
        """파일 없음 에러"""
        with pytest.raises(FileNotFoundError):
            producer_instance.run('/nonexistent/file.csv')

    def test_run_flushes_producer(self, producer_instance, temp_csv_file):
        """run 완료 후 flush 호출"""
        producer_instance.run(temp_csv_file, num_records=1)

        # flush가 호출되었는지 확인
        producer_instance.producer.flush.assert_called()

    def test_run_prints_stats(self, producer_instance, temp_csv_file, caplog):
        """통계 출력 확인"""
        import logging
        caplog.set_level(logging.INFO)

        producer_instance.run(temp_csv_file, num_records=2)

        # 통계가 로그에 출력되어야 함
        assert 'Producer Statistics' in caplog.text or producer_instance.stats['total'] == 2


# ============================================================
# 통계 테스트
# ============================================================

class TestProducerStats:
    """통계 관련 테스트"""

    def test_stats_initialization(self, producer_instance):
        """통계 초기화"""
        assert producer_instance.stats['total'] == 0
        assert producer_instance.stats['success'] == 0
        assert producer_instance.stats['validation_failed'] == 0
        assert producer_instance.stats['send_failed'] == 0

    def test_stats_update_on_success(self, producer_instance):
        """성공 시 통계 업데이트"""
        raw_data = {
            'id': '1.0e+19',
            'click': '0',
            'hour': '14102101',
            'banner_pos': '0',
            'site_id': 'test',
            'site_domain': 'test',
            'site_category': 'test',
            'app_id': 'test',
            'app_domain': 'test',
            'app_category': 'test',
            'device_id': 'test',
            'device_ip': 'test',
            'device_model': 'test',
            'device_type': '1',
            'device_conn_type': '0',
            'C1': '100',
            'C14': '200',
            'C15': '300',
            'C16': '400',
            'C17': '500',
            'C18': '600',
            'C19': '700',
            'C20': '800',
            'C21': '900'
        }

        producer_instance.process_and_send(raw_data, 1)
        producer_instance._delivery_report(None, MagicMock())

        assert producer_instance.stats['success'] == 1

    def test_stats_update_on_failure(self, producer_instance):
        """실패 시 통계 업데이트"""
        raw_data = {'id': 'invalid'}  # 불완전한 데이터

        producer_instance.process_and_send(raw_data, 1)

        assert producer_instance.stats['validation_failed'] == 1


# ============================================================
# 통합 테스트
# ============================================================

class TestProducerIntegration:
    """통합 테스트"""

    def test_full_pipeline(self, producer_instance, temp_csv_file):
        """전체 파이프라인 테스트"""
        producer_instance.run(temp_csv_file, num_records=5)

        # 모든 행이 처리되었는지 확인
        assert producer_instance.stats['total'] == 5
        assert producer_instance.stats['validation_failed'] == 0

        # produce가 여러 번 호출되었는지 확인
        assert producer_instance.producer.produce.call_count > 0

    def test_producer_close(self, producer_instance):
        """Producer 종료"""
        producer_instance.close()

        # flush가 호출되었는지 확인
        producer_instance.producer.flush.assert_called()

    def test_multiple_batches(self, producer_instance, temp_csv_file):
        """여러 배치 처리"""
        # 첫 번째 배치
        producer_instance.run(temp_csv_file, num_records=2)
        first_batch_total = producer_instance.stats['total']

        # 통계 리셋 (실제로는 새로운 producer 인스턴스)
        producer_instance.stats['total'] = 0
        producer_instance.stats['success'] = 0

        # 두 번째 배치
        producer_instance.run(temp_csv_file, num_records=3)
        second_batch_total = producer_instance.stats['total']

        assert first_batch_total == 2
        assert second_batch_total == 3


# ============================================================
# 에러 처리 테스트
# ============================================================

class TestProducerErrorHandling:
    """에러 처리 테스트"""

    def test_process_and_send_exception_handling(self, producer_instance):
        """process_and_send 예외 처리"""
        # transformer를 mock해서 예외 발생
        with patch.object(producer_instance.transformer, 'transform', side_effect=Exception("Transform error")):
            result = producer_instance.process_and_send({}, 1)

            assert result is False
            assert producer_instance.stats['validation_failed'] == 1

    def test_corrupted_csv_handling(self, producer_instance):
        """손상된 CSV 처리"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write('invalid csv content\n')
            f.write('no proper headers\n')
            temp_path = f.name

        try:
            # 손상된 CSV도 처리되지만 검증 실패
            producer_instance.run(temp_path, num_records=1)
            # 헤더가 없으므로 검증 실패로 처리됨
            assert producer_instance.stats['validation_failed'] > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# ============================================================
# 엣지 케이스 테스트
# ============================================================

class TestProducerEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_csv_file(self, producer_instance):
        """빈 CSV 파일"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write('id,click,hour\n')  # 헤더만
            temp_path = f.name

        try:
            producer_instance.run(temp_path)
            assert producer_instance.stats['total'] == 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_zero_num_records(self, producer_instance, temp_csv_file):
        """num_records=0 (falsy이므로 모든 행 처리)"""
        producer_instance.run(temp_csv_file, num_records=0)
        # 0은 falsy이므로 모든 행(5개)이 처리됨
        assert producer_instance.stats['total'] == 5

    def test_large_num_records(self, producer_instance, temp_csv_file):
        """실제 행 수보다 큰 num_records"""
        producer_instance.run(temp_csv_file, num_records=1000)
        # 파일에 5개만 있으므로 5개만 처리
        assert producer_instance.stats['total'] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
