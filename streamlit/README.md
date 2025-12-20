# 📊 Streamlit - Real-time Dashboard

Streamlit을 활용한 **실시간 광고 클릭 데이터 분석 대시보드**입니다.
PostgreSQL의 실시간 데이터를 시각화하여 CTR 메트릭을 모니터링합니다.

---

## 📦 구조

```
streamlit/
├── README.md                      # 이 파일
├── requirements.txt               # Python 의존성 (streamlit, plotly, pandas)
├── config.py                      # 데이터베이스 및 앱 설정
├── realtime_dashboard.py          # 메인 대시보드
├── Dockerfile                     # Streamlit 컨테이너 환경
│
└── pages/                         # 멀티페이지 구성
    ├── metrics.py                 # 상세 메트릭 분석
    └── alerts.py                  # 이상 탐지 및 알림
```

---

## 🎯 기능

### **Main Dashboard (realtime_dashboard.py)**
```
실시간 CTR 메트릭 표시
├─ 현재 CTR (큰 숫자로 표시)
├─ 시간별 트렌드 (라인 차트)
├─ 사이트별 CTR (막대 차트)
├─ 디바이스 타입별 분포 (파이 차트)
└─ 실시간 업데이트 (5초마다 새로고침)
```

### **Metrics Page (pages/metrics.py)**
```
상세 분석
├─ 일별 CTR 추이
├─ 시간대별 성능 비교
├─ 사이트별 상세 통계
├─ 디바이스 타입별 성과
└─ 필터링 (날짜, 사이트, 디바이스)
```

### **Alerts Page (pages/alerts.py)**
```
이상 탐지 및 알림
├─ CTR 급변 감지 (100% 이상 변화)
├─ 데이터 부재 감지 (신규 데이터 없음)
├─ 성능 저하 경고 (임계값 이하)
└─ 알림 히스토리
```

---

## 🚀 실행 방법

### **1️⃣ 설치**

```bash
# 프로젝트 폴더로 이동
cd streamlit

# 가상환경 활성화 (선택사항)
source venv/Scripts/activate

# 의존성 설치
pip install -r requirements.txt
```

### **2️⃣ 설정 확인**

`config.py` 파일에서 PostgreSQL 연결 정보 확인:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'marketing_roas'
}
```

### **3️⃣ 대시보드 실행**

```bash
# 메인 페이지 실행 (포트 8501)
streamlit run realtime_dashboard.py

# 또는 다른 포트 사용
streamlit run realtime_dashboard.py --server.port 8502
```

### **4️⃣ 웹 브라우저 접속**

```
http://localhost:8501
```

---

## 📊 페이지별 설명

### **Main Dashboard**

**위치**: `realtime_dashboard.py`

**화면 구성**:
```
┌─────────────────────────────────────┐
│  Realtime CTR Monitoring Dashboard  │
├─────────────────────────────────────┤
│                                     │
│  Current CTR: 16.5% ↑ 0.3%          │
│                                     │
│  [라인 차트] 시간별 CTR 추이          │
│                                     │
│  [막대 차트] 사이트별 CTR             │
│  [파이 차트] 디바이스 분포            │
│                                     │
│  Last Updated: 2024-12-20 12:34:56 │
└─────────────────────────────────────┘
```

**데이터 갱신**: 5초 자동 새로고침

### **Metrics Page**

**위치**: `pages/metrics.py`

**기능**:
- 📈 일별 CTR 추이 분석
- 🕐 시간대별 성능 비교
- 🌐 사이트별 상세 통계
- 📱 디바이스 타입별 성과
- 🔍 날짜/사이트/디바이스 필터링

**쿼리**:
```sql
SELECT
    event_date,
    site_id,
    device_type,
    daily_ctr_percentage,
    daily_total_clicks,
    daily_total_impressions
FROM analytics.fct_daily_metrics
WHERE event_date >= date_trunc('day', now()) - interval '30 days'
ORDER BY event_date DESC
```

### **Alerts Page**

**위치**: `pages/alerts.py`

**감지 항목**:
1. **CTR 급변** (1000% 이상 변화)
   ```sql
   WHERE abs(clicks_dod_pct_change) > 1000
   ```

2. **데이터 부재** (최근 1시간 신규 데이터 없음)
   ```sql
   WHERE max(event_date) < now() - interval '1 hour'
   ```

3. **성능 저하** (CTR < 15%)
   ```sql
   WHERE daily_ctr_percentage < 15
   ```

---

## 🔧 설정 파일

### **config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL 연결
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'marketing_roas')
}

# Streamlit 설정
STREAMLIT_CONFIG = {
    'page_title': 'CTR Monitoring Dashboard',
    'page_icon': '📊',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# 대시보드 설정
DASHBOARD_CONFIG = {
    'refresh_interval': 5,        # 5초마다 새로고침
    'chart_height': 400,
    'max_rows': 1000,
    'timezone': 'UTC'
}
```

