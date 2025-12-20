# Airflow Docker Image
FROM apache/airflow:2.7.0-python3.10

# Set working directory
WORKDIR /airflow

# Set environment variables
ENV AIRFLOW_HOME=/airflow \
    PYTHONUNBUFFERED=1 \
    AIRFLOW__CORE__DAGS_FOLDER=/airflow/dags \
    AIRFLOW__CORE__BASE_LOG_FOLDER=/airflow/logs \
    AIRFLOW__CORE__LOAD_EXAMPLES=False \
    AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS=False

# Switch to root to install packages
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy requirements file
COPY requirements.txt /airflow/

# Install Python dependencies
RUN pip install --no-cache-dir -r /airflow/requirements.txt

# Copy Airflow configuration
COPY config/airflow.cfg $AIRFLOW_HOME/

# Create necessary directories
RUN mkdir -p $AIRFLOW_HOME/dags \
    && mkdir -p $AIRFLOW_HOME/logs \
    && mkdir -p $AIRFLOW_HOME/plugins \
    && mkdir -p $AIRFLOW_HOME/config

# Copy DAGs
COPY dags/ $AIRFLOW_HOME/dags/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=5 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Expose ports
EXPOSE 8080 5555

# Default command (webserver)
CMD ["airflow", "webserver"]
