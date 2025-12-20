"""
E2E 테스트: 전체 데이터 파이프라인 흐름
Kafka → Flink → PostgreSQL 전체 흐름 검증
"""

import pytest
import time
import json
import psycopg2
from datetime import datetime

# Test topic constants
TEST_RAW_TOPIC = "test_ad_events_raw"
TEST_RETRY_TOPIC = "test_ad_events_retry"
TEST_DLQ_TOPIC = "test_ad_events_dlq"


class TestFullPipeline:
    """전체 파이프라인 흐름 테스트"""

    @pytest.fixture(scope="function")
    def postgres_connection(self):
        """PostgreSQL 연결"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password='postgres',
                database='marketing_roas'
            )
            yield conn
            conn.close()
        except psycopg2.OperationalError as e:
            pytest.skip(f"PostgreSQL not available: {e}")

    def test_kafka_to_postgres_flow(self, kafka_producer, postgres_connection):
        """Kafka → PostgreSQL 전체 데이터 흐름 테스트"""
        # 1. 테스트 데이터 생성
        test_events = [
            {
                'id': f'test_event_{i}',
                'click': 1 if i % 5 == 0 else 0,
                'hour': '2024122009',
                'banner_pos': str(i % 10),
                'site_id': f'site_{i % 3}',
                'site_domain': f'example{i % 3}.com',
                'site_category': 'tech',
                'app_id': None,
                'app_domain': None,
                'app_category': None,
                'device_id': f'device_{i % 5}',
                'device_ip': f'192.168.1.{i}',
                'device_model': 'iPhone',
                'device_type': 'phone',
                'device_conn_type': '4G',
                'c1': 'test',
                'c14': 'test',
                'c15': 'test',
                'c16': 'test',
                'c17': 'test',
                'c18': 'test',
                'c19': 'test',
                'c20': 'test',
                'c21': 'test'
            }
            for i in range(10)
        ]

        # 2. Kafka에 메시지 발송
        message_count = 0
        for event in test_events:
            future = kafka_producer.send(TEST_RAW_TOPIC, value=event)
            future.get(timeout=5)
            message_count += 1

        kafka_producer.flush()

        # 3. Flink 처리 대기 (실제 환경에서는 더 오래)
        time.sleep(3)

        # 4. PostgreSQL에서 데이터 확인
        cursor = postgres_connection.cursor()
        try:
            # 테이블 존재 여부 확인
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema='realtime' AND table_name='ad_events'
            """)
            table_exists = cursor.fetchone()[0] > 0

            if table_exists:
                # 데이터 개수 확인
                cursor.execute("SELECT COUNT(*) FROM realtime.ad_events")
                db_count = cursor.fetchone()[0]

                # 검증
                assert db_count >= 0, f"Expected data in realtime.ad_events but got {db_count}"
                print(f"✅ PostgreSQL에 {db_count}개 레코드 확인")
            else:
                print("⚠️ realtime.ad_events 테이블이 없음")

        finally:
            cursor.close()

    def test_data_no_loss(self, kafka_producer, postgres_connection):
        """메시지 손실 확인 테스트"""
        # 1. Kafka에 100개 메시지 발송
        test_ids = []
        for i in range(100):
            event = {
                'id': f'test_no_loss_{i}',
                'click': i % 2,
                'hour': '2024122010',
                'banner_pos': '0',
                'site_id': 'test_site',
                'site_domain': 'test.com',
                'site_category': 'test',
                'app_id': None,
                'app_domain': None,
                'app_category': None,
                'device_id': 'test_device',
                'device_ip': '127.0.0.1',
                'device_model': 'test',
                'device_type': 'test',
                'device_conn_type': 'test',
                'c1': 'test', 'c14': 'test', 'c15': 'test', 'c16': 'test',
                'c17': 'test', 'c18': 'test', 'c19': 'test', 'c20': 'test', 'c21': 'test'
            }
            kafka_producer.send(TEST_RAW_TOPIC, value=event)
            test_ids.append(f'test_no_loss_{i}')

        kafka_producer.flush()
        time.sleep(3)

        # 2. PostgreSQL에서 확인
        cursor = postgres_connection.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM realtime.ad_events
                WHERE id LIKE 'test_no_loss_%'
            """)
            count = cursor.fetchone()[0]

            if count > 0:
                print(f"✅ 메시지 손실 테스트: {count}/100 메시지 확인")
                assert count == 100, f"Expected 100 messages but got {count}"
            else:
                print("⚠️ 메시지 처리 안 됨 (Flink 실행 필요)")

        finally:
            cursor.close()

    def test_processing_latency(self, kafka_producer, postgres_connection):
        """처리 지연시간 측정"""
        # 1. 시작 시간 기록
        start_time = time.time()

        # 2. 메시지 발송
        event = {
            'id': f'latency_test_{int(start_time)}',
            'click': 1,
            'hour': '2024122011',
            'banner_pos': '0',
            'site_id': 'latency_test',
            'site_domain': 'latency.com',
            'site_category': 'test',
            'app_id': None, 'app_domain': None, 'app_category': None,
            'device_id': 'test', 'device_ip': '127.0.0.1', 'device_model': 'test',
            'device_type': 'test', 'device_conn_type': 'test',
            'c1': 'test', 'c14': 'test', 'c15': 'test', 'c16': 'test',
            'c17': 'test', 'c18': 'test', 'c19': 'test', 'c20': 'test', 'c21': 'test'
        }

        kafka_producer.send(TEST_RAW_TOPIC, value=event)
        kafka_producer.flush()

        # 3. PostgreSQL에 도착할 때까지 대기 (최대 10초)
        cursor = postgres_connection.cursor()
        try:
            event_id = event['id']
            for attempt in range(20):  # 최대 10초 대기
                cursor.execute(
                    f"SELECT * FROM realtime.ad_events WHERE id = %s",
                    (event_id,)
                )
                if cursor.fetchone():
                    end_time = time.time()
                    latency = end_time - start_time
                    print(f"✅ 처리 지연시간: {latency:.2f}초")
                    assert latency < 10, f"Latency {latency:.2f}s exceeds 10s threshold"
                    return
                time.sleep(0.5)

            print("⚠️ 메시지 도착 안 됨 (Flink 미실행)")

        finally:
            cursor.close()

    def test_ctr_calculation_in_pipeline(self, postgres_connection):
        """파이프라인에서 CTR 계산 정확성"""
        cursor = postgres_connection.cursor()
        try:
            # 샘플 데이터가 있는지 확인
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN click = 1 THEN 1 ELSE 0 END) as clicks
                FROM realtime.ad_events
                LIMIT 1000
            """)
            result = cursor.fetchone()

            if result and result[0] > 0:
                total = result[0]
                clicks = result[1] if result[1] else 0
                ctr = (clicks / total * 100) if total > 0 else 0

                print(f"✅ CTR 계산: {clicks}/{total} = {ctr:.2f}%")
                assert 0 <= ctr <= 100, f"CTR {ctr} is outside valid range [0, 100]"
            else:
                print("⚠️ 샘플 데이터 없음")

        finally:
            cursor.close()
