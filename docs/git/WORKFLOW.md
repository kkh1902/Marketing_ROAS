# 🔄 일일 워크플로우

## 개요

Trunk-Based Development에서 하루 동안 일어나는 작업 흐름을 단계별로 설명합니다.

---

## 전체 흐름도

```
아침 시작
  ↓
[1단계] 준비 - 최신 main 가져오기
  ↓
[2단계] 시작 - feature 브랜치 생성
  ↓
[3단계] 개발 - 코드 작성 및 커밋
  ↓
[4단계] 점심/오후 - 중간 커밋 및 push
  ↓
[5단계] 완료 - 최종 push
  ↓
[6단계] PR - Pull Request 생성
  ↓
[7단계] 리뷰 - 코드 리뷰 및 수정
  ↓
[8단계] 병합 - main에 merge
  ↓
다음날 반복
```

---

## 1단계: 아침 준비 (8:00~8:15)

### 목표
최신 코드를 로컬에 동기화하기

### 명령어

```bash
# 1. 메인 디렉토리로 이동
cd ~/marketing_roas

# 2. main 브랜치로 전환
git checkout main

# 3. 최신 코드 다운로드
git pull origin main

# 4. 브랜치 목록 확인
git branch -a
```

### 확인사항

```bash
# ✅ main 브랜치가 최신 상태인지 확인
git log -1 --oneline main
# 예: abc1234 (HEAD -> main, origin/main) feat: 메트릭 테이블 완료

# ✅ 로컬 변경사항 없는지 확인
git status
# 예: On branch main
#     nothing to commit, working tree clean
```

---

## 2단계: 기능 선택 및 브랜치 생성 (8:15~8:30)

### 목표
오늘 구현할 기능을 정하고 브랜치 생성

### 예시: Google Ads API 수집기 구현

```bash
# 1. main에서 feature 브랜치 생성
git checkout -b feature/google-ads-api-collector

# 2. 원격에 브랜치 push (추적)
git push origin feature/google-ads-api-collector

# 3. upstream 설정 (자동 추적)
git branch --set-upstream-to=origin/feature/google-ads-api-collector
```

### 확인

```bash
git branch -v
# feature/google-ads-api-collector abc1234 [origin/feature/google-ads-api-collector] 최초
# main                             abc1234 [origin/main: 최신]
```

---

## 3단계: 개발 (8:30~12:00)

### 목표
코드 작성 및 자주 커밋하기

### 개발 흐름

```bash
# 1단계: 파일 생성/수정
# editor에서: src/collectors/google_ads.py 작성

# 2단계: 변경사항 확인
git status

# 출력:
# On branch feature/google-ads-api-collector
# Changes not staged for commit:
#   modified:   src/collectors/google_ads.py
#   new file:   src/collectors/google_ads_config.py

# 3단계: 변경사항 검토
git diff src/collectors/google_ads.py
# (코드가 맞는지 확인)

# 4단계: Staging (추가)
git add src/collectors/google_ads.py
git add src/collectors/google_ads_config.py

# 5단계: Commit (로컬 저장)
git commit -m "feat(collectors): Google Ads API 클라이언트 구현

- API 인증 로직
- 광고 데이터 조회 메서드
- 에러 처리"

# 6단계: Lint/테스트 실행 (로컬)
flake8 src/collectors/google_ads.py
mypy src/collectors/google_ads.py
pytest tests/test_google_ads.py

# 7단계: Push (원격 저장)
git push origin feature/google-ads-api-collector
```

### 점심시간 (12:00~13:00)

```bash
# 점심 전 상태 확인
git status
# 안정적인 상태여야 함

# 점심 후에도 계속 개발
```

---

## 4단계: 오후 개발 (13:00~17:00)

### 테스트 및 추가 개발

```bash
# 테스트 작성
# editor에서: tests/test_google_ads.py

git add tests/test_google_ads.py
git commit -m "test: Google Ads API 통합 테스트 추가

- API 응답 파싱 테스트
- 에러 핸들링 테스트
- Mock 데이터 사용"

git push origin feature/google-ads-api-collector

# 중간 코드 리뷰
git log --oneline -5
# 예:
# xyz7890 test: Google Ads API 통합 테스트 추가
# def4567 feat: Google Ads API 클라이언트 구현
# abc1234 (origin/main) feat: 메트릭 테이블 완료
```

