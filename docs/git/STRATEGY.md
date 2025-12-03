# 🌳 Git 전략: Trunk-Based Development

## 📌 개요

이 프로젝트는 **Trunk-Based Development (TBD)** 전략을 채택합니다.

> **Trunk-Based Development**는 모든 개발자가 짧은 수명의 feature 브랜치에서 작업한 후, main 브랜치(Trunk)로 빠르게 병합하는 개발 방식입니다.

### 왜 Trunk-Based Development를 선택했나?

| 기준 | 상황 | 선택 이유 |
|------|------|----------|
| **팀 규모** | 1-2명 (초기 팀) | 소규모 팀에 최적화 |
| **프로젝트 기간** | 1개월 집중 | 빠른 속도 필요 |
| **데이터 파이프라인** | Airflow 기반 자동화 | 기능 독립성 높음 |
| **CI/CD** | 자동화 준비 완료 | 자동 테스트 가능 |
| **배포 전략** | 지속적 통합 (매일) | Feature flags로 제어 |

---

## 🎯 핵심 원칙

### 1. Main 브랜치는 항상 배포 가능해야 함
```
✅ 모든 테스트 통과
✅ 코드 리뷰 완료
✅ 자동 배포 준비 완료
```

### 2. Feature 브랜치는 짧게 (2-5일)
```
main ← feature/collector (1-2일) → merge
main ← feature/processor (2-3일) → merge
main ← feature/dashboard (1-2일) → merge
```

### 3. 하루에 최소 1회 commit & push
- 병렬 작업 충돌 최소화
- 팀 동기화
- 진행 상황 가시성

### 4. Feature flags로 미완성 기능 제어
```python
# 기능이 완료되지 않았으면 배포해도 disable 처리
if ENABLE_FEATURE_X:
    # 새 기능
else:
    # 기존 기능
```

---

## 📊 브랜치 모델

### 브랜치 타입

```
main (프로덕션)
 ↑
 ├─ feature/airflow-dag-setup
 ├─ feature/google-ads-collector
 ├─ feature/staging-processor
 ├─ feature/metrics-calculation
 ├─ feature/looker-dashboard
 ├─ feature/slack-alerting
 └─ bugfix/urgent-data-bug (긴급)
```

### 브랜치명 규칙

**Feature 브랜치:**
```
feature/{기능-영문-하이픈}
feature/google-ads-collector
feature/bigquery-schema-setup
feature/airflow-dag-scheduler
```

**Bugfix 브랜치:**
```
bugfix/{버그-영문-하이픈}
bugfix/data-validation-error
bugfix/timezone-handling
```

**문서/설정:**
```
docs/{내용-영문-하이픈}
docs/api-setup-guide
docs/deployment-guide
```

---

## 🔄 일일 워크플로우

### 아침 (시작)
```bash
# 1. 최신 main 가져오기
git checkout main
git pull origin main

# 2. feature 브랜치 생성
git checkout -b feature/my-feature

# 예시
git checkout -b feature/google-ads-api-setup
```

### 낮 (개발)
```bash
# 자주 commit (최소 2-3회)
git add src/collectors/google_ads.py
git commit -m "feat: Google Ads API 클라이언트 구현"

git add tests/test_google_ads.py
git commit -m "test: Google Ads 수집 테스트 추가"

git add docs/API_SETUP.md
git commit -m "docs: Google Ads API 설정 가이드"

# 하루 중간에 push
git push origin feature/google-ads-api-setup
```

### 저녁 (완료)
```bash
# 최종 push
git push origin feature/google-ads-api-setup

# GitHub/GitLab에서:
# 1. Pull Request 생성
# 2. 자동 테스트 실행 대기
# 3. 코드 리뷰 진행
# 4. Approve 후 main에 merge (Squash merge)
```

### 다음날
```bash
# 새 feature 브랜치 시작
git checkout main
git pull origin main
git checkout -b feature/next-feature
```

---

## ✅ Pull Request 프로세스

### 1. PR 생성 전 체크리스트
```
□ 로컬에서 테스트 완료
□ 린트 통과 (flake8, mypy)
□ 최신 main과 병합됨 (git pull origin main)
□ 민감 정보 없음 (.env, 키 등)
□ 코드 스타일 일관성
```

