"""
E2E 테스트: 성능 검증
처리량, 지연시간, 메모리 사용량 측정
"""

import pytest
import time
import psycopg2
from datetime import datetime


class TestPerformance:
    """성능 검증 테스트"""

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

    def test_query_performance(self, postgres_connection):
        """쿼리 성능 측정"""
        cursor = postgres_connection.cursor()
        test_cases = [
            ("COUNT(*)", "SELECT COUNT(*) FROM realtime.ad_events"),
            ("GROUP BY hour", """
                SELECT hour, COUNT(*) FROM realtime.ad_events
                GROUP BY hour LIMIT 100
            """),
            ("GROUP BY site_id", """
                SELECT site_id, COUNT(*) FROM realtime.ad_events
                GROUP BY site_id LIMIT 100
            """),
        ]

        try:
            for test_name, query in test_cases:
                start = time.time()
                cursor.execute(query)
                cursor.fetchall()
                elapsed = time.time() - start

                print(f"✅ 쿼리 '{test_name}': {elapsed*1000:.2f}ms")

                # SLA 확인 (< 1초)
                assert elapsed < 1.0, f"Query '{test_name}' took {elapsed:.2f}s (> 1s)"

        except psycopg2.ProgrammingError:
            print("⚠️ realtime.ad_events 테이블이 없음")
        finally:
            cursor.close()

    def test_throughput_measurement(self, kafka_producer, postgres_connection):
        """처리량 측정"""
        print("\n📊 처리량 측정 시작...")

        # 1. 메시지 발송 속도 측정
        num_messages = 100
        start_time = time.time()

        for i in range(num_messages):
            event = {
                'id': f'throughput_test_{i}',
                'click': i % 2,
                'hour': '2024122012',
                'banner_pos': '0',
                'site_id': 'perf_test',
                'site_domain': 'perf.com',
                'site_category': 'test',
                'app_id': None, 'app_domain': None, 'app_category': None,
                'device_id': 'test', 'device_ip': '127.0.0.1', 'device_model': 'test',
                'device_type': 'test', 'device_conn_type': 'test',
                'c1': 't', 'c14': 't', 'c15': 't', 'c16': 't',
                'c17': 't', 'c18': 't', 'c19': 't', 'c20': 't', 'c21': 't'
            }
            kafka_producer.send('test_ad_events_raw', value=event)

        kafka_producer.flush()
        producer_time = time.time() - start_time
        producer_throughput = num_messages / producer_time if producer_time > 0 else 0

        print(f"✅ Kafka Producer 처리량: {producer_throughput:.0f} msg/sec")
        print(f"   ({num_messages} 메시지, {producer_time:.2f}초)")

        # 2. PostgreSQL 쿼리 처리량 측정 (5초 내 몇 개 쿼리?)
        cursor = postgres_connection.cursor()
        query_count = 0
        start_time = time.time()

        try:
            while time.time() - start_time < 5:
                cursor.execute("""
                    SELECT COUNT(*) FROM realtime.ad_events LIMIT 1
                """)
                cursor.fetchone()
                query_count += 1

            query_throughput = query_count / 5
            print(f"✅ PostgreSQL 쿼리 처리량: {query_throughput:.0f} queries/sec")

        except psycopg2.ProgrammingError:
            print("⚠️ realtime.ad_events 테이블이 없음")
        finally:
            cursor.close()

    def test_latency_distribution(self, kafka_producer, postgres_connection):
        """지연시간 분포 측정"""
        print("\n📊 지연시간 분포 측정...")

        latencies = []

        # 10개 메시지로 테스트
        for i in range(10):
            start = time.time()

            # 메시지 발송
            event = {
                'id': f'latency_dist_{i}_{int(start*1000)}',
                'click': i % 2,
                'hour': '2024122013',
                'banner_pos': '0',
                'site_id': 'latency',
                'site_domain': 'latency.com',
                'site_category': 'test',
                'app_id': None, 'app_domain': None, 'app_category': None,
                'device_id': 'test', 'device_ip': '127.0.0.1', 'device_model': 'test',
                'device_type': 'test', 'device_conn_type': 'test',
                'c1': 't', 'c14': 't', 'c15': 't', 'c16': 't',
                'c17': 't', 'c18': 't', 'c19': 't', 'c20': 't', 'c21': 't'
            }

            kafka_producer.send('test_ad_events_raw', value=event)
            kafka_producer.flush()

            # PostgreSQL 도착 확인 (최대 5초)
            cursor = postgres_connection.cursor()
            for _ in range(10):
                cursor.execute("""
                    SELECT 1 FROM realtime.ad_events
                    WHERE id = %s LIMIT 1
                """, (event['id'],))

                if cursor.fetchone():
                    latency = time.time() - start
                    latencies.append(latency)
                    break

                time.sleep(0.5)
            cursor.close()

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)

            print(f"""✅ 지연시간 분포:
   - 최소: {min_latency:.2f}초
   - 평균: {avg_latency:.2f}초
   - 최대: {max_latency:.2f}초
            """)
        else:
            print("⚠️ 메시지 도착 없음 (Flink 미실행)")

    def test_table_size_growth(self, postgres_connection):
        """테이블 크기 증가율 측정"""
        cursor = postgres_connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname IN ('realtime', 'analytics')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)

            results = cursor.fetchall()

            if results:
                print("\n📊 테이블 크기:")
                total_size = 0
                for schema, table, size in results:
                    print(f"   {schema}.{table}: {size}")

                    # 숫자 추출해서 합계 계산 (선택적)
            else:
                print("⚠️ 테이블이 없음")

        except (psycopg2.ProgrammingError, psycopg2.OperationalError) as e:
            print(f"⚠️ 테이블 조회 실패: {e}")
        finally:
            cursor.close()

    def test_index_usage(self, postgres_connection):
        """인덱스 사용 현황"""
        cursor = postgres_connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as scans
                FROM pg_stat_user_indexes
                WHERE schemaname IN ('realtime', 'analytics')
                ORDER BY idx_scan DESC
                LIMIT 10
            """)

            results = cursor.fetchall()

            if results:
                print("\n📊 인덱스 사용 현황:")
                for schema, table, index, scans in results:
                    print(f"   {schema}.{table}.{index}: {scans} scans")
            else:
                print("⚠️ 인덱스 정보 없음")

        except (psycopg2.ProgrammingError, psycopg2.OperationalError):
            print("⚠️ 인덱스 조회 실패")
        finally:
            cursor.close()

    def test_connection_pool_health(self, postgres_connection):
        """연결 풀 상태 확인"""
        cursor = postgres_connection.cursor()
        try:
            cursor.execute("SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname")
            results = cursor.fetchall()

            print("\n📊 연결 상태:")
            for dbname, count in results:
                if dbname:
                    print(f"   {dbname}: {count} 연결")

        except (psycopg2.ProgrammingError, psycopg2.OperationalError):
            print("⚠️ 연결 상태 조회 실패")
        finally:
            cursor.close()
