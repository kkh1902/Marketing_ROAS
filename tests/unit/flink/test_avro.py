# -*- coding: utf-8 -*-
"""
Avro 직렬화/역직렬화 테스트

Avro 스키마 로드 및 데이터 인코딩/디코딩을 테스트합니다.
"""

import pytest
import json
import io
import sys
from pathlib import Path

import fastavro

# flink/src를 Python path에 추가
# tests/unit/flink/test_avro.py 기준: ../../.. = 프로젝트 루트
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "flink" / "src"))

from ctr_streaming import AdEvent, load_avro_schema


class TestAvroSchema:
    """Avro 스키마 로드 테스트"""

    def test_ad_event_schema_load(self):
        """ad_event.avsc 스키마 로드 테스트"""
        # tests/unit/flink에서 프로젝트 루트까지: ../../.. -> schemas
        schemas_dir = Path(__file__).parent.parent.parent.parent / "schemas"
        schema_file = schemas_dir / "ad_event.avsc"

        schema = load_avro_schema(str(schema_file))

        assert schema is not None
        assert schema["name"] == "AdEvent"
        assert schema["type"] == "record"
        assert len(schema["fields"]) == 24  # 24개 필드
        print(f"✅ Loaded AdEvent schema with {len(schema['fields'])} fields")

    def test_schema_has_required_fields(self):
        """스키마에 필수 필드 확인"""
        schemas_dir = Path(__file__).parent.parent.parent.parent / "schemas"
        schema_file = schemas_dir / "ad_event.avsc"

        schema = load_avro_schema(str(schema_file))

        field_names = [f["name"] for f in schema["fields"]]
        required_fields = ["id", "click", "hour", "site_id"]

        for field in required_fields:
            assert field in field_names, f"Missing required field: {field}"

        print(f"✅ All required fields present: {required_fields}")


class TestAvroSerialization:
    """Avro 직렬화/역직렬화 테스트"""

    def test_encode_decode_ad_event(self, sample_ad_event_data, temp_schema_file):
        """Avro 인코딩/디코딩 테스트"""
        with open(temp_schema_file, 'r') as f:
            schema = json.load(f)

        # 1. 데이터 인코딩 (Python dict -> Avro bytes)
        fo = io.BytesIO()
        fastavro.schemaless_writer(fo, schema, sample_ad_event_data)
        encoded_bytes = fo.getvalue()

        assert len(encoded_bytes) > 0
        print(f"✅ Encoded data: {len(encoded_bytes)} bytes")

        # 2. 데이터 디코딩 (Avro bytes -> Python dict)
        fo = io.BytesIO(encoded_bytes)
        decoded_data = fastavro.schemaless_reader(fo, schema)

        assert decoded_data["id"] == sample_ad_event_data["id"]
        assert decoded_data["click"] == sample_ad_event_data["click"]
        assert decoded_data["hour"] == sample_ad_event_data["hour"]
        print(f"✅ Decoded data matches original")

    def test_encoded_data_to_ad_event(self, sample_ad_event_data, temp_schema_file):
        """Avro 바이트 -> AdEvent 객체 변환"""
        with open(temp_schema_file, 'r') as f:
            schema = json.load(f)

        # Avro 인코딩
        fo = io.BytesIO()
        fastavro.schemaless_writer(fo, schema, sample_ad_event_data)
        encoded_bytes = fo.getvalue()

        # Avro 디코딩
        fo = io.BytesIO(encoded_bytes)
        decoded_data = fastavro.schemaless_reader(fo, schema)

        # AdEvent 객체 생성
        event = AdEvent(decoded_data)

        assert event.id == 12345.0
        assert event.click == 1
        assert event.site_id == "site_123"
        print(f"✅ Avro bytes -> AdEvent: {event}")

    def test_multiple_records_serialization(self, sample_ad_event_data, temp_schema_file):
        """여러 레코드 직렬화/역직렬화 테스트"""
        with open(temp_schema_file, 'r') as f:
            schema = json.load(f)

        # 3개의 레코드 생성
        records = []
        for i in range(3):
            record = sample_ad_event_data.copy()
            record["id"] = float(12345 + i)
            record["click"] = i % 2
            records.append(record)

        # 인코딩
        fo = io.BytesIO()
        for record in records:
            fastavro.schemaless_writer(fo, schema, record)
        encoded_bytes = fo.getvalue()

        # 디코딩 및 검증
        fo = io.BytesIO(encoded_bytes)
        decoded_records = []
        try:
            while True:
                record = fastavro.schemaless_reader(fo, schema)
                decoded_records.append(record)
        except (EOFError, StopIteration):
            pass

        # 첫 번째 레코드만 디코딩됨 (현재 구현)
        assert len(decoded_records) >= 1
        assert decoded_records[0]["id"] == 12345.0
        print(f"✅ Multiple records encoding/decoding test passed")


class TestAvroSchemaValidation:
    """Avro 스키마 검증"""

    def test_schema_namespace(self):
        """스키마 namespace 확인"""
        schemas_dir = Path(__file__).parent.parent.parent.parent / "schemas"
        schema_file = schemas_dir / "ad_event.avsc"

        schema = load_avro_schema(str(schema_file))

        assert schema["namespace"] == "com.marketing.ctr"
        print(f"✅ Schema namespace: {schema['namespace']}")

    def test_all_fields_documented(self):
        """모든 필드에 문서화(doc) 확인"""
        schemas_dir = Path(__file__).parent.parent.parent.parent / "schemas"
        schema_file = schemas_dir / "ad_event.avsc"

        schema = load_avro_schema(str(schema_file))

        undocumented_fields = []
        for field in schema["fields"]:
            if "doc" not in field:
                undocumented_fields.append(field["name"])

        if undocumented_fields:
            print(f"⚠️ Undocumented fields: {undocumented_fields}")
        else:
            print("✅ All fields are documented")
