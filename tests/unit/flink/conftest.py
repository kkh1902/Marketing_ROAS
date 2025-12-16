# -*- coding: utf-8 -*-
"""
Pytest configuration for Flink tests

공유 fixtures와 설정들을 정의합니다.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

import pytest

# flink/src 디렉토리를 Python path에 추가
# tests/unit/flink/conftest.py 기준: ../../.. = 프로젝트 루트
FLINK_SRC_DIR = Path(__file__).parent.parent.parent.parent / "flink" / "src"
sys.path.insert(0, str(FLINK_SRC_DIR))

# schemas 디렉토리 위치
SCHEMAS_DIR = Path(__file__).parent.parent.parent.parent / "schemas"


@pytest.fixture
def ad_event_schema():
    """ad_event.avsc 스키마 로드"""
    schema_file = SCHEMAS_DIR / "ad_event.avsc"
    with open(schema_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def ctr_metric_schema():
    """ctr_metric.avsc 스키마 로드"""
    schema_file = SCHEMAS_DIR / "ctr_metric.avsc"
    with open(schema_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def sample_ad_event_data():
    """테스트용 샘플 광고 이벤트 데이터"""
    return {
        "id": 12345.0,
        "click": 1,
        "hour": 24112116,
        "banner_pos": 1,
        "site_id": "site_123",
        "site_domain": "example.com",
        "site_category": "news",
        "app_id": "app_456",
        "app_domain": "app.example.com",
        "app_category": "shopping",
        "device_id": "device_789",
        "device_ip": "192.168.1.1",
        "device_model": "iPhone",
        "device_type": 1,
        "device_conn_type": 1,
        "C1": 1,
        "C14": 5,
        "C15": 320,
        "C16": 50,
        "C17": 12,
        "C18": 1,
        "C19": 0,
        "C20": 5460,
        "C21": 25,
    }


@pytest.fixture
def temp_schema_file(sample_ad_event_data):
    """임시 Avro 스키마 파일 생성"""
    schema = {
        "type": "record",
        "name": "AdEvent",
        "namespace": "com.marketing.ctr",
        "fields": [
            {"name": "id", "type": "double"},
            {"name": "click", "type": "int"},
            {"name": "hour", "type": "long"},
            {"name": "banner_pos", "type": "int"},
            {"name": "site_id", "type": "string"},
            {"name": "site_domain", "type": ["null", "string"], "default": None},
            {"name": "site_category", "type": ["null", "string"], "default": None},
            {"name": "app_id", "type": ["null", "string"], "default": None},
            {"name": "app_domain", "type": ["null", "string"], "default": None},
            {"name": "app_category", "type": ["null", "string"], "default": None},
            {"name": "device_id", "type": ["null", "string"], "default": None},
            {"name": "device_ip", "type": ["null", "string"], "default": None},
            {"name": "device_model", "type": ["null", "string"], "default": None},
            {"name": "device_type", "type": ["null", "int"], "default": None},
            {"name": "device_conn_type", "type": ["null", "int"], "default": None},
            {"name": "C1", "type": ["null", "int"], "default": None},
            {"name": "C14", "type": ["null", "int"], "default": None},
            {"name": "C15", "type": ["null", "int"], "default": None},
            {"name": "C16", "type": ["null", "int"], "default": None},
            {"name": "C17", "type": ["null", "int"], "default": None},
            {"name": "C18", "type": ["null", "int"], "default": None},
            {"name": "C19", "type": ["null", "int"], "default": None},
            {"name": "C20", "type": ["null", "int"], "default": None},
            {"name": "C21", "type": ["null", "int"], "default": None},
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)
