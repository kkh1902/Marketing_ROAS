# 3주 실행 계획 (Marketing ROAS 프로젝트)

## 📅 개요

Avazu 광고 데이터를 기반으로 실시간 CTR(Click-Through Rate) 분석 및 배치 처리 파이프라인을 구축하는 3주 프로젝트입니다.

**프로젝트 기간:** 3주 (21일)
**목표:** 완전한 데이터 파이프라인 구축 및 모니터링 시스템 완성

---

## 📊 주간 계획 요약

| 주차 | 주제 | 핵심 산출물 | 진행률 |
|------|------|---------|--------|
| **1주** | 데이터 수집 & 스트리밍 기초 | Kafka + Producer | 0% |
| **2주** | 실시간 처리 & 캐싱 | PyFlink + Redis + Streamlit | 0% |
| **3주** | 배치 처리 & 모니터링 | Airflow + dbt + Grafana | 0% |

---

## 🏗️ 시스템 아키텍처 (최종)

```
[Avazu Data]
    ↓
[Kafka Producer] → [Kafka Topics] → [PyFlink]
                                        ↓
                        [Redis Cache] + [PostgreSQL] ← [Airflow/dbt]
                                        ↓
                        [Streamlit] + [Metabase] + [Grafana]
                                        ↓
                        [Slack Alerts]
```

---

## 📝 상세 계획

### [Week 1: 데이터 수집 & 스트리밍 기초](./1week/README.md)
**목표:** Kafka 클러스터 구축 및 데이터 수집 파이프라인 완성

**주요 작업:**
- Avazu 데이터 분석 및 전처리
- Kafka + Schema Registry 구축
- Python Kafka Producer 개발
- 기본 모니터링 설정

**일정:** 6일
**예상 산출물:**
- Docker Compose 설정
- Kafka Producer 코드
- Schema Registry 스키마

---

### [Week 2: 실시간 처리 & 캐싱](./2week/README.md)
**목표:** 실시간 데이터 처리 및 즉시 조회 가능한 캐시 구축

**주요 작업:**
- PyFlink 스트리밍 작업 개발
- Tumbling Window (1분, 5분) 구현
- Redis 캐시 시스템 구축
- PostgreSQL realtime 데이터베이스
- Streamlit 대시보드 개발

**일정:** 10일
**예상 산출물:**
- PyFlink 스트리밍 작업
- Redis 캐시 관리자
- Streamlit 대시보드

---

### [Week 3: 배치 처리 & 모니터링 완성](./3week/README.md)
**목표:** 일배치 처리, 데이터 품질 보증, 완전한 모니터링 시스템 완성

**주요 작업:**
- Airflow DAG 구축 (일배치)
- dbt 모델 설계 및 구현
- DLQ 에러 처리 시스템
- Prometheus + Grafana 모니터링
- Metabase 분석 대시보드
- Slack 알림 통합
- 운영 문서화

**일정:** 10일
**예상 산출물:**
- Airflow DAG 4개
- dbt 모델 (mart 4개)
- Grafana 대시보드
- Metabase 대시보드
- 운영 가이드

---

## 🎯 각 주차별 마일스톤

### Week 1 마일스톤
- ✅ Kafka 클러스터 정상 작동
- ✅ 10,000건 이상 메시지 발행 완료
- ✅ 메시지 수신 확인

### Week 2 마일스톤
- ✅ PyFlink 스트리밍 작업 실행 중
- ✅ 1분, 5분 단위 CTR 계산 완료
- ✅ Streamlit 대시보드 실시간 표시

### Week 3 마일스톤
- ✅ 모든 DAG 정상 실행
- ✅ dbt 테스트 100% 통과
- ✅ 모니터링 시스템 완성

---

## 💻 기술 스택

| 계층 | 기술 | 용도 |
|------|------|------|
| **수집** | Python, Kafka | 데이터 수집 및 스트리밍 |
| **처리** | PyFlink | 실시간 스트리밍 처리 |
| **저장** | PostgreSQL, Redis | 데이터 저장 및 캐싱 |
| **변환** | dbt | 데이터 변환 및 테스트 |
| **스케줄** | Airflow | 배치 작업 스케줄링 |
| **분석** | Streamlit, Metabase | 대시보드 및 분석 |
| **모니터링** | Prometheus, Grafana | 메트릭 수집 및 시각화 |
| **알림** | Slack | 실시간 알림 |
| **인프라** | Docker | 컨테이너화 |

---

## 📋 리소스 요구사항

### 하드웨어
- CPU: 8 cores 이상
- 메모리: 16GB 이상
- 디스크: 50GB 이상

### 소프트웨어
- Docker & Docker Compose
- Python 3.9+
- Git

---

## ⚠️ 주요 위험요소 및 대응

| 위험 | 영향 | 대응 |
|------|------|------|
| 메모리 부족 | 파이프라인 중단 | 데이터 샘플링, 체크포인트 최적화 |
| Kafka 메시지 손실 | 데이터 누락 | replication factor 설정, 백업 구성 |
| 레이턴시 증가 | 실시간 성능 저하 | 캐시 최적화, 파이프라인 병렬화 |
| 데이터 품질 | 분석 신뢰도 하락 | dbt 테스트, 스키마 검증 |

---

## 📞 연락처 및 지원

문제가 발생하거나 질문이 있으면:
1. 해당 주차의 README.md 참고
2. `docs/TROUBLESHOOTING.md` 확인
3. 팀 회의에서 논의

---

## 🚀 다음 단계

프로젝트 완료 후:
1. 클라우드 환경 마이그레이션 검토
2. 머신러닝 모델 통합 계획
3. 성능 벤치마크 및 최적화
4. 운영 체계 안정화

---

**마지막 업데이트:** 2025-12-03
**프로젝트 상태:** 준비 중 (Week 1 시작 전)
