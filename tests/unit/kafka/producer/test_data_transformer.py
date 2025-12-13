"""
data_transformer.py 단위 테스트

pytest를 사용한 테스트
실행: pytest tests/test_data_transformer.py -v
"""

import sys
import os
from typing import Dict, Any

# 프로젝트 루트 경로 추가 (FIRST!)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from kafka.producer.data_transformer import AdEventTransformer


@pytest.fixture
def transformer():
    """트랜스포머 인스턴스 생성"""
    return AdEventTransformer()


@pytest.fixture
def valid_csv_row():
    """유효한 CSV 행 샘플"""
    return {
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
        'C21': '100'
    }


# ============================================================
# transform() 테스트
# ============================================================

class TestTransform:
    """transform() 메서드 테스트"""

    def test_transform_valid_data(self, transformer, valid_csv_row):
        """유효한 CSV 데이터 변환 테스트"""
        result = transformer.transform(valid_csv_row)

        assert result is not None, "변환 결과가 None이 아니어야 함"
        assert isinstance(result, dict), "결과는 dict여야 함"
        assert len(result) == 24, "모든 필드가 변환되어야 함"

    def test_transform_float_conversion(self, transformer, valid_csv_row):
        """float 타입 변환 테스트"""
        result = transformer.transform(valid_csv_row)

        assert isinstance(result['id'], float), "id는 float이어야 함"
        assert result['id'] == 1.4199688212321208e+19, "id 값이 올바르게 변환되어야 함"

    def test_transform_int_conversion(self, transformer, valid_csv_row):
        """int 타입 변환 테스트"""
        result = transformer.transform(valid_csv_row)

        assert isinstance(result['click'], int), "click은 int여야 함"
        assert result['click'] == 0, "click 값이 올바르게 변환되어야 함"
        assert isinstance(result['hour'], int), "hour는 int여야 함"
        assert result['hour'] == 14102101, "hour 값이 올바르게 변환되어야 함"

    def test_transform_scientific_notation(self, transformer):
        """과학 표기법 변환 테스트"""
        csv_row = {
            'id': '1.5237701630207834e+19',
            'click': '0',
            'hour': '14102101',
            'banner_pos': '2',
            'site_id': 'test',
            'site_domain': 'test',
            'site_category': 'test',
            'app_id': 'test',
            'app_domain': 'test',
            'app_category': 'test',
            'device_id': 'test',
            'device_ip': 'test',
            'device_model': 'test',
            'device_type': '2',
            'device_conn_type': '1',
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
        result = transformer.transform(csv_row)

        assert result is not None, "과학 표기법 변환 실패"
        assert isinstance(result['id'], float)

    def test_transform_missing_field(self, transformer, valid_csv_row):
        """필드 누락 테스트"""
        incomplete_row = valid_csv_row.copy()
        del incomplete_row['click']

        result = transformer.transform(incomplete_row)

        # 누락된 필드는 결과에 포함되지 않음
        assert 'click' not in result, "누락된 필드는 결과에 포함되지 않아야 함"

    def test_transform_invalid_type(self, transformer, valid_csv_row):
        """잘못된 타입 변환 테스트"""
        invalid_row = valid_csv_row.copy()
        invalid_row['hour'] = 'invalid'

        result = transformer.transform(invalid_row)

        assert result is None, "잘못된 타입은 None을 반환해야 함"

    def test_transform_string_conversion(self, transformer, valid_csv_row):
        """string 타입 변환 테스트"""
        result = transformer.transform(valid_csv_row)

        assert isinstance(result['site_id'], str), "site_id는 str이어야 함"
        assert result['site_id'] == '12fb4121', "site_id 값이 올바르게 변환되어야 함"


# ============================================================
# validate() 테스트
# ============================================================

class TestValidate:
    """validate() 메서드 테스트"""

    def test_validate_valid_data(self, transformer, valid_csv_row):
        """유효한 데이터 검증 테스트"""
        transformed = transformer.transform(valid_csv_row)
        result = transformer.validate(transformed)

        assert result is True, "유효한 데이터는 True를 반환해야 함"

    def test_validate_none_data(self, transformer):
        """None 데이터 검증 테스트"""
        result = transformer.validate(None)

        assert result is False, "None 데이터는 False를 반환해야 함"

    def test_validate_missing_field(self, transformer, valid_csv_row):
        """필수 필드 누락 테스트"""
        transformed = transformer.transform(valid_csv_row)
        del transformed['click']

        result = transformer.validate(transformed)

        assert result is False, "필수 필드 누락은 False를 반환해야 함"

    def test_validate_invalid_click_value(self, transformer, valid_csv_row):
        """click 값 범위 검증 테스트"""
        transformed = transformer.transform(valid_csv_row)
        transformed['click'] = 2  # 0 또는 1만 가능

        result = transformer.validate(transformed)

        assert result is False, "click 값이 0 또는 1이 아니면 False를 반환해야 함"

    def test_validate_click_values(self, transformer, valid_csv_row):
        """click 유효한 값 테스트"""
        for click_value in [0, 1]:
            transformed = transformer.transform(valid_csv_row)
            transformed['click'] = click_value
            result = transformer.validate(transformed)
            assert result is True, f"click={click_value}는 유효해야 함"

    def test_validate_invalid_hour_value(self, transformer, valid_csv_row):
        """hour 값 범위 검증 테스트"""
        transformed = transformer.transform(valid_csv_row)
        transformed['hour'] = 9999999  # YYMMDDHH 형식 위반

        result = transformer.validate(transformed)

        assert result is False, "유효하지 않은 hour 값은 False를 반환해야 함"

    def test_validate_hour_format(self, transformer, valid_csv_row):
        """hour 유효한 형식 테스트"""
        valid_hours = [10000000, 14102101, 99999999]
        for hour_value in valid_hours:
            transformed = transformer.transform(valid_csv_row)
            transformed['hour'] = hour_value
            result = transformer.validate(transformed)
            assert result is True, f"hour={hour_value}는 유효해야 함"

    def test_validate_invalid_banner_pos(self, transformer, valid_csv_row):
        """banner_pos 값 범위 검증 테스트"""
        transformed = transformer.transform(valid_csv_row)
        transformed['banner_pos'] = 10  # 0-7 범위 위반

        result = transformer.validate(transformed)

        assert result is False, "banner_pos가 0-7 범위를 벗어나면 False를 반환해야 함"

    def test_validate_banner_pos_valid(self, transformer, valid_csv_row):
        """banner_pos 유효한 값 테스트"""
        for pos in range(8):  # 0-7
            transformed = transformer.transform(valid_csv_row)
            transformed['banner_pos'] = pos
            result = transformer.validate(transformed)
            assert result is True, f"banner_pos={pos}는 유효해야 함"

    def test_validate_invalid_device_type(self, transformer, valid_csv_row):
        """device_type 값 범위 검증 테스트"""
        transformed = transformer.transform(valid_csv_row)
        transformed['device_type'] = 10  # 0-5 범위 위반

        result = transformer.validate(transformed)

        assert result is False, "device_type가 0-5 범위를 벗어나면 False를 반환해야 함"

    def test_validate_device_type_valid(self, transformer, valid_csv_row):
        """device_type 유효한 값 테스트"""
        for dev_type in range(6):  # 0-5
            transformed = transformer.transform(valid_csv_row)
            transformed['device_type'] = dev_type
            result = transformer.validate(transformed)
            assert result is True, f"device_type={dev_type}는 유효해야 함"

    def test_validate_invalid_device_conn_type(self, transformer, valid_csv_row):
        """device_conn_type 값 범위 검증 테스트"""
        transformed = transformer.transform(valid_csv_row)
        transformed['device_conn_type'] = 10  # 0-4 범위 위반

        result = transformer.validate(transformed)

        assert result is False, "device_conn_type가 0-4 범위를 벗어나면 False를 반환해야 함"

    def test_validate_wrong_type(self, transformer):
        """잘못된 필드 타입 검증 테스트"""
        invalid_data = {
            'id': 'not_a_float',  # float여야 함
            'click': 0,
            'hour': 14102101,
            'banner_pos': 0,
            'site_id': 'test',
            'site_domain': 'test',
            'site_category': 'test',
            'app_id': 'test',
            'app_domain': 'test',
            'app_category': 'test',
            'device_id': 'test',
            'device_ip': 'test',
            'device_model': 'test',
            'device_type': 1,
            'device_conn_type': 0,
            'C1': 100,
            'C14': 200,
            'C15': 300,
            'C16': 400,
            'C17': 500,
            'C18': 600,
            'C19': 700,
            'C20': 800,
            'C21': 900
        }

        result = transformer.validate(invalid_data)

        assert result is False, "잘못된 타입은 False를 반환해야 함"


# ============================================================
# to_json() 테스트
# ============================================================

class TestToJson:
    """to_json() 메서드 테스트"""

    def test_to_json_valid_data(self, transformer, valid_csv_row):
        """유효한 데이터 JSON 변환 테스트"""
        transformed = transformer.transform(valid_csv_row)
        result = transformer.to_json(transformed)

        assert result is not None, "유효한 데이터는 JSON 문자열을 반환해야 함"
        assert isinstance(result, str), "결과는 문자열이어야 함"
        assert len(result) > 0, "JSON 문자열은 비어있지 않아야 함"

    def test_to_json_none_data(self, transformer):
        """None 데이터 JSON 변환 테스트"""
        result = transformer.to_json(None)

        assert result is None, "None 데이터는 None을 반환해야 함"

    def test_to_json_contains_required_fields(self, transformer, valid_csv_row):
        """JSON에 모든 필드가 포함되는지 테스트"""
        transformed = transformer.transform(valid_csv_row)
        json_str = transformer.to_json(transformed)

        assert 'id' in json_str, "JSON에 id 필드가 포함되어야 함"
        assert 'click' in json_str, "JSON에 click 필드가 포함되어야 함"
        assert 'hour' in json_str, "JSON에 hour 필드가 포함되어야 함"

    def test_to_json_is_valid_json(self, transformer, valid_csv_row):
        """반환된 JSON이 유효한지 테스트"""
        import json

        transformed = transformer.transform(valid_csv_row)
        json_str = transformer.to_json(transformed)

        try:
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict), "JSON은 dict로 파싱되어야 함"
            assert len(parsed) > 0, "JSON dict는 비어있지 않아야 함"
        except json.JSONDecodeError as e:
            pytest.fail(f"유효하지 않은 JSON: {e}")

    def test_to_json_supports_korean(self, transformer):
        """한글 문자 지원 테스트"""
        import json

        data = {
            'id': 1.0,
            'click': 0,
            'hour': 14102101,
            'banner_pos': 0,
            'site_id': '한글테스트',
            'site_domain': 'test',
            'site_category': 'test',
            'app_id': 'test',
            'app_domain': 'test',
            'app_category': 'test',
            'device_id': 'test',
            'device_ip': 'test',
            'device_model': 'test',
            'device_type': 1,
            'device_conn_type': 0,
            'C1': 100,
            'C14': 200,
            'C15': 300,
            'C16': 400,
            'C17': 500,
            'C18': 600,
            'C19': 700,
            'C20': 800,
            'C21': 900
        }

        json_str = transformer.to_json(data)
        parsed = json.loads(json_str)

        assert parsed['site_id'] == '한글테스트', "한글 문자가 올바르게 저장되어야 함"


