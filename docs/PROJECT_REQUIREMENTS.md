# 광고 캠페인 분석 자동화 플랫폼

## 프로젝트 개요

Google Ads / Meta Ads / Naver Ads 등 다채널 광고 데이터를 자동 수집·정제·가공하여

매일 새벽 자동 업데이트되는 **통합 마케팅 대시보드**를 제공하는 엔드투엔드 데이터 파이프라인

## 1. 핵심 기능 요구사항

| ID | 기능 | 상세 요구사항 | 우선순위 |
| --- | --- | --- | --- |
| F1 | 다채널 데이터 수집 | • Google Ads, Meta Ads, Naver Ads API 지원<br>• (개발 중) Kaggle + Mock API 대체 가능<br>• 일별 데이터 추출 | 필수 |
| F2 | Raw 데이터 저장 | • 수집된 원본 JSON/CSV → S3 또는 GCS에 저장<br>• 날짜 파티셔닝 (`year/month/day`) | 필수 |
| F3 | 스키마 통합 (Staging) | 서로 다른 채널의 필드를 아래 공통 스키마로 정규화 | 필수 |
| F4 | 지표 계산 (Curated) | Airflow 내에서 자동 계산 후 적재<br>• CTR, CPC, CPA, ROAS, CVR | 필수 |
| F5 | DWH 적재 | BigQuery (또는 Snowflake)<br>• raw → staging → metrics 3계층<br>• date 파티션 + campaign_id 클러스터링 | 필수 |
| F6 | 대시보드 자동 리프레시 | Looker Studio 또는 Metabase<br>• 주요 차트 5개 이상<br>• 매일 새벽 자동 업데이트 | 필수 |
| F7 | 스케줄링 및 모니터링 | Apache Airflow로 전체 파이프라인 오케스트레이션<br>• 매일 새벽 3시 실행<br>• 실패 시 Slack/Email 알림 | 필수 |
| F8 | 실제 광고 연계 (선택) | Google Ads 500원 소액 캠페인 집행 → 실 데이터 API 수집 (가산점용) | 선택 |

## 2. 공통 스키마 (Staging → Metrics)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| date | DATE | 데이터 발생일 |
| campaign_id | STRING | 캠페인 ID |
| campaign_name | STRING | 캠페인 이름 |
| channel | STRING | Google / Meta / Naver |
| impressions | INT64 | 노출 수 |
| clicks | INT64 | 클릭 수 |
| spend | FLOAT64 | 광고비 (원) |
| conversions | INT64 | 전환 수 |
| sales | FLOAT64 | 매출액 (ROAS 계산용) |
| ctr | FLOAT64 | clicks / impressions |
| cpc | FLOAT64 | spend / clicks |
| cpa | FLOAT64 | spend / conversions |
| roas | FLOAT64 | sales / spend |
| cvr | FLOAT64 | conversions / clicks |

## 3. 기술 스택

| 레이어 | 기술 |
| --- | --- |
| 데이터 수집 | Google·Meta·Naver Ads API / FastAPI Mock |
| 오케스트레이션 | Apache Airflow (Docker Compose) |
| 스토리지 | Google Cloud Storage 또는 AWS S3 |
| DWH | Google BigQuery |
| BI Tool | Looker Studio (주력) 또는 Metabase |
| 언어/라이브러리 | Python, Pandas, SQL |

## 4. 비기능 요구사항

- 전체 파이프라인 실패 시 Slack 또는 Email 알림
- Raw 데이터 90일 이상 보관
- Staging → Metrics 지연 시간 10분 이내 목표
- 대시보드 일일 자동 리프레시

## 5. 프로젝트 성공 기준 (완성 조건)

1. 매일 새벽 3시 자동으로 최신 데이터가 BigQuery `metrics` 테이블에 적재되는가?
2. Looker Studio 대시보드가 매일 자동으로 최신 데이터 반영되는가?
3. 채널별·캠페인별 ROAS 1위와 최하위 캠페인을 한눈에 확인할 수 있는가?

→ 위 3개 충족 시 실무 즉시 투입 가능한 DE 포트폴리오 완성

---

문서 작성일: 2025-11-29

프로젝트 기간: 1개월
