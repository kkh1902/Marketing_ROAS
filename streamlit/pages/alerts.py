import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from config import DB_CONFIG, ALERT_CONFIG
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(
    page_title='Alerts & Anomalies',
    page_icon='=¨',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ============================================================================
# Database Connection
# ============================================================================
@st.cache_resource
def get_db_connection():
    """Create database connection"""
    try:
        connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        st.error(f"Database Connection Error: {str(e)}")
        st.stop()

# ============================================================================
# Alert Detection Functions
# ============================================================================
@st.cache_data(ttl=60)
def detect_ctr_spike_alerts(engine):
    """Detect CTR spike anomalies (DayOverDay > threshold)"""
    try:
        threshold = ALERT_CONFIG['ctr_spike_threshold']
        query = f"""
        SELECT
            event_date,
            site_id,
            device_type,
            daily_ctr_percentage,
            clicks_dod_pct_change,
            'CTR Spike' as alert_type,
            CASE
                WHEN abs(clicks_dod_pct_change) > {threshold}
                THEN 'CRITICAL'
                ELSE 'WARNING'
            END as severity
        FROM analytics.fct_daily_metrics
        WHERE abs(clicks_dod_pct_change) > {threshold}
          AND event_date >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY event_date DESC
        LIMIT 50
        """

        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.warning(f"Error detecting CTR spikes: {str(e)}")
        return None

@st.cache_data(ttl=60)
def detect_ctr_drop_alerts(engine):
    """Detect low CTR anomalies"""
    try:
        threshold = ALERT_CONFIG['ctr_drop_threshold']
        query = f"""
        SELECT
            event_date,
            site_id,
            device_type,
            daily_ctr_percentage,
            daily_total_clicks,
            daily_total_impressions,
            'Low CTR' as alert_type,
            'WARNING' as severity
        FROM analytics.fct_daily_metrics
        WHERE daily_ctr_percentage < {threshold}
          AND event_date >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY event_date DESC
        LIMIT 50
        """

        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.warning(f"Error detecting low CTR: {str(e)}")
        return None

@st.cache_data(ttl=60)
def detect_data_freshness_alerts(engine):
    """Detect stale data"""
    try:
        threshold = ALERT_CONFIG['data_freshness_threshold']  # seconds
        query = f"""
        SELECT
            event_date,
            MAX(event_date) as max_date,
            'Stale Data' as alert_type,
            'INFO' as severity
        FROM analytics.fct_daily_metrics
        WHERE event_date < CURRENT_DATE - INTERVAL '1 hour'
        GROUP BY event_date
        ORDER BY event_date DESC
        LIMIT 20
        """

        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.warning(f"Error detecting stale data: {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_alert_summary(engine):
    """Get summary of all alerts"""
    try:
        query = """
        SELECT
            COUNT(*) as total_records,
            COUNT(CASE WHEN clicks_dod_pct_change > 1000 THEN 1 END) as critical_spikes,
            COUNT(CASE WHEN daily_ctr_percentage < 15 THEN 1 END) as low_ctr,
            MAX(event_date) as latest_data
        FROM analytics.fct_daily_metrics
        WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
        """

        df = pd.read_sql(query, engine)
        return df.iloc[0] if not df.empty else None
    except Exception as e:
        st.warning(f"Error getting alert summary: {str(e)}")
        return None

# ============================================================================
# Display Functions
# ============================================================================
def display_alert_card(alert_type, count, color, icon):
    """Display alert card"""
    col = st.columns(1)[0]
    with col:
        st.markdown(f"""
        <div style='
            background-color: {color};
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
        '>
            <h3>{icon} {alert_type}</h3>
            <h2>{count}</h2>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# Main Application
# ============================================================================
def main():
    st.title('=¨ Alerts & Anomaly Detection')
    st.markdown('---')

    # Get database connection
    engine = get_db_connection()

    # Alert Summary
    st.subheader('=Ê Alert Summary (Last 7 Days)')

    summary = get_alert_summary(engine)
    if summary is not None:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric('Total Records', int(summary['total_records']))

        with col2:
            st.metric('Critical Spikes', int(summary['critical_spikes']), delta='=4' if summary['critical_spikes'] > 0 else '')

        with col3:
            st.metric('Low CTR Cases', int(summary['low_ctr']), delta=' ' if summary['low_ctr'] > 0 else '')

        with col4:
            st.metric('Latest Data', str(summary['latest_data'])[:10])

    st.markdown('---')

    # Tabs for different alert types
    tab1, tab2, tab3 = st.tabs(['=4 CTR Spikes', '  Low CTR', '9 Data Freshness'])

    # Tab 1: CTR Spike Alerts
    with tab1:
        st.subheader('CTR Spike Anomalies (>1000% change)')
        st.info('Indicates unusual spikes in click-through rate that might indicate bot activity or data anomalies')

        spike_alerts = detect_ctr_spike_alerts(engine)
        if spike_alerts is not None and not spike_alerts.empty:
            display_df = spike_alerts[['event_date', 'site_id', 'device_type', 'daily_ctr_percentage', 'clicks_dod_pct_change', 'severity']].copy()
            display_df.columns = ['Date', 'Site ID', 'Device', 'CTR (%)', 'DoD Change (%)', 'Severity']

            # Color code by severity
            def color_severity(row):
                if row['Severity'] == 'CRITICAL':
                    return ['background-color: #ff4b4b'] * len(row)
                elif row['Severity'] == 'WARNING':
                    return ['background-color: #ff9800'] * len(row)
                else:
                    return ['background-color: white'] * len(row)

            st.dataframe(
                display_df.style.apply(color_severity, axis=1),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success(' No CTR spike alerts detected')

    # Tab 2: Low CTR Alerts
    with tab2:
        st.subheader(f'Low CTR Detection (< {ALERT_CONFIG["ctr_drop_threshold"]}%)')
        st.info('Indicates periods with below-average click-through rates')

        low_ctr_alerts = detect_ctr_drop_alerts(engine)
        if low_ctr_alerts is not None and not low_ctr_alerts.empty:
            display_df = low_ctr_alerts[['event_date', 'site_id', 'device_type', 'daily_ctr_percentage', 'daily_total_clicks', 'daily_total_impressions']].copy()
            display_df.columns = ['Date', 'Site ID', 'Device', 'CTR (%)', 'Clicks', 'Impressions']

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            # Summary statistics for low CTR
            col1, col2 = st.columns(2)
            with col1:
                avg_ctr = low_ctr_alerts['daily_ctr_percentage'].mean()
                st.metric('Avg CTR (Low Cases)', f'{avg_ctr:.2f}%')

            with col2:
                count = len(low_ctr_alerts)
                st.metric('Low CTR Occurrences', count)
        else:
            st.success(' No low CTR alerts detected')

    # Tab 3: Data Freshness
    with tab3:
        st.subheader('Data Freshness Status')
        st.info('Checks if data is being updated regularly')

        try:
            query = "SELECT MAX(event_date) as max_date FROM analytics.fct_daily_metrics"
            result = pd.read_sql(query, engine)
            if not result.empty:
                max_date = result['max_date'].iloc[0]
                time_diff = datetime.now() - max_date
                hours_diff = time_diff.total_seconds() / 3600

                if hours_diff < 1:
                    st.success(f' Data is fresh (updated {int(hours_diff * 60)} minutes ago)')
                elif hours_diff < 24:
                    st.warning(f'  Data is {int(hours_diff)} hours old')
                else:
                    st.error(f'=4 Data is {int(hours_diff / 24)} days old - please check pipeline')

                col1, col2 = st.columns(2)
                with col1:
                    st.metric('Latest Data Date', str(max_date)[:10])
                with col2:
                    st.metric('Hours Since Update', f'{int(hours_diff)}')
            else:
                st.error('No data found in database')
        except Exception as e:
            st.error(f'Error checking data freshness: {str(e)}')

    st.markdown('---')

    # Alert Settings
    with st.expander('™ Alert Configuration'):
        st.write('Current Alert Thresholds:')
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info(f'CTR Drop Threshold: {ALERT_CONFIG["ctr_drop_threshold"]}%')

        with col2:
            st.info(f'CTR Spike Threshold: {ALERT_CONFIG["ctr_spike_threshold"]}%')

        with col3:
            st.info(f'Data Freshness: {ALERT_CONFIG["data_freshness_threshold"]} seconds')

if __name__ == '__main__':
    main()
