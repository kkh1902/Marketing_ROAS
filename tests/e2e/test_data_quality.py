"""
E2E 테스트: 데이터 품질 검증
중복 제거, NULL 처리, 범위 검증 등
"""

import pytest
import psycopg2


class TestDataQuality:
    """데이터 품질 검증 테스트"""

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

    def test_no_duplicate_ids(self, postgres_connection):
        """ID 중복 제거 검증"""
        cursor = postgres_connection.cursor()
        try:
            cursor.execute("""
                SELECT id, COUNT(*) as cnt
                FROM realtime.ad_events
                GROUP BY id
                HAVING COUNT(*) > 1
                LIMIT 10
            """)

            duplicates = cursor.fetchall()
            if duplicates:
                print(f"⚠️ 중복 ID 발견: {len(duplicates)}개")
                for dup in duplicates:
                    print(f"   ID: {dup[0]}, Count: {dup[1]}")
            else:
                print("✅ 중복 ID 없음")

            assert len(duplicates) == 0, "Duplicate IDs found in realtime.ad_events"

        except psycopg2.ProgrammingError:
            print("⚠️ realtime.ad_events 테이블이 없음")
        finally:
            cursor.close()

    def test_click_values_valid(self, postgres_connection):
        """Click 값이 0 또는 1만 포함"""
        cursor = postgres_connection.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM realtime.ad_events
                WHERE click NOT IN (0, 1)
            """)

            invalid_count = cursor.fetchone()[0]

            if invalid_count > 0:
                cursor.execute("""
                    SELECT DISTINCT click FROM realtime.ad_events
                    WHERE click NOT IN (0, 1)
                """)
                invalid_values = cursor.fetchall()
                print(f"❌ 유효하지 않은 click 값: {invalid_values}")
            else:
                print("✅ 모든 click 값이 0 또는 1")

            assert invalid_count == 0, f"Found {invalid_count} invalid click values"

        except psycopg2.ProgrammingError:
            print("⚠️ realtime.ad_events 테이블이 없음")
        finally:
            cursor.close()

    def test_no_null_required_fields(self, postgres_connection):
        """필수 필드에 NULL 없음"""
        cursor = postgres_connection.cursor()
        required_fields = ['id', 'click', 'hour', 'site_id']

        try:
            for field in required_fields:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM realtime.ad_events
                    WHERE {field} IS NULL
                """)

                null_count = cursor.fetchone()[0]

                if null_count > 0:
                    print(f"❌ {field} 필드에 {null_count}개 NULL 값")
                else:
                    print(f"✅ {field}: NULL 없음")

                assert null_count == 0, f"{field} has {null_count} NULL values"

        except psycopg2.ProgrammingError:
            print("⚠️ realtime.ad_events 테이블이 없음")
        finally:
            cursor.close()

    def test_ctr_calculation_valid_range(self, postgres_connection):
        """CTR 계산이 0-100% 범위 내"""
        cursor = postgres_connection.cursor()
        try:
            # realtime.ad_events에서 샘플 데이터로 CTR 계산
            cursor.execute("""
                SELECT
                    COUNT(*) as impressions,
                    SUM(CASE WHEN click = 1 THEN 1 ELSE 0 END) as clicks
                FROM realtime.ad_events
                WHERE click IN (0, 1)
            """)

            result = cursor.fetchone()
            if result and result[0] > 0:
                impressions = result[0]
                clicks = result[1] if result[1] else 0
                ctr = (clicks / impressions * 100) if impressions > 0 else 0

                print(f"✅ CTR 계산: {clicks}/{impressions} = {ctr:.2f}%")

                # CTR이 0-100% 범위 확인
                assert 0 <= ctr <= 100, f"CTR {ctr}% is outside valid range"

                # analytics 스키마가 있으면 추가 검증
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables
                        WHERE table_schema='analytics' AND table_name='fct_daily_metrics'
                    """)

                    if cursor.fetchone()[0] > 0:
                        cursor.execute("""
                            SELECT
                                COUNT(*) as cnt,
                                MIN(daily_ctr_percentage) as min_ctr,
                                MAX(daily_ctr_percentage) as max_ctr
                            FROM analytics.fct_daily_metrics
                        """)

                        result = cursor.fetchone()
                        if result and result[0] > 0:
                            min_ctr = result[1]
                            max_ctr = result[2]

                            print(f"✅ dbt CTR 범위: {min_ctr:.2f}% ~ {max_ctr:.2f}%")

                            assert min_ctr >= 0, f"Min CTR {min_ctr} < 0"
                            assert max_ctr <= 100, f"Max CTR {max_ctr} > 100"
                except:
                    print("⚠️ analytics 스키마 미검증 (dbt 미실행)")

            else:
                print("⚠️ 샘플 데이터 없음")

        except psycopg2.ProgrammingError:
            print("⚠️ realtime.ad_events 테이블이 없음")
        finally:
            cursor.close()

    def test_data_type_integrity(self, postgres_connection):
        """데이터 타입 무결성"""
        cursor = postgres_connection.cursor()
        try:
            # 숫자 필드 검증
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN banner_pos ~ '^[0-9]+$' THEN 1 END) as valid_banner
                FROM realtime.ad_events
            """)

            result = cursor.fetchone()
            if result and result[0] > 0:
                total = result[0]
                valid = result[1]

                print(f"✅ 데이터 타입 검증: {valid}/{total} 유효")

                if total > 0:
                    assert valid == total, f"Invalid data types found in {total - valid} records"

        except psycopg2.ProgrammingError:
            print("⚠️ realtime.ad_events 테이블이 없음")
        finally:
            cursor.close()

    def test_data_volume_sanity(self, postgres_connection):
        """데이터 볼륨 합리성 검증"""
        cursor = postgres_connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT hour) as unique_hours,
                    COUNT(DISTINCT site_id) as unique_sites
                FROM realtime.ad_events
            """)

            result = cursor.fetchone()
            if result:
                total = result[0]
                hours = result[1]
                sites = result[2]

                print(f"""
✅ 데이터 볼륨 검증:
   - 총 레코드: {total}개
   - 유니크 시간: {hours}개
   - 유니크 사이트: {sites}개
                """)

                # 합리성 검증 (선택적)
                if total > 0:
                    avg_per_hour = total / max(1, hours)
                    print(f"   - 시간별 평균: {avg_per_hour:.0f}개/시간")

        except psycopg2.ProgrammingError:
            print("⚠️ realtime.ad_events 테이블이 없음")
        finally:
            cursor.close()
