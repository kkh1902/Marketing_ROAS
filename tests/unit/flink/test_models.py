# -*- coding: utf-8 -*-
"""
AdEvent와 CTRMetric 모델 테스트

데이터 모델이 올바르게 작동하는지 검증합니다.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# flink/src를 Python path에 추가
# tests/unit/flink/test_models.py 기준: ../../.. = 프로젝트 루트
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "flink" / "src"))

from ctr_streaming import AdEvent, CTRMetric


class TestAdEvent:
    """AdEvent 모델 테스트"""

    def test_ad_event_creation(self, sample_ad_event_data):
        """AdEvent 객체 생성 테스트"""
        event = AdEvent(sample_ad_event_data)

        assert event.id == 12345.0
        assert event.click == 1
        assert event.hour == 24112116
        assert event.banner_pos == 1
        assert event.site_id == "site_123"
        assert event.device_id == "device_789"
        print(f"✅ AdEvent created: {event}")

    def test_ad_event_to_tuple(self, sample_ad_event_data):
        """AdEvent -> Tuple 변환 테스트 (PostgreSQL INSERT용)"""
        event = AdEvent(sample_ad_event_data)
        tuple_data = event.to_tuple()

        # 튜플은 24개 필드를 가져야 함
        assert len(tuple_data) == 24
        assert tuple_data[0] == 12345.0  # id
        assert tuple_data[1] == 1  # click
        assert tuple_data[2] == 24112116  # hour
        print(f"✅ AdEvent tuple conversion successful: {len(tuple_data)} fields")

    def test_ad_event_str(self, sample_ad_event_data):
        """AdEvent __str__ 테스트"""
        event = AdEvent(sample_ad_event_data)
        str_repr = str(event)

        assert "AdEvent" in str_repr
        assert "id=12345" in str_repr
        assert "click=1" in str_repr
        print(f"✅ AdEvent string representation: {str_repr}")

    def test_ad_event_timestamp(self, sample_ad_event_data):
        """AdEvent 타임스탬프 설정 테스트"""
        event = AdEvent(sample_ad_event_data)

        # 타임스탬프는 밀리초 단위
        assert isinstance(event.timestamp, int)
        assert event.timestamp > 0
        print(f"✅ AdEvent timestamp: {event.timestamp}ms")

    def test_ad_event_with_none_values(self):
        """Optional 필드가 None인 경우 처리"""
        data = {
            "id": 123.0,
            "click": 0,
            "hour": 24112116,
            "banner_pos": 0,
            "site_id": "site_1",
            # 나머지 필드는 None
        }
        event = AdEvent(data)

        assert event.id == 123.0
        assert event.site_domain is None
        assert event.device_id is None
        print("✅ AdEvent handles None values correctly")


class TestCTRMetric:
    """CTRMetric 모델 테스트"""

    def test_ctr_metric_creation(self):
        """CTRMetric 객체 생성 테스트"""
        window_start = 1000  # 1초
        window_end = 2000    # 2초
        impressions = 100
        clicks = 10

        metric = CTRMetric(window_start, window_end, impressions, clicks)

        assert metric.impressions == 100
        assert metric.clicks == 10
        assert metric.ctr == 10.0  # 10/100 * 100 = 10%
        print(f"✅ CTRMetric created: {metric}")

    def test_ctr_metric_calculation(self):
        """CTR 계산 테스트"""
        metric = CTRMetric(1000, 2000, 50, 5)

        # CTR = (5 / 50) * 100 = 10%
        assert metric.ctr == 10.0
        print(f"✅ CTR calculated correctly: {metric.ctr}%")

    def test_ctr_metric_zero_impressions(self):
        """노출이 0인 경우 CTR 계산 (0으로 나누기 방지)"""
        metric = CTRMetric(1000, 2000, 0, 0)

        # 노출이 0이면 CTR은 0
        assert metric.ctr == 0.0
        print("✅ CTRMetric handles zero impressions correctly")

    def test_ctr_metric_to_tuple(self):
        """CTRMetric -> Tuple 변환 테스트"""
        metric = CTRMetric(1000, 2000, 100, 15)
        tuple_data = metric.to_tuple()

        # 튜플은 5개 필드: window_start, window_end, impressions, clicks, ctr
        assert len(tuple_data) == 5
        assert tuple_data[2] == 100  # impressions
        assert tuple_data[3] == 15   # clicks
        assert tuple_data[4] == 15.0  # ctr
        print(f"✅ CTRMetric tuple conversion: {tuple_data}")

    def test_ctr_metric_str(self):
        """CTRMetric __str__ 테스트"""
        metric = CTRMetric(1000, 2000, 200, 40)
        str_repr = str(metric)

        assert "CTRMetric" in str_repr
        assert "impressions=200" in str_repr
        assert "clicks=40" in str_repr
        assert "ctr=20.00" in str_repr
        print(f"✅ CTRMetric string representation: {str_repr}")

    def test_ctr_metric_timestamp_conversion(self):
        """타임스탬프 변환 테스트 (밀리초 -> datetime)"""
        # 2024-01-01 00:00:00 UTC = 1704067200000ms
        window_start = 1704067200000
        window_end = 1704067260000  # +60초

        metric = CTRMetric(window_start, window_end, 100, 20)

        assert isinstance(metric.window_start, datetime)
        assert isinstance(metric.window_end, datetime)
        assert (metric.window_end - metric.window_start).total_seconds() == 60
        print(f"✅ Timestamp conversion: {metric.window_start} -> {metric.window_end}")

    def test_ctr_metric_high_ctr(self):
        """높은 CTR 테스트"""
        # 100번 노출, 99번 클릭 = 99% CTR
        metric = CTRMetric(1000, 2000, 100, 99)

        assert metric.ctr == 99.0
        print(f"✅ High CTR: {metric.ctr}%")

    def test_ctr_metric_low_ctr(self):
        """낮은 CTR 테스트"""
        # 1000번 노출, 1번 클릭 = 0.1% CTR
        metric = CTRMetric(1000, 2000, 1000, 1)

        assert metric.ctr == 0.1
        print(f"✅ Low CTR: {metric.ctr}%")
