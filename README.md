# 광고 캠페인 분석 자동화 플랫폼

> **Google Ads / Meta Ads / Naver Ads** 다채널 광고 데이터를 자동 수집·정제·가공하여
> 매일 새벽 자동 업데이트되는 **통합 마케팅 대시보드**를 제공하는 엔드투엔드 데이터 파이프라인

---

## 📋 프로젝트 개요

### 핵심 가치
- **자동화**: 매일 새벽 3시 자동으로 최신 광고 데이터 적재
- **통합 관리**: 3개 광고 플랫폼 데이터를 하나의 스키마로 통합
- **즉시 활용**: Looker Studio 대시보드로 ROAS 분석 자동화

### 기대 효과
- 광고 성과 모니터링 자동화
- 채널별·캠페인별 ROAS 한눈에 파악
- 의사결정 속도 향상

---

## 🏗️ 프로젝트 구조

```
marketing_roas/
├── docs/
│   ├── PROJECT_REQUIREMENTS.md    # 상세 요구사항 명세
│   ├── ARCHITECTURE.md            # 파이프라인 아키텍처
│   ├── API_SETUP.md               # 각 광고 API 설정 가이드
│   └── DEPLOYMENT.md              # 배포 가이드
│
├── src/
│   ├── __init__.py
│   ├── config.py                  # 환경 설정 및 credential
│   ├── collectors/                # 데이터 수집 모듈
│   │   ├── __init__.py
│   │   ├── google_ads.py          # Google Ads API
│   │   ├── meta_ads.py            # Meta Ads API
│   │   ├── naver_ads.py           # Naver Ads API
│   │   └── mock_api.py            # Mock 데이터 (개발용)
│   │
│   ├── processors/                # 데이터 처리 모듈
│   │   ├── __init__.py
│   │   ├── raw_storage.py         # Raw 데이터 GCS/S3 저장
│   │   ├── staging.py             # Staging 스키마 정규화
│   │   ├── metrics.py             # 지표 계산 (ROAS, CPC 등)
│   │   └── validators.py          # 데이터 검증
│   │
│   ├── warehouse/                 # DWH 레이어
│   │   ├── __init__.py
│   │   ├── bigquery.py            # BigQuery 클라이언트
│   │   ├── schemas.py             # 테이블 스키마 정의
│   │   └── sql/                   # 쿼리 템플릿
│   │       ├── raw.sql
│   │       ├── staging.sql
│   │       └── metrics.sql
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # 로깅
│       ├── slack_notifier.py      # Slack 알림
│       └── error_handler.py       # 에러 처리
│
├── airflow/
│   ├── dags/
│   │   ├── __init__.py
│   │   └── marketing_pipeline.py  # 메인 DAG
│   │
│   ├── plugins/
│   │   └── operators/             # 커스텀 Operator
│   │
│   └── config/                    # Airflow 설정
│       └── airflow.cfg
│
├── tests/
│   ├── __init__.py
│   ├── test_collectors.py         # 수집 모듈 테스트
│   ├── test_processors.py         # 처리 모듈 테스트
│   └── test_e2e.py                # E2E 테스트
│
├── docker-compose.yml             # Airflow 로컬 환경
├── requirements.txt               # Python 패키지
├── .env.example                   # 환경변수 템플릿
├── setup.py                       # 패키지 설정
└── README.md                      # 이 파일
```

---

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.9+
- Docker & Docker Compose
- GCP (BigQuery, GCS) 또는 AWS (Snowflake, S3) 계정
- Google Ads / Meta Ads / Naver Ads API 접근 권한

### 설치

1. **저장소 클론 및 의존성 설치**
   ```bash
   git clone <repository-url>
   cd marketing_roas

   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **환경 변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일에 GCP 인증, API 키 등을 입력
   ```

3. **Airflow 시작 (Docker Compose)**
   ```bash
   docker-compose up -d
   # http://localhost:8080 에서 Airflow UI 접속
   ```

4. **DAG 배포**
   ```bash
   cp airflow/dags/* <AIRFLOW_HOME>/dags/
   ```

---

## 📊 핵심 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| **F1** 다채널 데이터 수집 | 🔄 | Google/Meta/Naver Ads API |
| **F2** Raw 데이터 저장 | 🔄 | GCS/S3에 날짜별 파티셔닝 |
| **F3** 스키마 통합 | 🔄 | 공통 스키마로 정규화 |
| **F4** 지표 계산 | 🔄 | CTR, CPC, CPA, ROAS, CVR |
| **F5** DWH 적재 | 🔄 | BigQuery 3계층 (raw/staging/metrics) |
| **F6** 대시보드 | ⏳ | Looker Studio 자동 리프레시 |
| **F7** Airflow 스케줄링 | ⏳ | 매일 새벽 3시 자동 실행 |
| **F8** 실제 광고 연계 | ⏳ | (선택) Google Ads 소액 캠페인 |

---

## 🏆 성공 기준 (MVP)

1. ✅ 매일 새벽 3시 BigQuery `metrics` 테이블에 최신 데이터 적재
2. ✅ Looker Studio 대시보드 자동 리프레시 (매일 새벽 4시)
3. ✅ 채널별·캠페인별 ROAS Top/Bottom 5 한눈에 확인

---

## 📚 문서

- [PROJECT_REQUIREMENTS.md](docs/PROJECT_REQUIREMENTS.md) - 상세 요구사항
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 기술 아키텍처 (준비 중)
- [API_SETUP.md](docs/API_SETUP.md) - API 설정 가이드 (준비 중)

---

## 🛠️ 기술 스택

| 레이어 | 기술 |
|--------|------|
| **데이터 수집** | Python, FastAPI, Google/Meta/Naver Ads APIs |
| **오케스트레이션** | Apache Airflow |
| **스토리지** | Google Cloud Storage (GCS) / AWS S3 |
| **데이터 웨어하우스** | Google BigQuery |
| **BI Tool** | Looker Studio |
| **언어** | Python, SQL |

---

## 📈 데이터 흐름

```
Google Ads API ─┐
Meta Ads API   ─┼─→ [수집] → [Raw Storage] → [Staging] → [Metrics] → [BigQuery] → [Looker Studio]
Naver Ads API  ─┘      │                                                              ↓
                      Airflow                                              Dashboard (ROAS분석)
                    (매일 3시)
```

---

## 🔔 알림 설정

- **Slack**: DAG 실패 시 실시간 알림
- **Email**: 일일 파이프라인 실행 결과 리포트

---

## 🤝 기여 가이드

1. Feature Branch 생성: `git checkout -b feature/new-feature`
2. 커밋: `git commit -am 'Add new feature'`
3. Push: `git push origin feature/new-feature`
4. Pull Request 생성

---

## 📝 라이센스

MIT License

---

## 👤 연락처

프로젝트 관련 문의: [당신의 이메일]

**프로젝트 기간**: 2025-11-29 ~ 2025-12-29 (1개월)
