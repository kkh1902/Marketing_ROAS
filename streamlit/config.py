import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Database Configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'marketing_roas'),
}

# Database Connection String
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Streamlit Page Configuration
STREAMLIT_CONFIG = {
    'page_title': 'CTR Monitoring Dashboard',
    'page_icon': '=Ê',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded',
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'refresh_interval': 5,           # Refresh every 5 seconds
    'chart_height': 400,             # Chart height in pixels
    'max_rows': 1000,                # Max rows for tables
    'timezone': 'UTC',
}

# Data Queries
QUERIES = {
    'current_ctr': """
        SELECT
            ROUND(AVG(daily_ctr_percentage), 2) as ctr_percentage,
            MAX(event_date) as last_updated
        FROM analytics.fct_daily_metrics
        WHERE event_date >= CURRENT_DATE
    """,

    'hourly_trend': """
        SELECT
            event_hour_timestamp as timestamp,
            ROUND(AVG(ctr_percentage), 2) as ctr_percentage
        FROM analytics.int_hourly_agg
        WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY event_hour_timestamp
        ORDER BY timestamp DESC
        LIMIT 100
    """,

    'site_performance': """
        SELECT
            site_domain,
            ROUND(AVG(daily_ctr_percentage), 2) as ctr_percentage,
            SUM(daily_total_clicks) as total_clicks,
            SUM(daily_total_impressions) as total_impressions
        FROM analytics.fct_daily_metrics
        WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY site_domain
        ORDER BY ctr_percentage DESC
        LIMIT 20
    """,

    'device_distribution': """
        SELECT
            device_type,
            ROUND(AVG(daily_ctr_percentage), 2) as ctr_percentage,
            COUNT(*) as count
        FROM analytics.fct_daily_metrics
        WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY device_type
        ORDER BY count DESC
    """,

    'alerts': """
        SELECT
            event_date,
            site_id,
            device_type,
            daily_ctr_percentage,
            clicks_dod_pct_change as dod_change
        FROM analytics.fct_daily_metrics
        WHERE (abs(clicks_dod_pct_change) > 1000)
           OR (daily_ctr_percentage < 15)
           OR (event_date < CURRENT_DATE - INTERVAL '1 hour')
        ORDER BY event_date DESC
        LIMIT 20
    """,
}

# Alert Configuration
ALERT_CONFIG = {
    'ctr_drop_threshold': 15,           # Alert if CTR < 15%
    'ctr_spike_threshold': 1000,        # Alert if DoD change > 1000%
    'data_freshness_threshold': 3600,   # Alert if data > 1 hour old (seconds)
}