### 2. PR 제목 규칙
```
feat: Google Ads API 수집기 구현
fix: 데이터 검증 로직 버그 수정
docs: API 설정 가이드 추가
refactor: Processor 클래스 구조 개선
test: E2E 테스트 추가
```

### 3. PR 설명 템플릿
```markdown
## 설명
이 PR은 Google Ads API 수집기를 구현합니다.

## 변경 사항
- API 클라이언트 구현
- 날짜 범위 필터링 추가
- 에러 핸들링 추가

## 테스트
- [ ] 로컬 테스트 완료
- [ ] CI 테스트 통과
- [ ] E2E 테스트 통과

## 관련 이슈
Closes #123

## 리뷰 팁
- src/collectors/google_ads.py: 주요 구현
- tests/test_google_ads.py: 테스트 케이스
```

### 4. 병합 전 필수 조건
```
✅ 모든 자동 테스트 통과
✅ 코드 리뷰 1명 이상 승인
✅ 충돌 해결 완료
✅ main 브랜치 최신 상태
```

### 5. 병합 방식: Squash Merge
```bash
# GitHub UI에서 "Squash and merge" 선택
# 또는 CLI에서:
git checkout main
git pull origin main
git merge --squash feature/my-feature
git commit -m "feat: 설명적인 커밋 메시지"
git push origin main
```

---

## 🛡️ 보안 가이드

### Commit 전 확인사항
```bash
# ❌ 커밋하면 안 되는 것
.env              # 환경 변수
*.key             # API 키
*.pem             # 인증서
credentials.json  # GCP 인증
```

### .gitignore 확인
```bash
# 다음이 모두 무시되는지 확인
git check-ignore .env
git check-ignore credentials.json
git check-ignore data/google_ads.csv

# 만약 이미 커밋되었다면
git filter-branch --tree-filter 'rm -f .env' HEAD
```

---

## 📈 커밋 메시지 규칙

### 컨벤션: Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 종류

| Type | 설명 | 예시 |
|------|------|------|
| **feat** | 새 기능 | `feat: Google Ads 수집기 추가` |
| **fix** | 버그 수정 | `fix: 타임존 처리 오류 수정` |
| **docs** | 문서 | `docs: API 가이드 추가` |
| **refactor** | 코드 정리 | `refactor: Processor 클래스 분리` |
| **test** | 테스트 | `test: Google Ads 수집 테스트` |
| **chore** | 빌드/설정 | `chore: Python 의존성 업그레이드` |

### 좋은 예시

```bash
# 기본
git commit -m "feat: BigQuery 메트릭 테이블 생성"

# 상세한 설명
git commit -m "feat: Airflow DAG 스케줄링 추가

- 매일 새벽 3시 자동 실행
- 재시도 로직 추가 (최대 3회)
- Slack 알림 통합"

# Scope 포함
git commit -m "feat(collectors): Google Ads API 에러 핸들링 개선"
```

---

## 🚀 배포 프로세스

### 프로덕션 배포
```bash
# 1. main 브랜치 최신 상태
git checkout main
git pull origin main

# 2. 태그 생성 (월간 릴리스)
git tag -a v1.0 -m "Monthly release v1.0"
git push origin v1.0

# 3. 자동 배포 (CI/CD)
# GitHub Actions가 자동으로 실행됨
# → 테스트 → 빌드 → 배포
```

---

## 📋 체크리스트

### 프로젝트 시작 시
- [ ] `.gitignore` 강화 (민감 정보)
- [ ] Branch protection 설정 (main)
- [ ] CI/CD 파이프라인 구성
- [ ] 팀 규칙 공유

### 매 feature 마다
- [ ] Descriptive 브랜치명
- [ ] 하루 1회 이상 commit
- [ ] 테스트 코드 작성
- [ ] PR 생성 전 자동 테스트
- [ ] Code review 요청

### Merge 전
- [ ] All tests pass
- [ ] Approval 받음
- [ ] Conflicts 해결됨
- [ ] Feature flags 설정됨

---

## 🔗 관련 문서

- [BRANCHING.md](./BRANCHING.md) - 브랜칭 상세 가이드
- [WORKFLOW.md](./WORKFLOW.md) - 일일 워크플로우
- [FEATURE_FLAGS.md](./FEATURE_FLAGS.md) - Feature flags 구현

---

## 📞 문의사항

Git 전략에 대한 질문은 [프로젝트 리드]에게 문의하세요.
