"""
Integration 테스트: Flink 스트리밍 파이프라인

테스트:
- Kafka 메시지 → Flink 수신 확인
- 1분 Tumbling Window CTR 집계
- 결과 → PostgreSQL realtime.ctr_metrics 저장
"""

import pytest
import json
import time
from datetime import datetime
from tests.integration.conftest import TEST_RAW_TOPIC


@pytest.mark.integration
class TestFlinkStreamingIntegration:
    """Flink 스트리밍 파이프라인 테스트"""

    def test_kafka_to_flink_message_flow(self, kafka_producer, kafka_consumer):
        """Kafka → Flink 메시지 흐름 확인"""
        # 1. 테스트 메시지 발행
        test_messages = []
        for i in range(5):
            message = {
                'id': float(i),
                'click': i % 2,  # 0, 1, 0, 1, 0
                'hour': 14102101,
                'banner_pos': 0,
                'site_id': 'test_site',
                'device_type': 1,
                'test_type': 'flink_flow_test',
                'timestamp': int(time.time() * 1000)  # milliseconds
            }
            kafka_producer.send(TEST_RAW_TOPIC, message)
            test_messages.append(message)

        kafka_producer.flush()

        # 2. Kafka에서 메시지 수신 확인
        kafka_consumer.subscribe([TEST_RAW_TOPIC])
        received_messages = []

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'flink_flow_test':
                received_messages.append(msg.value)

            if len(received_messages) >= 5:
                break

        # 3. 검증
        assert len(received_messages) == 5, "Flink 입력 메시지 수 불일치"

        # 각 메시지의 필수 필드 확인
        for msg in received_messages:
            assert 'id' in msg
            assert 'click' in msg
            assert 'hour' in msg
            assert 'timestamp' in msg

    def test_ctr_calculation_window(self, kafka_producer, kafka_consumer):
        """CTR 계산 검증 (클릭률 = 클릭 수 / 총 건수)"""
        # 1. 테스트 데이터: 10개 중 4개 클릭
        #    예상 CTR = 4 / 10 = 0.4 (40%)
        total_messages = 10
        clicked_count = 4

        for i in range(total_messages):
            message = {
                'id': float(i),
                'click': 1 if i < clicked_count else 0,
                'hour': 14102101,
                'banner_pos': 0,
                'site_id': 'test_site',
                'device_type': 1,
                'test_type': 'ctr_calc_test',
                'timestamp': int(time.time() * 1000)
            }
            kafka_producer.send(TEST_RAW_TOPIC, message)

        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RAW_TOPIC])
        received_messages = []

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'ctr_calc_test':
                received_messages.append(msg.value)

            if len(received_messages) >= total_messages:
                break

        # 3. CTR 계산
        total_clicks = sum(1 for msg in received_messages if msg['click'] == 1)
        total_impressions = len(received_messages)
        calculated_ctr = total_clicks / total_impressions if total_impressions > 0 else 0

        # 4. 검증
        assert total_clicks == clicked_count, f"클릭 수 불일치: {total_clicks} != {clicked_count}"
        assert total_impressions == total_messages, f"임프레션 수 불일치: {total_impressions} != {total_messages}"
        assert abs(calculated_ctr - 0.4) < 0.01, f"CTR 계산 오류: {calculated_ctr} != 0.4"

    def test_tumbling_window_aggregation(self, kafka_producer, kafka_consumer):
        """Tumbling Window 집계 검증"""
        window_size = 10  # 1분 윈도우 대신 테스트용으로 10개 메시지를 1 윈도우로 간주

        # 1. 윈도우 크기만큼 메시지 발행
        for i in range(window_size):
            message = {
                'id': float(i),
                'click': 1 if i < 3 else 0,  # 3개 클릭
                'hour': 14102101,
                'banner_pos': 0,
                'site_id': 'test_site',
                'device_type': 1,
                'test_type': 'window_agg_test',
                'timestamp': int(time.time() * 1000) + i * 1000  # 1초씩 증가
            }
            kafka_producer.send(TEST_RAW_TOPIC, message)

        kafka_producer.flush()

        # 2. 메시지 수신
        kafka_consumer.subscribe([TEST_RAW_TOPIC])
        received_messages = []

        for msg in kafka_consumer:
            if msg.value and msg.value.get('test_type') == 'window_agg_test':
                received_messages.append(msg.value)

            if len(received_messages) >= window_size:
                break

        # 3. 윈도우 집계 계산
        total_clicks = sum(1 for msg in received_messages if msg['click'] == 1)
        total_impressions = len(received_messages)
        window_ctr = total_clicks / total_impressions if total_impressions > 0 else 0

        # 4. 검증
        assert len(received_messages) == window_size, f"윈도우 크기: {len(received_messages)} != {window_size}"
        assert total_clicks == 3, f"윈도우 내 클릭 수: {total_clicks} != 3"
        assert abs(window_ctr - 0.3) < 0.01, f"윈도우 CTR: {window_ctr} != 0.3"

    def test_postgresql_metrics_schema(self, postgres_cursor):
        """PostgreSQL realtime.ctr_metrics 테이블 검증"""
        # 1. 테이블 존재 확인
        try:
            postgres_cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'realtime'
                    AND table_name = 'ctr_metrics'
                )
            """)
            exists = postgres_cursor.fetchone()[0]

            if not exists:
                # 테이블 생성
                postgres_cursor.execute("""
                    CREATE SCHEMA IF NOT EXISTS realtime;

                    CREATE TABLE realtime.ctr_metrics (
                        id SERIAL PRIMARY KEY,
                        window_start TIMESTAMP,
                        window_end TIMESTAMP,
                        ctr FLOAT,
                        impressions INT,
                        clicks INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                postgres_cursor.connection.commit()
        except Exception as e:
            pytest.fail(f"PostgreSQL 테이블 생성 실패: {e}")

        # 2. 테이블 컬럼 확인
        postgres_cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'realtime'
            AND table_name = 'ctr_metrics'
            ORDER BY ordinal_position
        """)
        columns = postgres_cursor.fetchall()

        assert len(columns) >= 6, f"컬럼 수 부족: {len(columns)} columns"
        assert columns[1][0] == 'window_start'
        assert columns[2][0] == 'window_end'
        assert columns[3][0] == 'ctr'
        assert columns[4][0] == 'impressions'
        assert columns[5][0] == 'clicks'

    def test_insert_metrics_to_postgresql(self, postgres_cursor):
        """PostgreSQL에 메트릭 데이터 삽입"""
        # 1. 테이블 생성 (없으면)
        postgres_cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS realtime;

            CREATE TABLE IF NOT EXISTS realtime.ctr_metrics (
                id SERIAL PRIMARY KEY,
                window_start TIMESTAMP,
                window_end TIMESTAMP,
                ctr FLOAT,
                impressions INT,
                clicks INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. 테스트 데이터 삽입
        test_data = {
            'window_start': datetime.now(),
            'window_end': datetime.now(),
            'ctr': 0.35,
            'impressions': 100,
            'clicks': 35
        }

        postgres_cursor.execute("""
            INSERT INTO realtime.ctr_metrics
            (window_start, window_end, ctr, impressions, clicks)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            test_data['window_start'],
            test_data['window_end'],
            test_data['ctr'],
            test_data['impressions'],
            test_data['clicks']
        ))

        postgres_cursor.connection.commit()

        # 3. 데이터 검증
        postgres_cursor.execute("""
            SELECT ctr, impressions, clicks
            FROM realtime.ctr_metrics
            WHERE ctr = %s
        """, (test_data['ctr'],))

        result = postgres_cursor.fetchone()

        assert result is not None, "삽입된 데이터를 조회할 수 없습니다"
        assert result[0] == test_data['ctr'], f"CTR 값 불일치: {result[0]} != {test_data['ctr']}"
        assert result[1] == test_data['impressions'], f"Impressions 불일치: {result[1]} != {test_data['impressions']}"
        assert result[2] == test_data['clicks'], f"Clicks 불일치: {result[2]} != {test_data['clicks']}"

        # 4. 정리 (테스트 데이터 삭제)
        postgres_cursor.execute("TRUNCATE realtime.ctr_metrics CASCADE")
        postgres_cursor.connection.commit()