### **requirements.txt**

```
streamlit==1.31.0
pandas==2.1.0
plotly==5.18.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
sqlalchemy==2.0.23
```

---

## 📈 사용 사례

### **1. 실시간 모니터링**
```
09:00 - 매일 아침 대시보드 확인
      - 어제 CTR 추이
      - 이상 탐지 알림 확인
      - 주요 메트릭 요약
```

### **2. 성능 분석**
```
17:00 - 일일 리포트 작성
      - 사이트별 성능 비교
      - 디바이스별 CTR 분석
      - 시간대별 트렌드
```

### **3. 이슈 대응**
```
12:30 - CTR 급변 감지
      - 알림 페이지 확인
      - 원인 분석
      - 팀과 공유
```

---

## 🐳 Docker 실행

### **이미지 빌드**

```bash
docker build -t streamlit-dashboard:latest .
```

### **컨테이너 실행**

```bash
docker run -p 8501:8501 \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=marketing_roas \
  streamlit-dashboard:latest
```

### **Docker Compose 통합**

```yaml
services:
  streamlit:
    build: ./streamlit
    ports:
      - "8501:8501"
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: marketing_roas
    depends_on:
      - postgres
```

```bash
docker-compose up -d streamlit
```

---

## 🔍 트러블슈팅

### Q: PostgreSQL 연결 안 됨
```bash
# PostgreSQL 실행 확인
docker-compose ps postgres

# 연결 테스트
psql -h localhost -U postgres -d marketing_roas -c "SELECT COUNT(*) FROM analytics.fct_daily_metrics;"
```

### Q: 대시보드 로딩 느림
```python
# config.py에서 새로고침 간격 조정
'refresh_interval': 10  # 10초로 변경
```

### Q: 데이터가 없음
```bash
# dbt 모델 실행 확인
airflow dags list
airflow tasks list dag_dbt_run

# 수동 실행
cd /dbt
dbt run
```

### Q: 포트 충돌
```bash
# 다른 포트 사용
streamlit run realtime_dashboard.py --server.port 8502
```

---

## 📊 성능 최적화

### **1. 데이터 캐싱**

```python
@st.cache_data(ttl=300)  # 5분 캐시
def load_metrics():
    # 데이터 로드
    pass
```

### **2. 쿼리 최적화**

```python
# 필터링을 SQL에서 수행
query = f"""
SELECT * FROM analytics.fct_daily_metrics
WHERE event_date >= '{start_date}'
  AND site_id = '{selected_site}'
"""
```

### **3. 비동기 로딩**

```python
import asyncio

async def load_data():
    # 병렬로 여러 쿼리 실행
    pass
```

---

## 🎨 커스터마이징

### **테마 변경**

`.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### **차트 커스터마이징**

```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=data['event_date'],
    y=data['daily_ctr_percentage'],
    mode='lines+markers',
    name='CTR (%)',
    line=dict(color='#FF4B4B', width=2)
))
fig.update_layout(
    title='Daily CTR Trend',
    xaxis_title='Date',
    yaxis_title='CTR (%)',
    hovermode='x unified'
)
st.plotly_chart(fig, use_container_width=True)
```

---

## 📅 개발 일정

| 단계 | 작업 | 상태 |
|------|------|------|
| 1 | realtime_dashboard.py 구현 | 🔄 진행중 |
| 2 | pages/metrics.py 구현 | ⏳ 대기 |
| 3 | pages/alerts.py 구현 | ⏳ 대기 |
| 4 | Docker 통합 | ⏳ 대기 |
| 5 | 성능 최적화 | ⏳ 대기 |

---

## 🔗 관련 문서

- [Streamlit 공식 문서](https://docs.streamlit.io/)
- [Plotly 차트](https://plotly.com/python/)
- [PostgreSQL 쿼리](../schemas/realtime_ctr_metrics.sql)
- [dbt 모델](../dbt/README.md)
- [Airflow DAG](../airflow/README.md)

---

## 💡 Best Practices

### ✅ DO
- 데이터 캐싱 활용 (성능)
- 필터링은 SQL에서 수행 (효율성)
- 에러 처리 추가 (안정성)
- 실시간 업데이트 설정 (UX)

### ❌ DON'T
- 모든 데이터 로드 후 필터링
- 동기 쿼리로 블로킹 (UI 느려짐)
- 캐시 없이 매번 조회
- 하드코딩된 연결 정보

---

**마지막 업데이트**: 2024-12-20
**상태**: 개발 진행중 🚀
