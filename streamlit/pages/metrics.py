import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine
from config import DB_CONFIG, STREAMLIT_CONFIG, DASHBOARD_CONFIG
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(
    page_title='Metrics Analysis',
    page_icon='=È',
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
# Data Loading Functions
# ============================================================================
@st.cache_data(ttl=300)
def load_daily_metrics(engine, start_date, end_date, site_id=None, device_type=None):
    """Load daily metrics with filters"""
    try:
        query = f"""
        SELECT
            event_date,
            site_domain,
            device_type,
            daily_ctr_percentage,
            daily_total_clicks,
            daily_total_impressions,
            clicks_dod_pct_change,
            ctr_7day_moving_avg
        FROM analytics.fct_daily_metrics
        WHERE event_date >= '{start_date}'
          AND event_date <= '{end_date}'
        """

        if site_id:
            query += f" AND site_domain = '{site_id}'"

        if device_type:
            query += f" AND device_type = '{device_type}'"

        query += " ORDER BY event_date DESC"

        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error loading metrics: {str(e)}")
        return None

@st.cache_data(ttl=300)
def load_site_list(engine):
    """Load available sites"""
    try:
        query = "SELECT DISTINCT site_domain FROM analytics.fct_daily_metrics ORDER BY site_domain"
        df = pd.read_sql(query, engine)
        return df['site_domain'].tolist()
    except Exception as e:
        st.warning(f"Error loading site list: {str(e)}")
        return []

@st.cache_data(ttl=300)
def load_device_list(engine):
    """Load available devices"""
    try:
        query = "SELECT DISTINCT device_type FROM analytics.fct_daily_metrics WHERE device_type IS NOT NULL ORDER BY device_type"
        df = pd.read_sql(query, engine)
        return df['device_type'].tolist()
    except Exception as e:
        st.warning(f"Error loading device list: {str(e)}")
        return []

# ============================================================================
# Chart Functions
# ============================================================================
def create_daily_ctr_chart(df):
    """Create daily CTR trend chart"""
    if df is None or df.empty:
        return None

    fig = go.Figure()

    # CTR actual
    fig.add_trace(go.Scatter(
        x=df['event_date'],
        y=df['daily_ctr_percentage'],
        mode='lines+markers',
        name='Daily CTR',
        line=dict(color='#FF4B4B', width=2),
        marker=dict(size=8)
    ))

    # 7-day moving average
    fig.add_trace(go.Scatter(
        x=df['event_date'],
        y=df['ctr_7day_moving_avg'],
        mode='lines',
        name='7-Day MA',
        line=dict(color='#4B4BFF', width=2, dash='dash')
    ))

    fig.update_layout(
        title='Daily CTR Trend',
        xaxis_title='Date',
        yaxis_title='CTR (%)',
        hovermode='x unified',
        height=DASHBOARD_CONFIG['chart_height'],
        template='plotly_light'
    )

    return fig

def create_clicks_chart(df):
    """Create clicks trend chart"""
    if df is None or df.empty:
        return None

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['event_date'],
        y=df['daily_total_clicks'],
        name='Daily Clicks',
        marker=dict(color='#4CAF50')
    ))

    fig.update_layout(
        title='Daily Clicks Trend',
        xaxis_title='Date',
        yaxis_title='Clicks',
        height=DASHBOARD_CONFIG['chart_height'],
        template='plotly_light'
    )

    return fig

def create_impressions_chart(df):
    """Create impressions trend chart"""
    if df is None or df.empty:
        return None

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['event_date'],
        y=df['daily_total_impressions'],
        name='Daily Impressions',
        marker=dict(color='#2196F3')
    ))

    fig.update_layout(
        title='Daily Impressions Trend',
        xaxis_title='Date',
        yaxis_title='Impressions',
        height=DASHBOARD_CONFIG['chart_height'],
        template='plotly_light'
    )

    return fig

# ============================================================================
# Main Application
# ============================================================================
def main():
    st.title('=È Detailed Metrics Analysis')
    st.markdown('---')

    # Get database connection
    engine = get_db_connection()

    # Sidebar Filters
    st.sidebar.header('= Filters')

    # Date range filter
    default_start = datetime.now() - timedelta(days=30)
    default_end = datetime.now()

    start_date = st.sidebar.date_input(
        'Start Date',
        value=default_start,
        max_value=default_end
    )

    end_date = st.sidebar.date_input(
        'End Date',
        value=default_end,
        min_value=start_date
    )

    # Site filter
    sites = load_site_list(engine)
    selected_site = st.sidebar.selectbox(
        'Site Domain',
        options=['All'] + sites,
        index=0
    )

    # Device filter
    devices = load_device_list(engine)
    selected_device = st.sidebar.selectbox(
        'Device Type',
        options=['All'] + devices,
        index=0
    )

    st.sidebar.markdown('---')
    st.sidebar.caption('=Ê Auto-refresh: 5 minutes')

    # Load data with filters
    site_filter = selected_site if selected_site != 'All' else None
    device_filter = selected_device if selected_device != 'All' else None

    metrics_df = load_daily_metrics(
        engine,
        str(start_date),
        str(end_date),
        site_filter,
        device_filter
    )

    if metrics_df is None or metrics_df.empty:
        st.warning('No data available for selected filters')
        return

    # Summary Statistics
    st.subheader('=Ê Summary Statistics')
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_ctr = metrics_df['daily_ctr_percentage'].mean()
        st.metric('Avg CTR', f'{avg_ctr:.2f}%')

    with col2:
        total_clicks = metrics_df['daily_total_clicks'].sum()
        st.metric('Total Clicks', f'{int(total_clicks):,}')

    with col3:
        total_impressions = metrics_df['daily_total_impressions'].sum()
        st.metric('Total Impressions', f'{int(total_impressions):,}')

    with col4:
        max_ctr = metrics_df['daily_ctr_percentage'].max()
        st.metric('Max CTR', f'{max_ctr:.2f}%')

    st.markdown('---')

    # Charts
    st.subheader('=È Trends')

    col1, col2 = st.columns(2)

    with col1:
        ctr_chart = create_daily_ctr_chart(metrics_df.sort_values('event_date'))
        if ctr_chart:
            st.plotly_chart(ctr_chart, use_container_width=True)

    with col2:
        clicks_chart = create_clicks_chart(metrics_df.sort_values('event_date'))
        if clicks_chart:
            st.plotly_chart(clicks_chart, use_container_width=True)

    impressions_chart = create_impressions_chart(metrics_df.sort_values('event_date'))
    if impressions_chart:
        st.plotly_chart(impressions_chart, use_container_width=True)

    st.markdown('---')

    # Data Table
    st.subheader('=Ë Detailed Data')

    display_df = metrics_df[['event_date', 'site_domain', 'device_type', 'daily_ctr_percentage', 'daily_total_clicks', 'daily_total_impressions']].copy()
    display_df.columns = ['Date', 'Site', 'Device', 'CTR (%)', 'Clicks', 'Impressions']

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # Download button
    st.markdown('---')
    csv = display_df.to_csv(index=False)
    st.download_button(
        label='=å Download as CSV',
        data=csv,
        file_name=f'metrics_{start_date}_{end_date}.csv',
        mime='text/csv'
    )

if __name__ == '__main__':
    main()
