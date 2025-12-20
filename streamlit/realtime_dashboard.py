import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine
from config import DB_CONFIG, STREAMLIT_CONFIG, DASHBOARD_CONFIG, QUERIES
import time

# Page Configuration
st.set_page_config(**STREAMLIT_CONFIG)

# Custom CSS
st.markdown("""
<style>
    [data-testid="metric.container"] {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

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
@st.cache_data(ttl=5)
def load_current_ctr(engine):
    """Load current CTR metric"""
    try:
        df = pd.read_sql(QUERIES['current_ctr'], engine)
        return df
    except Exception as e:
        st.warning(f"Error loading current CTR: {str(e)}")
        return None

@st.cache_data(ttl=5)
def load_hourly_trend(engine):
    """Load hourly CTR trend"""
    try:
        df = pd.read_sql(QUERIES['hourly_trend'], engine)
        return df
    except Exception as e:
        st.warning(f"Error loading hourly trend: {str(e)}")
        return None

@st.cache_data(ttl=5)
def load_site_performance(engine):
    """Load site performance metrics"""
    try:
        df = pd.read_sql(QUERIES['site_performance'], engine)
        return df
    except Exception as e:
        st.warning(f"Error loading site performance: {str(e)}")
        return None

@st.cache_data(ttl=5)
def load_device_distribution(engine):
    """Load device type distribution"""
    try:
        df = pd.read_sql(QUERIES['device_distribution'], engine)
        return df
    except Exception as e:
        st.warning(f"Error loading device distribution: {str(e)}")
        return None

# ============================================================================
# Chart Functions
# ============================================================================
def create_hourly_trend_chart(df):
    """Create hourly trend line chart"""
    if df is None or df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['ctr_percentage'],
        mode='lines+markers',
        name='CTR (%)',
        line=dict(color='#FF4B4B', width=2),
        marker=dict(size=6),
        hovertemplate='%{x}<br>CTR: %{y:.2f}%<extra></extra>'
    ))

    fig.update_layout(
        title='Hourly CTR Trend (Last 7 Days)',
        xaxis_title='Time',
        yaxis_title='CTR (%)',
        hovermode='x unified',
        height=DASHBOARD_CONFIG['chart_height'],
        template='plotly_light'
    )

    return fig

def create_site_performance_chart(df):
    """Create site performance bar chart"""
    if df is None or df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['site_domain'],
        y=df['ctr_percentage'],
        name='CTR (%)',
        marker=dict(color=df['ctr_percentage'], colorscale='Viridis'),
        hovertemplate='%{x}<br>CTR: %{y:.2f}%<extra></extra>'
    ))

    fig.update_layout(
        title='Site Performance (Last 7 Days)',
        xaxis_title='Site',
        yaxis_title='CTR (%)',
        height=DASHBOARD_CONFIG['chart_height'],
        template='plotly_light',
        xaxis_tickangle=-45
    )

    return fig

def create_device_distribution_chart(df):
    """Create device distribution pie chart"""
    if df is None or df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=df['device_type'],
        values=df['count'],
        name='Count',
        hovertemplate='%{label}<br>Count: %{value}<br>CTR: %{customdata:.2f}%<extra></extra>',
        customdata=df['ctr_percentage']
    ))

    fig.update_layout(
        title='Device Type Distribution (Last 7 Days)',
        height=DASHBOARD_CONFIG['chart_height'],
        template='plotly_light'
    )

    return fig

# ============================================================================
# Main Application
# ============================================================================
def main():
    # Header
    st.title('=Ê Realtime CTR Monitoring Dashboard')
    st.markdown('---')

    # Get database connection
    engine = get_db_connection()

    # Top section: Current Metrics
    st.subheader('Current Metrics')

    col1, col2, col3 = st.columns(3)

    ctr_data = load_current_ctr(engine)
    if ctr_data is not None and not ctr_data.empty:
        current_ctr = ctr_data['ctr_percentage'].iloc[0]
        last_updated = ctr_data['last_updated'].iloc[0]

        with col1:
            st.metric(
                label='Current CTR',
                value=f'{current_ctr:.2f}%',
                delta=None
            )

        with col2:
            st.metric(
                label='Last Updated',
                value=str(last_updated)[:10]
            )

        with col3:
            st.info(f'ñ Auto-refreshing every {DASHBOARD_CONFIG["refresh_interval"]} seconds')

    st.markdown('---')

    # Charts section
    st.subheader('Analytics')

    # Hourly Trend
    hourly_data = load_hourly_trend(engine)
    if hourly_data is not None and not hourly_data.empty:
        hourly_chart = create_hourly_trend_chart(hourly_data)
        if hourly_chart:
            st.plotly_chart(hourly_chart, use_container_width=True)
    else:
        st.info('No hourly trend data available')

    # Site Performance and Device Distribution (side by side)
    col1, col2 = st.columns(2)

    with col1:
        site_data = load_site_performance(engine)
        if site_data is not None and not site_data.empty:
            site_chart = create_site_performance_chart(site_data)
            if site_chart:
                st.plotly_chart(site_chart, use_container_width=True)
        else:
            st.info('No site performance data available')

    with col2:
        device_data = load_device_distribution(engine)
        if device_data is not None and not device_data.empty:
            device_chart = create_device_distribution_chart(device_data)
            if device_chart:
                st.plotly_chart(device_chart, use_container_width=True)
        else:
            st.info('No device distribution data available')

    st.markdown('---')

    # Data Table
    st.subheader('Site Performance Details')
    if site_data is not None and not site_data.empty:
        st.dataframe(
            site_data,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info('No site data available')

    # Footer
    st.markdown('---')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption('=Ê Data refreshes automatically every 5 seconds')
    with col2:
        st.caption('= Real-time monitoring powered by Streamlit')
    with col3:
        st.caption('ð Timezone: UTC')

    # Auto-refresh logic
    st.write('')  # Spacing
    time.sleep(DASHBOARD_CONFIG['refresh_interval'])
    st.rerun()

if __name__ == '__main__':
    main()
