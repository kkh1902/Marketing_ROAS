-- ============================================================
-- Flink CTR Streaming - PostgreSQL Schema
-- ============================================================
-- Description:
--   Flink 스트리밍 작업에서 집계한 CTR 메트릭 저장
--   1분 및 5분 단위 Tumbling Window 집계 결과
--
-- Created: 2024-12-16
-- Updated: 2024-12-16
-- ============================================================


-- ============================================================
-- 1. realtime 스키마 생성
-- ============================================================

CREATE SCHEMA IF NOT EXISTS realtime;


-- ============================================================
-- 2. 원본 광고 이벤트 테이블
-- ============================================================

CREATE TABLE IF NOT EXISTS realtime.ad_events (
    event_id BIGSERIAL PRIMARY KEY,
    id DOUBLE PRECISION NOT NULL,
    click INT NOT NULL,
    hour BIGINT NOT NULL,
    banner_pos INT NOT NULL,
    site_id VARCHAR(255) NOT NULL,
    site_domain VARCHAR(255),
    site_category VARCHAR(255),
    app_id VARCHAR(255),
    app_domain VARCHAR(255),
    app_category VARCHAR(255),
    device_id VARCHAR(255),
    device_ip VARCHAR(255),
    device_model VARCHAR(255),
    device_type INT,
    device_conn_type INT,
    C1 INT,
    C14 INT,
    C15 INT,
    C16 INT,
    C17 INT,
    C18 INT,
    C19 INT,
    C20 INT,
    C21 INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성 (조회 성능)
CREATE INDEX IF NOT EXISTS idx_ad_events_hour
    ON realtime.ad_events(hour DESC);

CREATE INDEX IF NOT EXISTS idx_ad_events_created_at
    ON realtime.ad_events(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ad_events_event_time
    ON realtime.ad_events(created_at, click);

CREATE INDEX IF NOT EXISTS idx_ad_events_site_id
    ON realtime.ad_events(site_id);

CREATE INDEX IF NOT EXISTS idx_ad_events_device_id
    ON realtime.ad_events(device_id);

-- 테이블 주석
COMMENT ON TABLE realtime.ad_events
    IS 'Kafka에서 수신한 원본 광고 이벤트 데이터 저장소';

COMMENT ON COLUMN realtime.ad_events.event_id
    IS '이벤트 고유 ID (자동 증가)';

COMMENT ON COLUMN realtime.ad_events.id
    IS '광고 ID - 각 광고 impression의 고유 식별자';

COMMENT ON COLUMN realtime.ad_events.click
    IS '클릭 여부 (0=노출만, 1=클릭)';

COMMENT ON COLUMN realtime.ad_events.hour
    IS '타임스탬프 (YYMMDDHH 형식, UTC)';

COMMENT ON COLUMN realtime.ad_events.banner_pos
    IS '배너가 표시된 위치 (0-7)';

COMMENT ON COLUMN realtime.ad_events.site_id
    IS '광고가 표시된 사이트 ID';

COMMENT ON COLUMN realtime.ad_events.device_id
    IS '사용자 기기 ID (익명화됨)';

COMMENT ON COLUMN realtime.ad_events.device_type
    IS '기기 유형 (0=Unknown, 1=Mobile, 2=Tablet, ...)';

COMMENT ON COLUMN realtime.ad_events.device_conn_type
    IS '네트워크 연결 유형 (0=Unknown, 1=WiFi, 2=Cellular, ...)';


-- ============================================================
-- 3. 1분 단위 CTR 메트릭 테이블
-- ============================================================

CREATE TABLE IF NOT EXISTS realtime.ctr_metrics_1min (
    metric_id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    impressions INT NOT NULL DEFAULT 0,
    clicks INT NOT NULL DEFAULT 0,
    ctr FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성 (조회 성능)
CREATE INDEX IF NOT EXISTS idx_ctr_metrics_1min_window_start
    ON realtime.ctr_metrics_1min(window_start DESC);

CREATE INDEX IF NOT EXISTS idx_ctr_metrics_1min_created_at
    ON realtime.ctr_metrics_1min(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ctr_metrics_1min_window_range
    ON realtime.ctr_metrics_1min(window_start, window_end);

-- 테이블 주석
COMMENT ON TABLE realtime.ctr_metrics_1min
    IS '1분 Tumbling Window로 집계한 CTR 메트릭';

COMMENT ON COLUMN realtime.ctr_metrics_1min.window_start
    IS '윈도우 시작 시간';

COMMENT ON COLUMN realtime.ctr_metrics_1min.window_end
    IS '윈도우 종료 시간';

COMMENT ON COLUMN realtime.ctr_metrics_1min.impressions
    IS '노출 건수 (click=0인 이벤트)';

COMMENT ON COLUMN realtime.ctr_metrics_1min.clicks
    IS '클릭 건수 (click=1인 이벤트)';

COMMENT ON COLUMN realtime.ctr_metrics_1min.ctr
    IS 'Click-Through Rate (%)';


-- ============================================================
-- 4. 5분 단위 CTR 메트릭 테이블 (선택)
-- ============================================================

CREATE TABLE IF NOT EXISTS realtime.ctr_metrics_5min (
    metric_id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    impressions INT NOT NULL DEFAULT 0,
    clicks INT NOT NULL DEFAULT 0,
    ctr FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_ctr_metrics_5min_window_start
    ON realtime.ctr_metrics_5min(window_start DESC);

CREATE INDEX IF NOT EXISTS idx_ctr_metrics_5min_created_at
    ON realtime.ctr_metrics_5min(created_at DESC);

-- 테이블 주석
COMMENT ON TABLE realtime.ctr_metrics_5min
    IS '5분 Tumbling Window로 집계한 CTR 메트릭';


-- ============================================================
-- 5. 뷰: 최신 CTR 메트릭 (1분)
-- ============================================================

CREATE OR REPLACE VIEW realtime.latest_ctr_1min AS
SELECT
    metric_id,
    window_start,
    window_end,
    impressions,
    clicks,
    ctr,
    created_at,
    updated_at
FROM realtime.ctr_metrics_1min
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY window_start DESC;

COMMENT ON VIEW realtime.latest_ctr_1min
    IS '최근 1시간 1분 단위 CTR 메트릭 뷰';


-- ============================================================
-- 6. 뷰: 최신 CTR 메트릭 (5분)
-- ============================================================

CREATE OR REPLACE VIEW realtime.latest_ctr_5min AS
SELECT
    metric_id,
    window_start,
    window_end,
    impressions,
    clicks,
    ctr,
    created_at,
    updated_at
FROM realtime.ctr_metrics_5min
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '2 hours'
ORDER BY window_start DESC;

COMMENT ON VIEW realtime.latest_ctr_5min
    IS '최근 2시간 5분 단위 CTR 메트릭 뷰';


-- ============================================================
-- 7. 통계 함수
-- ============================================================

CREATE OR REPLACE FUNCTION realtime.get_avg_ctr_1h()
RETURNS FLOAT AS $$
    SELECT AVG(ctr)
    FROM realtime.ctr_metrics_1min
    WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '1 hour';
$$ LANGUAGE SQL;

COMMENT ON FUNCTION realtime.get_avg_ctr_1h()
    IS '최근 1시간 평균 CTR 계산';


-- ============================================================
-- 8. 데이터 보관 정책 (Retention Policy)
-- ============================================================
-- 목적: 저장 공간 절약 및 성능 유지
-- - ad_events: 90일 이상 데이터 자동 삭제
-- - 메트릭: 장기 보관 (필요 시 정책 수정)
--
-- 사용: SELECT realtime.cleanup_old_events();
-- 스케줄: Cron Job 또는 pg_cron 확장 사용

-- 1. 오래된 이벤트 데이터 정리 함수
CREATE OR REPLACE FUNCTION realtime.cleanup_old_events(
    p_days_retained INT DEFAULT 90
)
RETURNS TABLE(deleted_rows BIGINT) AS $$
DECLARE
    v_deleted BIGINT;
BEGIN
    DELETE FROM realtime.ad_events
    WHERE created_at < CURRENT_TIMESTAMP - (p_days_retained || ' days')::INTERVAL;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    RETURN QUERY SELECT v_deleted;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION realtime.cleanup_old_events(INT)
    IS '90일 이상 된 ad_events 데이터 삭제. 반환: 삭제된 행 수';


-- 2. 테이블 최적화 함수 (VACUUM + ANALYZE)
CREATE OR REPLACE FUNCTION realtime.optimize_tables()
RETURNS TABLE(table_name TEXT, status TEXT) AS $$
BEGIN
    -- ad_events 테이블 최적화
    VACUUM ANALYZE realtime.ad_events;
    RETURN QUERY SELECT 'ad_events'::TEXT, 'Optimized'::TEXT;

    -- 메트릭 테이블 최적화
    VACUUM ANALYZE realtime.ctr_metrics_1min;
    RETURN QUERY SELECT 'ctr_metrics_1min'::TEXT, 'Optimized'::TEXT;

    VACUUM ANALYZE realtime.ctr_metrics_5min;
    RETURN QUERY SELECT 'ctr_metrics_5min'::TEXT, 'Optimized'::TEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION realtime.optimize_tables()
    IS '모든 realtime 테이블 최적화 (VACUUM ANALYZE)';


-- 3. 통합 유지보수 함수
CREATE OR REPLACE FUNCTION realtime.maintenance()
RETURNS TABLE(step TEXT, details TEXT) AS $$
BEGIN
    -- 단계 1: 오래된 데이터 삭제
    RETURN QUERY EXECUTE 'SELECT ''cleanup_events''::TEXT, deleted_rows::TEXT FROM realtime.cleanup_old_events()';

    -- 단계 2: 테이블 최적화
    RETURN QUERY SELECT 'optimize_tables'::TEXT, status FROM realtime.optimize_tables();

    -- 단계 3: 완료
    RETURN QUERY SELECT 'status'::TEXT, 'Maintenance completed'::TEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION realtime.maintenance()
    IS '전체 유지보수 작업 실행 (정리 + 최적화)';


-- ============================================================
-- ⚠️ 자동 정리 스케줄 설정 (선택사항)
-- ============================================================
-- 매주 일요일 02:00에 정리 작업 실행
--
-- 설치 필요: sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS pg_cron;"
--
-- 적용 방법 (PostgreSQL 컨테이너 내부 또는 호스트에서):
-- psql -U admin -d my-app-db -c "
--   CREATE EXTENSION IF NOT EXISTS pg_cron;
--   SELECT cron.schedule('cleanup-old-events', '0 2 * * 0', 'SELECT realtime.cleanup_old_events()');
--   SELECT cron.schedule('optimize-tables', '0 3 * * 0', 'SELECT realtime.optimize_tables()');
-- "
--
-- 현재 스케줄 확인:
-- SELECT * FROM cron.job;
--
-- 스케줄 삭제:
-- SELECT cron.unschedule('cleanup-old-events');


-- ============================================================
-- 9. 데이터 샘플 (테스트용)
-- ============================================================

-- 주석 처리: 필요시 주석 해제하여 테스트 데이터 삽입
-- INSERT INTO realtime.ctr_metrics_1min
--     (window_start, window_end, impressions, clicks, ctr, created_at, updated_at)
-- VALUES
--     ('2024-12-16 14:30:00', '2024-12-16 14:31:00', 834, 166, 19.90, NOW(), NOW()),
--     ('2024-12-16 14:31:00', '2024-12-16 14:32:00', 920, 150, 16.30, NOW(), NOW()),
--     ('2024-12-16 14:32:00', '2024-12-16 14:33:00', 1050, 172, 16.38, NOW(), NOW());


-- ============================================================
-- 테이블 생성 확인
-- ============================================================

SELECT
    schemaname,
    tablename
FROM pg_tables
WHERE schemaname = 'realtime'
ORDER BY tablename;