### Main 동기화 (필요시)

```bash
# 오후에 main에 새로운 기능이 병합된 경우
git fetch origin main

# 현재 브랜치에 반영
git rebase origin/main
# 또는
git merge origin/main

# Push
git push origin feature/google-ads-api-collector
```

---

## 5단계: 완료 및 최종 Push (17:00~17:30)

### 마무리

```bash
# 1. 최종 상태 확인
git status
# nothing to commit, working tree clean

# 2. 테스트 최종 확인
pytest tests/test_google_ads.py -v
flake8 src/
mypy src/

# 3. 커밋 히스토리 확인
git log --oneline origin/main..HEAD
# 예:
# xyz7890 test: Google Ads API 통합 테스트
# def4567 feat: Google Ads API 클라이언트 구현

# 4. 모든 변경사항 push
git push origin feature/google-ads-api-collector

# 5. 리모트 상태 확인
git ls-remote origin feature/google-ads-api-collector
```

### 체크리스트

```
□ 모든 코드 커밋됨
□ 모든 테스트 통과
□ Lint 통과
□ 문서 업데이트됨
□ 민감 정보 없음 (.env 등)
□ 최신 main과 동기화됨
□ push 완료
```

---

## 6단계: Pull Request 생성 (17:30~18:00)

### GitHub에서 PR 생성

```
1. GitHub 저장소 오픈
   https://github.com/yourorg/marketing_roas

2. "Compare & pull request" 버튼 클릭

3. PR 제목 입력
   feat: Google Ads API 수집기 구현

4. 설명 작성 (템플릿 사용)
```

### PR 설명 템플릿

```markdown
## 설명
Google Ads API를 통해 광고 데이터를 수집하는 기능을 구현합니다.

## 변경사항
- Google Ads API 클라이언트 구현
- API 응답 파싱 로직
- 에러 핸들링 및 재시도 로직
- 통합 테스트 작성

## 관련 파일
- src/collectors/google_ads.py (신규)
- src/collectors/google_ads_config.py (신규)
- tests/test_google_ads.py (신규)

## 테스트
- [x] 로컬 테스트 통과
- [x] pytest: 12 passed
- [x] flake8: OK
- [x] mypy: OK

## 체크리스트
- [x] 테스트 작성됨
- [x] 문서 업데이트됨
- [x] CI 테스트 통과
- [x] 민감 정보 없음

## 관련 이슈
Closes #45
```

### 명령어로 PR 생성 (선택)

```bash
# GitHub CLI 사용
gh pr create --title "feat: Google Ads API 수집기" \
             --body "Google Ads API 클라이언트 구현..." \
             --base main \
             --head feature/google-ads-api-collector
```

---

## 7단계: 코드 리뷰 (18:00~다음날 오전)

### 리뷰 대기

```
PR이 생성되면:
1. CI/CD 자동 테스트 실행 (15분~)
2. 코드 리뷰 대기 (팀원이 검토)
3. Feedback 반영 (필요시)
4. Approval (1명 이상)
```

### Feedback 반영 (필요시)

```bash
# 예: 리뷰에서 "에러 처리 개선 필요" 댓글

# 1. 로컬에서 수정
# editor에서: src/collectors/google_ads.py 수정

# 2. 커밋
git add src/collectors/google_ads.py
git commit -m "refactor: Google Ads API 에러 처리 개선

- TimeoutError 재시도 로직 추가
- 로그 메시지 상세화"

# 3. Push (자동으로 PR 업데이트)
git push origin feature/google-ads-api-collector

# 4. GitHub에서 다시 리뷰 요청
```

---

## 8단계: 병합 (다음날 오전)

### 승인 후 병합

```
GitHub에서:
1. Approve 확인
2. "Squash and merge" 클릭
3. 병합 완료!
```

### 명령어로 병합 (선택)

```bash
# 또는 로컬에서 수행
git checkout main
git pull origin main
git merge --squash feature/google-ads-api-collector
git commit -m "feat: Google Ads API 수집기 구현"
git push origin main

# 브랜치 정리
git branch -d feature/google-ads-api-collector
git push origin --delete feature/google-ads-api-collector
```

---

## 실제 예시: 일일 커맨드

### 월요일 (새 기능 시작)

