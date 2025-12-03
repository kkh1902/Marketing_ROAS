# 🌿 브랜칭 가이드

## 개요

이 문서는 Trunk-Based Development에서 브랜칭의 모든 것을 다룹니다.

---

## 브랜치 종류와 역할

### 1. Main 브랜치 (Trunk)

```bash
# main 브랜치
# - 프로덕션 배포 가능한 상태
# - 모든 feature는 여기로 병합
# - 직접 커밋 금지 (PR 필수)
```

**보호 규칙 (Protection Rules):**
- PR 없이 직접 push 불가
- 최소 1명 이상 리뷰 필수
- 모든 자동 테스트 통과 필수
- 최신 main 상태 유지 필수

### 2. Feature 브랜치 (개인 작업)

```bash
feature/google-ads-collector      # 새 기능
feature/bigquery-schema-fix       # 기능 개선
feature/staging-processor         # 모듈 구현
```

**특징:**
- 최대 2-5일 수명
- main에서 생성
- 작은 단위의 기능 (PR당 500줄 이하 권장)
- 매일 커밋하고 push

### 3. Bugfix 브랜치 (긴급 수정)

```bash
bugfix/data-validation-error      # 버그 수정
bugfix/timezone-handling-issue    # 긴급 패치
```

**특징:**
- feature와 동일한 규칙
- 우선순위 높음 (빠르게 병합)
- 재현 가능한 테스트 필수

### 4. Docs 브랜치 (문서)

```bash
docs/api-setup-guide             # 문서 추가
docs/deployment-procedure        # 문서 수정
```

**특징:**
- 코드 변경 없음
- 빠른 리뷰 가능
- 소규모 PR

---

## 브랜치 생명주기

### 생성 (Create)

```bash
# 1. main 최신 상태로 업데이트
git checkout main
git pull origin main

# 2. feature 브랜치 생성
git checkout -b feature/my-feature

# 3. 원격에 push (추적)
git push origin feature/my-feature

# 4. upstream 설정 (선택사항)
git branch --set-upstream-to=origin/feature/my-feature
```

### 개발 (Development) - 2-5일

```bash
# 매일 commit (최소 1회)
git add .
git commit -m "feat: 기능 구현"
git push origin feature/my-feature

# 다음날, 최신 main 반영 (필요시)
git fetch origin main
git rebase origin/main

# 또는 merge (prefer rebase)
git merge origin/main
```

### 리뷰 (Review)

```bash
# GitHub/GitLab에서:
# 1. Pull Request 생성
# 2. 자동 테스트 실행
# 3. 코드 리뷰
# 4. Feedback 반영
# 5. Approve
```

### 병합 (Merge)

```bash
# GitHub UI에서 "Squash and merge" 클릭
# 또는 CLI:

git checkout main
git pull origin main
git merge --squash feature/my-feature
git commit -m "feat: 설명"
git push origin main

# 또는
git checkout feature/my-feature
git rebase main
git checkout main
git merge --ff-only feature/my-feature
git push origin main
```

### 정리 (Cleanup)

```bash
# 로컬 브랜치 삭제
git branch -d feature/my-feature

# 원격 브랜치 삭제
git push origin --delete feature/my-feature

# 또는 GitHub UI에서 "Delete branch" 클릭
```

---

## 브랜치명 규칙

### 규칙

```
<type>/<description-with-hyphens>
```

### Type별 예시

```bash
# Feature (새 기능/개선)
feature/google-ads-api-integration
feature/bigquery-metrics-table
feature/airflow-dag-scheduling
feature/looker-studio-dashboard

# Bugfix (버그 수정)
bugfix/data-validation-error
bugfix/timezone-handling-bug
bugfix/memory-leak-processor

# Docs (문서)
docs/api-setup-guide
docs/deployment-manual
docs/troubleshooting-guide

# Chore (설정/의존성)
chore/upgrade-python-version
chore/update-dependencies
```

### 이름 짓기 팁

```bash
# ✅ Good
feature/google-ads-collector-retry-logic
feature/add-slack-notification

# ❌ Bad
feature/fix
feature/update
feature/new-feature
feature/123
feature/my_feature  # 언더스코어 대신 하이픈 사용
```

---

## 브랜치 전환 및 관리

### 브랜치 목록 조회

```bash
# 로컬 브랜치만
git branch

# 원격 포함
git branch -a

# 상세 정보 (마지막 커밋)
git branch -v

# main으로부터의 거리
git branch -v --ahead-behind
```

### 브랜치 전환

```bash
# Checkout
git checkout feature/my-feature

# 또는 (최신 Git)
git switch feature/my-feature

# 새 브랜치 생성 + 전환
git checkout -b feature/new-feature
git switch -c feature/new-feature
```

### 브랜치 삭제

```bash
# 로컬만
git branch -d feature/my-feature

# 강제 삭제 (병합 안 됨)
git branch -D feature/my-feature

# 원격
git push origin --delete feature/my-feature
```

### 브랜치 이름 변경

```bash
# 현재 브랜치 이름 변경
git branch -m new-name

# 다른 브랜치 이름 변경
git branch -m old-name new-name

# 원격 반영
git push origin --delete old-name
git push origin new-name
```