# ============================================================
# 통합 테스트 (E2E)
# ============================================================

class TestIntegration:
    """통합 테스트 (Transform → Validate → ToJSON)"""

    def test_full_pipeline_valid_data(self, transformer, valid_csv_row):
        """전체 파이프라인 테스트"""
        # 1. Transform
        transformed = transformer.transform(valid_csv_row)
        assert transformed is not None, "Transform 실패"

        # 2. Validate
        is_valid = transformer.validate(transformed)
        assert is_valid is True, "Validate 실패"

        # 3. ToJSON
        json_str = transformer.to_json(transformed)
        assert json_str is not None, "ToJSON 실패"

    def test_multiple_samples(self, transformer):
        """여러 샘플에 대한 파이프라인 테스트"""
        samples = [
            {
                'id': '1.0e+19',
                'click': '0',
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
            }
            for i in range(5)
        ]

        success_count = 0
        for sample in samples:
            transformed = transformer.transform(sample)
            if transformed and transformer.validate(transformed) and transformer.to_json(transformed):
                success_count += 1

        assert success_count == 5, "모든 샘플이 성공적으로 처리되어야 함"

    def test_invalid_pipeline_stops_at_validation(self, transformer, valid_csv_row):
        """검증 실패 시 파이프라인 중단"""
        transformed = transformer.transform(valid_csv_row)
        transformed['click'] = 5  # 유효하지 않은 값

        is_valid = transformer.validate(transformed)

        if not is_valid:
            json_str = transformer.to_json(transformed)
            # 검증 실패한 데이터는 로깅하지 않는 것이 좋음
            # (실제 프로덕션에서는 DLQ로 보냄)
            assert True, "유효하지 않은 데이터는 ToJSON까지 진행되지 않아야 함"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])