```bash
# 8:00 아침
git checkout main
git pull origin main
git checkout -b feature/google-ads-api-collector
git push origin feature/google-ads-api-collector

# 10:00 첫 커밋
git add src/collectors/google_ads.py
git commit -m "feat: Google Ads API 클라이언트 기초 구현"
git push origin feature/google-ads-api-collector

# 14:00 테스트 추가
git add tests/test_google_ads.py
git commit -m "test: Google Ads 클라이언트 단위 테스트"
git push origin feature/google-ads-api-collector

# 17:00 정리
git push origin feature/google-ads-api-collector
```

### 화요일 (추가 개발)

```bash
# 8:00 아침
git checkout main
git pull origin main
git checkout feature/google-ads-api-collector
git rebase origin/main  # main 최신화

# 11:00 에러 처리 추가
git add src/collectors/google_ads.py
git commit -m "refactor: 에러 처리 및 재시도 로직"
git push origin feature/google-ads-api-collector

# 15:00 문서 작성
git add docs/API_SETUP.md
git commit -m "docs: Google Ads API 설정 가이드"
git push origin feature/google-ads-api-collector

# 17:00 PR 생성
gh pr create --title "feat: Google Ads API 수집기" \
             --body "구현 완료, 리뷰 부탁합니다"
```

### 수요일 (PR 리뷰 및 병합)

```bash
# 8:00 PR 상태 확인
gh pr view --web  # 브라우저에서 PR 보기

# 9:00 Feedback 반영 (필요시)
git add src/collectors/google_ads.py
git commit -m "fix: 코드 리뷰 피드백 적용"
git push origin feature/google-ads-api-collector

# 11:00 Approve 확인
gh pr view  # PR 상태 확인

# 12:00 Merge
gh pr merge --squash  # GitHub CLI로 병합

# 13:00 다음 작업 시작
git checkout main
git pull origin main
git checkout -b feature/bigquery-schema-setup
```

---

## 문제 해결

### 실수 1: 잘못된 파일 커밋

```bash
# 상황: .env 파일을 실수로 커밋함
# 해결:

# 1. 커밋 되돌리기
git reset --soft HEAD~1

# 2. 파일 제거
git rm --cached .env

# 3. 다시 커밋
git commit -m "feat: 기능 추가 (민감 정보 제외)"
```

### 실수 2: Main에 직접 커밋

```bash
# 상황: main에 실수로 커밋함
# 해결:

# 1. 커밋 되돌리기
git reset --soft HEAD~1

# 2. feature 브랜치 생성
git checkout -b feature/my-feature

# 3. 커밋
git commit -m "feat: ..."
git push origin feature/my-feature
```

### 실수 3: Merge 충돌

```bash
# 상황: git merge/rebase 중 충돌
# 해결:

# 1. 상태 확인
git status

# 2. 충돌 파일 확인
# editor에서 수정 (<<<<<<, ======, >>>>>> 제거)

# 3. 해결 완료
git add .

# Merge 중인 경우
git merge --continue

# Rebase 중인 경우
git rebase --continue
```

---

## 팁과 트릭

### 커밋 메시지 수정

```bash
# 마지막 커밋 메시지 수정
git commit --amend -m "새로운 메시지"

# 푸시 전이면 OK, 푸시 후 강제 필요
git push origin -f
```

### 마지막 커밋 취소

```bash
# Commit 취소 (변경사항 유지)
git reset --soft HEAD~1

# Commit 취소 (변경사항도 취소)
git reset --hard HEAD~1
```

### 어느 브랜치에 어떤 기능이 있는지 확인

```bash
# 커밋 히스토리 그래프
git log --graph --oneline --all

# 특정 기능 찾기
git log --grep="Google Ads" --oneline
```

---

## 체크리스트: 매일 아침

```
□ git checkout main
□ git pull origin main
□ git status (clean?)
□ 어제 PR merge 확인
□ 오늘 할 기능 선택
□ feature 브랜치 생성
```

## 체크리스트: 매일 저녁

```
□ git status (clean?)
□ git push origin feature/...
□ 모든 변경사항 원격에 있나?
□ PR 필요한가?
```

---

## 다음 읽을 문서

- [BRANCHING.md](./BRANCHING.md) - 브랜칭 상세 가이드
- [FEATURE_FLAGS.md](./FEATURE_FLAGS.md) - Feature flags 구현