---

## 브랜치 동기화

### Main 브랜치 최신화

```bash
# 방법 1: Merge (권장 - 히스토리 보존)
git fetch origin main
git merge origin/main

# 방법 2: Rebase (깔끔한 히스토리)
git fetch origin main
git rebase origin/main

# 방법 3: Pull (fetch + merge)
git pull origin main
```

### 로컬 main과 원격 main 동기화

```bash
git checkout main
git pull origin main
```

### 모든 브랜치 정리

```bash
# 병합된 로컬 브랜치 삭제
git branch --merged | grep -v main | xargs git branch -d

# 원격에서 삭제된 브랜치 로컬에서도 정리
git remote prune origin
```

---

## 일반적인 시나리오

### 시나리오 1: Feature 개발 중 main 업데이트 필요

```bash
# 상황: main에 새 기능이 병합됨
# 현재: feature/my-feature 브랜치
# 필요: 최신 main 반영

git fetch origin main
git rebase origin/main

# 충돌 발생 시
git status  # 충돌 파일 확인
# → 에디터에서 수정
git add .
git rebase --continue
```

### 시나리오 2: Feature 병합 후 새 기능 시작

```bash
# 상황: feature/google-ads-collector 병합 완료
# 필요: 다음 feature 시작

# 1. main 업데이트
git checkout main
git pull origin main

# 2. 새 feature 브랜치 생성
git checkout -b feature/bigquery-schema

# 3. 작업...
```

### 시나리오 3: 실수로 main에 커밋함

```bash
# 상황: 실수로 main에 직접 커밋
# 현재 커밋: abc1234

# 1. 커밋 되돌리기
git reset --soft HEAD~1

# 2. feature 브랜치 생성
git checkout -b feature/fix-something

# 3. 다시 커밋
git commit -m "feat: ..."
git push origin feature/fix-something
```

### 시나리오 4: 오래된 브랜치 업데이트

```bash
# 상황: feature/old-feature (2주 됨)
# 필요: 최신 main 반영

git fetch origin main
git rebase origin/main

# 또는
git merge origin/main

# push
git push origin feature/old-feature -f  # ⚠️ 주의: rebase 후 -f 필요
```

---

## 모범 사례

### DO ✅

```bash
# 1. 작은 단위 기능 (500줄 이하)
feature/google-ads-api-client        ✅

# 2. Descriptive한 이름
feature/add-retry-logic-to-collector ✅

# 3. 자주 커밋 (하루 1회 이상)
git commit -m "feat: 단계별 구현"     ✅
git push origin feature/...            ✅

# 4. main과 최신 상태 유지
git pull origin main                   ✅
git rebase origin/main                 ✅

# 5. PR 생성 전 테스트
pytest tests/                          ✅
flake8 src/                            ✅
```

### DON'T ❌

```bash
# 1. 장시간 브랜치 (2주+)
feature/everything                     ❌

# 2. 모호한 이름
feature/update                         ❌
feature/fix                            ❌

# 3. 몰아서 commit (일주일 후 한 번)
git commit -m "everything done"        ❌

# 4. 오래된 main 상태
git rebase origin/main (안 함)         ❌

# 5. PR 없이 병합
git push origin feature/... to main    ❌
```

---

## 명령어 참고

### 자주 사용하는 명령어

```bash
# 조회
git branch                  # 로컬 브랜치
git branch -a               # 전체 브랜치
git log --oneline           # 커밋 히스토리

# 생성/전환
git checkout -b feature/... # 새 브랜치 생성 및 전환
git switch feature/...      # 브랜치 전환

# 커밋
git add .
git commit -m "feat: ..."
git push origin feature/...

# 동기화
git fetch origin main       # 원격 main 가져오기
git pull origin main        # main 병합
git rebase origin/main      # main 리베이스

# 정리
git branch -d feature/...   # 브랜치 삭제
git push origin --delete... # 원격 삭제
```

### 고급 명령어

```bash
# 마지막 커밋 되돌리기
git reset --soft HEAD~1     # 스테이징 유지
git reset --hard HEAD~1     # 완전 삭제

# 특정 커밋으로 되돌리기
git reset --hard abc1234

# cherry-pick (특정 커밋만 가져오기)
git cherry-pick abc1234

# 리베이스 (깔끔한 히스토리)
git rebase origin/main

# 강제 푸시 (주의!)
git push origin feature/... -f
```

---

## 체크리스트

### 브랜치 생성 시
- [ ] main에서 생성
- [ ] 의미있는 이름
- [ ] 즉시 원격 push

### 개발 중
- [ ] 하루 1회 이상 commit
- [ ] 매일 push
- [ ] main 최신화 (주 1-2회)
- [ ] 500줄 이하 유지

### PR 생성 전
- [ ] 로컬 테스트 완료
- [ ] Lint 통과
- [ ] 민감 정보 확인
- [ ] main과 최신 상태

### 병합 후
- [ ] 로컬/원격 브랜치 삭제
- [ ] main 최신화
- [ ] 새 브랜치로 전환

---

## 참고 자료

- [Git 공식 문서](https://git-scm.com/doc)
- [GitHub 브랜칭 전략](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-branches)
