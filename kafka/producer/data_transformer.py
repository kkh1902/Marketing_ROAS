"""
Kafka Producer용 데이터 변환 모듈
CSV 데이터를 Avro 형식으로 변환
"""

import json
from typing import Dict, Any, List

from utils.logger import get_logger

logger = get_logger(__name__)


class AdEventTransformer:
    """
    원본 광고 이벤트 데이터(CSV 형식)를 Kafka 메시지 형식(Avro)으로 변환
    """

    # ad_event.avsc 스키마에 정의된 필드와 타입
    FIELD_TYPES = {
        'id': float,
        'click': int,
        'hour': int,
        'banner_pos': int,
        'site_id': str,
        'site_domain': str,
        'site_category': str,
        'app_id': str,
        'app_domain': str,
        'app_category': str,
        'device_id': str,
        'device_ip': str,
        'device_model': str,
        'device_type': int,
        'device_conn_type': int,
        'C1': int,
        'C14': int,
        'C15': int,
        'C16': int,
        'C17': int,
        'C18': int,
        'C19': int,
        'C20': int,
        'C21': int,
    }

    def __init__(self):
        """변환기 초기화"""
        pass

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CSV 데이터 → Avro 포맷으로 변환

        매개변수:
            raw_data: CSV에서 읽은 원본 데이터 (딕셔너리)

        반환:
            Avro 포맷으로 변환된 데이터 (딕셔너리)
        """
        try:
            transformed = {}

            # 1. raw_data의 각 필드를 올바른 타입으로 변환
            for field_name, field_type in self.FIELD_TYPES.items():
                if field_name not in raw_data:
                    logger.warning(f"Missing field: {field_name}")
                    continue

                raw_value = raw_data[field_name]

                try:
                    # 타입 변환
                    if field_type == float:
                        converted_value = float(raw_value)
                    elif field_type == int:
                        converted_value = int(float(raw_value))  # 1e+19 형식 처리
                    elif field_type == str:
                        converted_value = str(raw_value)
                    else:
                        converted_value = raw_value

                    transformed[field_name] = converted_value

                except (ValueError, TypeError) as e:
                    logger.error(f"Type conversion error for {field_name}={raw_value}: {e}")
                    return None

            # 2. 필드명 기준으로 정렬 (선택사항이지만 일관성을 위해)
            # 3. 변환된 dict 반환
            return transformed

        except Exception as e:
            logger.error(f"Transform error: {e}")
            return None

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        변환된 데이터가 Avro 스키마를 만족하는지 검증

        매개변수:
            data: 변환된 데이터 (딕셔너리)

        반환:
            True (유효함) 또는 False (유효하지 않음)
        """
        if data is None:
            logger.error("Data is None")
            return False

        try:
            # 1. 모든 필수 필드가 있는지 확인
            for field_name in self.FIELD_TYPES.keys():
                if field_name not in data:
                    logger.error(f"Missing required field: {field_name}")
                    return False

            # 2. 각 필드의 타입이 맞는지 확인
            for field_name, field_type in self.FIELD_TYPES.items():
                value = data[field_name]

                if field_type == float and not isinstance(value, (float, int)):
                    logger.error(f"Field {field_name} should be float, got {type(value)}")
                    return False

                elif field_type == int and not isinstance(value, int):
                    logger.error(f"Field {field_name} should be int, got {type(value)}")
                    return False

                elif field_type == str and not isinstance(value, str):
                    logger.error(f"Field {field_name} should be str, got {type(value)}")
                    return False

            # 3. 값의 범위가 유효한지 확인
            # click: 0 또는 1만 가능
            if data.get('click') not in (0, 1):
                logger.error(f"Invalid click value: {data.get('click')} (must be 0 or 1)")
                return False

            # hour: YYMMDDHH 형식 (14091123 = 2014-09-11 23:00)
            hour = data.get('hour')
            if not (10000000 <= hour <= 99999999):
                logger.error(f"Invalid hour value: {hour} (must be YYMMDDHH format)")
                return False

            # banner_pos: 0-7 범위
            banner_pos = data.get('banner_pos')
            if not (0 <= banner_pos <= 7):
                logger.error(f"Invalid banner_pos: {banner_pos} (must be 0-7)")
                return False

            # device_type: 0-5 범위
            device_type = data.get('device_type')
            if not (0 <= device_type <= 5):
                logger.error(f"Invalid device_type: {device_type} (must be 0-5)")
                return False

            # device_conn_type: 0-4 범위
            device_conn_type = data.get('device_conn_type')
            if not (0 <= device_conn_type <= 4):
                logger.error(f"Invalid device_conn_type: {device_conn_type} (must be 0-4)")
                return False

            # 문자열 필드 길이 확인 (빈 문자열 방지)
            string_fields = ['site_id', 'site_domain', 'site_category', 'app_id',
                           'app_domain', 'app_category', 'device_id', 'device_ip', 'device_model']
            for field in string_fields:
                if len(data.get(field, '')) == 0:
                    logger.warning(f"Empty string field: {field}")

            logger.debug(f"✅ Validation passed for event id={data.get('id')}")
            return True

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    def to_json(self, data: Dict[str, Any]) -> str:
        """
        변환된 데이터를 JSON 문자열로 변환

        매개변수:
            data: 변환된 데이터 (딕셔너리)

        반환:
            JSON 문자열 또는 None (변환 실패 시)
        """
        if data is None:
            logger.error("Cannot serialize None data")
            return None

        try:
            # 1. dict를 JSON 문자열로 변환
            json_str = json.dumps(data, ensure_ascii=False)
            return json_str

        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialization error: {e}, data={data}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during JSON serialization: {e}")
            return None
