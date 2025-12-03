# 📚 Git 전략 문서

이 디렉토리는 프로젝트의 Git 관리 전략과 워크플로우에 대한 문서입니다.

> **프로젝트 Git 전략**: Trunk-Based Development (TBD)

---

## 📖 문서 목록

### 1. [STRATEGY.md](./STRATEGY.md) ⭐ **여기부터 시작하세요**

프로젝트의 Git 전략 전체를 이해하는 문서입니다.

**포함 내용:**
- Trunk-Based Development 개요
- 왜 TBD를 선택했는가
- 핵심 원칙
- 브랜치 모델
- Pull Request 프로세스
- 보안 가이드

**읽는 시간:** 10분

---

### 2. [BRANCHING.md](./BRANCHING.md)

브랜칭의 모든 것을 다루는 상세 가이드입니다.

**포함 내용:**
- 브랜치 종류와 역할
- 브랜치 생명주기 (생성 → 개발 → 리뷰 → 병합 → 정리)
- 브랜치명 규칙
- 브랜치 동기화 방법
- 일반적인 시나리오와 해결 방법
- 명령어 참고

**읽는 시간:** 15분

**자주 참고하는 문서:** ⭐⭐⭐

---

### 3. [WORKFLOW.md](./WORKFLOW.md)

하루 동안의 실제 작업 흐름을 단계별로 설명합니다.

**포함 내용:**
- 아침 준비
- Feature 브랜치 생성
- 코드 개발 및 커밋
- Pull Request 생성
- 코드 리뷰
- 병합
- 실제 예시 (월/화/수 워크플로우)
- 문제 해결

**읽는 시간:** 20분

**새 팀원이 반드시 읽을 문서:** ⭐⭐⭐

---

### 4. [FEATURE_FLAGS.md](./FEATURE_FLAGS.md)

미완성 기능을 안전하게 배포하는 방법입니다.

**포함 내용:**
- Feature Flags의 필요성
- 구현 방식 (환경변수, 설정파일, 클래스)
- 사용 패턴 (if-else, 래퍼, 데코레이터, 전략패턴)
- 실제 프로젝트 적용
- 점진적 배포 (Rollout)
- 모니터링 및 로깅
- 체크리스트

**읽는 시간:** 15분

**Trunk-Based Development의 핵심:** ⭐⭐⭐

---

## 🎯 상황별 읽기 가이드

### 🆕 프로젝트 신입자

```
1. STRATEGY.md 읽기 (전략 이해)
   ↓
2. WORKFLOW.md 읽기 (하루 일과 이해)
   ↓
3. BRANCHING.md 참고 (필요할 때)
   ↓
4. 첫 feature 작성 시 FEATURE_FLAGS.md 읽기
```

### 👨‍💻 이미 Git을 쓰고 있는 개발자

```
1. STRATEGY.md에서 TBD와 이전 전략의 차이점 이해
   ↓
2. WORKFLOW.md에서 일일 워크플로우 확인
   ↓
3. 필요시 BRANCHING.md와 FEATURE_FLAGS.md 참고
```

### 🔄 리더/PM

```
1. STRATEGY.md 읽기
   ↓
2. "왜 TBD를 선택했는가" 섹션 중점 읽기
   ↓
3. 팀과 공유
```

---

## 🚀 빠른 시작

### 첫 번째 feature 개발하기

```bash
# 1. 아침 준비
git checkout main
git pull origin main

# 2. Feature 브랜치 생성
git checkout -b feature/my-first-feature

# 3. 개발 (여러 번 커밋)
git add src/...
git commit -m "feat: 기능 구현 (1/3)"

git add tests/...
git commit -m "test: 테스트 추가"

# 4. 저녁 정리
git push origin feature/my-first-feature

# 5. PR 생성 (GitHub에서)
# → CI 자동 실행
# → 리뷰 대기
# → 병합

# 6. 다음날 정리
git checkout main
git pull origin main
```

자세한 내용은 [WORKFLOW.md](./WORKFLOW.md)를 참고하세요.

---

## 📋 핵심 규칙 (5가지)

### Rule 1: Main은 항상 배포 가능
```
❌ 문제있는 코드를 main에 직접 push
✅ PR로 검증 후 merge
```

### Rule 2: Feature 브랜치는 짧게 (2-5일)
```
❌ 2주 동안 feature 브랜치에서만 작업
✅ 2-3일 내에 작은 단위로 병합
```

### Rule 3: 하루 1회 이상 커밋 & 푸시
```
❌ 일주일 후 한 번에 큰 커밋
✅ 매일 작은 커밋 여러 번
```

### Rule 4: Feature Flags로 미완성 기능 제어
```
❌ 미완성 코드를 배포 안 함
✅ 미완성 코드도 배포 (flag로 비활성화)
```

### Rule 5: 자동 테스트와 코드 리뷰 필수
```
❌ 수동 테스트만 진행
✅ 자동 테스트 + 1명 이상 리뷰
```

---

## 🔗 자주 사용하는 명령어

### 보기

```bash
git branch          # 현재 브랜치 확인
git status          # 변경사항 확인
git log --oneline   # 커밋 히스토리
```

### 생성 & 전환

```bash
git checkout -b feature/name      # 새 브랜치 생성
git switch feature/name           # 브랜치 전환
git push origin feature/name      # 원격에 push
```

### 커밋

```bash
git add .                         # 변경사항 스테이징
git commit -m "feat: 설명"        # 커밋
git push origin feature/name      # push
```

### 동기화

```bash
git pull origin main              # main 최신화
git rebase origin/main            # rebase (권장)
git merge origin/main             # merge
```

더 많은 명령어는 [BRANCHING.md](./BRANCHING.md)를 참고하세요.

---

## ❓ FAQ

### Q: Feature 브랜치가 2주가 되었는데?
**A:** [BRANCHING.md - Rule 2](./BRANCHING.md)를 다시 읽고, 더 작은 단위로 나누어 병합하세요.

### Q: Feature가 미완성인데 배포해도 되나?
**A:** [FEATURE_FLAGS.md](./FEATURE_FLAGS.md)를 읽고, feature flag으로 비활성화하세요.

### Q: 실수로 main에 커밋했는데?
**A:** [BRANCHING.md - 시나리오 3](./BRANCHING.md)을 따르세요.

### Q: Merge conflict가 발생했는데?
**A:** [BRANCHING.md - 문제 해결](./BRANCHING.md)을 참고하세요.

### Q: PR을 어떻게 만드나?
**A:** [STRATEGY.md - Pull Request 프로세스](./STRATEGY.md)를 참고하세요.

---

## 📞 문의사항

Git 전략에 대한 질문이 있으시면:

1. 먼저 이 문서에서 답을 찾으세요
2. 팀 리더에게 물어보세요
3. GitHub Issues에 질문을 등록하세요

---

## 🎓 추가 학습 자료

- [Git 공식 문서](https://git-scm.com/doc)
- [Atlassian Git Tutorial](https://www.atlassian.com/git/tutorials)
- [GitHub Docs](https://docs.github.com)
- [Feature Toggles - Martin Fowler](https://martinfowler.com/articles/feature-toggles.html)

---

**작성일:** 2025-12-03
**마지막 수정:** 2025-12-03
**버전:** 1.0
