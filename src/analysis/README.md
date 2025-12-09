# 📊 Advertising CTR 예측 데이터 분석 가이드

**프로젝트**: Advertising Click-Through Rate (CTR) 예측
**버전**: 1.0
**최종 업데이트**: 2025-12-09
**담당자**: Data Engineering Team

---

## 📌 목차

1. [개요](#개요)
2. [데이터 개요](#데이터-개요)
3. [데이터 속성](#데이터-속성)
4. [데이터 품질](#데이터-품질)
5. [분석 가이드](#분석-가이드)
6. [자주 묻는 질문](#자주-묻는-질문)
7. [기술 스택](#기술-스택)

---

## 개요

### 프로젝트 목표

온라인 광고 데이터를 분석하여 **광고 클릭 가능성(CTR)을 예측**하는 이진 분류 모델을 개발합니다.

### 문제 정의

- **유형**: Binary Classification (이진 분류)
- **목표 변수**: `click` (0 = 클릭 안 함, 1 = 클릭함)
- **핵심 메트릭**: CTR (Click Through Rate)
- **데이터 특성**: 광고 노출 기록

### 핵심 메트릭

- **CTR (클릭율)** = 클릭한 광고 수 / 총 노출 수 = 16.41%
- **Baseline**: 무조건 0으로 예측해도 83.59% 정확도 (class imbalance)
- **목표**: 모델 AUC > 0.75 달성

### 데이터 특성

- **수집 방식**: Streaming (실시간 광고 이벤트)
- **저장 형식**: CSV (gzip 압축) / 원본은 train.gz
- **스키마 관리**: Kafka + Schema Registry (예정)
- **데이터베이스**: PostgreSQL

---

## 데이터 개요

### 데이터 저장 위치

```
project/
├── data/
│   ├── sample/          # 👈 현재 위치
│   │   ├── train.gz     (원본, 5MB~)
│   │   ├── test.gz      (테스트 데이터)
│   │   └── train_sample_*.csv (샘플)
│   ├── raw/             # 원본 데이터
│   └── processed/       # 전처리된 데이터
```

### 파일 상세 정보

| 파일명 | 크기 | 행 수 | 열 수 | 설명 |
|--------|------|--------|--------|------|
| `train.gz` | 5MB+ | 500K+ | 24 | 전체 학습 데이터 |
| `test.gz` | ? | ? | 24 | 테스트 데이터 (클릭 없음) |
| `train_sample_1k.csv` | - | 1,000 | 24 | 샘플 (1K) |
| `train_sample_10k.csv` | - | 10,000 | 24 | 샘플 (10K) |
| `train_sample_50k.csv` | - | 50,000 | 24 | 샘플 (50K) |

### 데이터 로드 방법

```python
import pandas as pd

# 전체 데이터 로드 (시간 걸림)
df = pd.read_csv('data/raw/train.gz', compression='gzip')

# 샘플 데이터 로드 (빠름)
df = pd.read_csv('data/sample/train_sample_50k.csv')

# 첫 N행만 로드 (메모리 절약)
df = pd.read_csv('data/raw/train.gz', compression='gzip', nrows=100000)

# 기본 정보
print(df.info())
print(df.describe())
print(df.head())
```

---

## 데이터 속성

### 필드 정의 (Data Dictionary)

총 **24개 필드** (ID + 타겟 + 22개 특성)

#### 📋 전체 필드 한눈에 보기

| # | 필드명 | 타입 | 설명 | 고유값 | 카테고리 |
|---|--------|------|------|--------|---------|
| 1 | `id` | float64 | Ad identifier - 광고 노출 고유 ID | ~500K | ID |
| 2 | `click` | int64 | **[TARGET]** 클릭 여부 (0/1) | 2 | **Target** |
| 3 | `hour` | int64 | 광고 노출 시간 (YYMMDDHH, UTC) | 4 | 시간 |
| 4 | `banner_pos` | int64 | 배너 위치 (광고 배치 위치) | 6 | 위치 |
| 5 | `site_id` | object | 광고가 표시된 사이트 ID | 1,704 | 사이트 |
| 6 | `site_domain` | object | 사이트 도메인 | 1,586 | 사이트 |
| 7 | `site_category` | object | 사이트 카테고리 | 21 | 사이트 |
| 8 | `app_id` | object | 모바일 앱 ID | 1,641 | 앱 |
| 9 | `app_domain` | object | 앱 도메인 | 122 | 앱 |
| 10 | `app_category` | object | 앱 카테고리 | 20 | 앱 |
| 11 | `device_id` | object | 사용자 디바이스 ID (익명화) | 41,413 | 디바이스 |
| 12 | `device_ip` | object | 사용자 IP 주소 (익명화) | 171,304 | 디바이스 |
| 13 | `device_model` | object | 디바이스 모델명 | 3,967 | 디바이스 |
| 14 | `device_type` | int64 | 디바이스 타입 (0~5) | 4 | 디바이스 |
| 15 | `device_conn_type` | int64 | 네트워크 연결 유형 (0~5) | 4 | 디바이스 |
| 16 | `C1` | int64 | Anonymized categorical variable 1 | 7 | 익명화 |
| 17 | `C14` | int64 | Anonymized categorical variable 14 | 540 | 익명화 |
| 18 | `C15` | int64 | Anonymized categorical variable 15 | 8 | 익명화 |
| 19 | `C16` | int64 | Anonymized categorical variable 16 | 9 | 익명화 |
| 20 | `C17` | int64 | Anonymized categorical variable 17 | 154 | 익명화 |
| 21 | `C18` | int64 | Anonymized categorical variable 18 | 4 | 익명화 |
| 22 | `C19` | int64 | Anonymized categorical variable 19 | 40 | 익명화 |
| 23 | `C20` | int64 | Anonymized categorical variable 20 | 154 | 익명화 |
| 24 | `C21` | int64 | Anonymized categorical variable 21 | 34 | 익명화 |

**통계 요약**:
- 수치형(int64): 11개 (click, hour, banner_pos, device_type, device_conn_type, C1, C14~C21)
- 문자형(object): 9개 (site_id, site_domain, site_category, app_id, app_domain, app_category, device_id, device_ip, device_model)
- 부동소수점(float64): 1개 (id)
- 결측치: 0개 (완벽한 데이터)

#### 1️⃣ 기본 필드

| 필드명 | 타입 | 설명 | 범위/예시 |
|--------|------|------|---------|
| `id` | float64 | **Ad identifier** - 광고 노출 고유 ID | 1.0e+12 ~ 1.8e+19 |
| `click` | int64 | **[TARGET]** 클릭 여부 | 0 (미클릭) 또는 1 (클릭) |

#### 2️⃣ 시간 & 위치 정보

| 필드명 | 타입 | 설명 | 고유값 |
|--------|------|------|--------|
| `hour` | int64 | 광고 노출 시간 (YYMMDDHH 형식) | 4개 |
| `banner_pos` | int64 | 배너 위치 (광고 배치) | 0 ~ 7 (6개) |

**hour 형식 상세**:
- `YYMMDDHH` = Year(2자리) + Month(2자리) + Day(2자리) + Hour(2자리)
- 예: `14091123` = 2014년 9월 11일 23:00 UTC
- 예: `14102100` = 2014년 10월 21일 00:00 UTC

#### 3️⃣ 사이트 정보

| 필드명 | 타입 | 설명 | 고유값 |
|--------|------|------|--------|
| `site_id` | object(string) | 광고가 표시된 사이트 ID | 1,704개 |
| `site_domain` | object(string) | 사이트 도메인 | 1,586개 |
| `site_category` | object(string) | 사이트 카테고리 | 21개 |

#### 4️⃣ 앱 정보

| 필드명 | 타입 | 설명 | 고유값 |
|--------|------|------|--------|
| `app_id` | object(string) | 모바일 앱 ID (앱 광고인 경우) | 1,641개 |
| `app_domain` | object(string) | 앱 도메인 | 122개 |
| `app_category` | object(string) | 앱 카테고리 | 20개 |

#### 5️⃣ 디바이스 정보

| 필드명 | 타입 | 설명 | 고유값 |
|--------|------|------|--------|
| `device_id` | object(string) | 사용자 디바이스 ID (익명화) | 41,413개 |
| `device_ip` | object(string) | 사용자 IP 주소 (익명화) | 171,304개 |
| `device_model` | object(string) | 디바이스 모델명 | 3,967개 |
| `device_type` | int64 | 디바이스 타입 (0=미상, 1=모바일, ...) | 4개 |
| `device_conn_type` | int64 | 네트워크 연결 유형 (0=미상, 1=Wi-Fi, ...) | 4개 |

#### 6️⃣ 익명화된 카테고리 특성 (C1, C14-C21)

| 필드명 | 타입 | 설명 | 고유값 |
|--------|------|------|--------|
| `C1` | int64 | **Anonymized categorical variable 1** | 7개 |
| `C14` | int64 | **Anonymized categorical variable 14** | 540개 |
| `C15` | int64 | **Anonymized categorical variable 15** | 8개 |
| `C16` | int64 | **Anonymized categorical variable 16** | 9개 |
| `C17` | int64 | **Anonymized categorical variable 17** | 154개 |
| `C18` | int64 | **Anonymized categorical variable 18** | 4개 |
| `C19` | int64 | **Anonymized categorical variable 19** | 40개 |
| `C20` | int64 | **Anonymized categorical variable 20** | 154개 |
| `C21` | int64 | **Anonymized categorical variable 21** | 34개 |

**참고**:
- 실제 의미는 공개되지 않은 익명화 변수
- C2~C13은 데이터에 포함되지 않음 (C1, 그리고 C14-C21만 존재)
- 범주형 특성으로 원핫 인코딩 또는 라벨 인코딩 필요

### 데이터 통계

```python
데이터 크기: (500,000 행, 24 열)
결측치: 0개 (완벽한 데이터 품질 ✅)

클릭 분포:
  - 미클릭 (click=0): 417,963 (83.59%)
  - 클릭 (click=1): 82,037 (16.41%)

CTR (Click Through Rate): 16.41%
클래스 비율: 약 5:1 (심각한 불균형)

시간 범위: 2014년 9월 11일 ~ 10월 21일 (특정 4시간만)
고유 광고 수: ~500K
고유 사이트: 1,704개
고유 앱: 1,641개
고유 디바이스: 41,413개
```

---

## 데이터 품질

### 데이터 검증 체크리스트

#### 1️⃣ 기본 통계 검증

```python
# 결측치 확인
print(df.isnull().sum())  # 모두 0이어야 함

# 클릭 분포 확인
print(df['click'].value_counts())
print(f"CTR: {df['click'].mean()*100:.2f}%")

# 데이터 크기 확인
print(df.shape)  # (행 수, 24)
```

**확인 사항**:
- ✅ 결측치 없음 (데이터 품질 우수)
- ✅ 타겟 변수(click)은 0 또는 1만 존재
- ✅ 모든 행이 유효함

---

#### 2️⃣ 클래스 불균형 (Class Imbalance)

```python
# 클래스 분포
print(df['click'].value_counts(normalize=True))
print(f"클릭율: {df['click'].mean()*100:.2f}%")

# 해결 방법
from sklearn.utils import class_weight
weights = class_weight.compute_class_weight('balanced',
                                             classes=np.unique(df['click']),
                                             y=df['click'])
```

**문제점**:
- 미클릭 (0): 83.59% vs 클릭 (1): 16.41%
- **극심한 클래스 불균형** (약 5:1)

**대응**:
- Stratified K-Fold 사용
- Class weight 조정
- Oversampling / Undersampling
- 평가 지표: Precision, Recall, AUC (정확도 X)

---

#### 3️⃣ 데이터 범위 검증

```python
# 수치형 필드 범위 확인
print(df.describe())

# 이상치 확인
print(f"device_type 범위: {df['device_type'].min()} ~ {df['device_type'].max()}")
print(f"device_conn_type 범위: {df['device_conn_type'].min()} ~ {df['device_conn_type'].max()}")
```

**확인 사항**:
- device_type: 0 ~ 5 (정상)
- device_conn_type: 0 ~ 5 (정상)
- hour: 모두 같은 날짜 (1410210x)
- 모든 수치형 필드가 합리적 범위

---

#### 4️⃣ 카테고리형 필드 검증

```python
# 고유값 개수 확인
print(df.nunique())

# 각 필드의 상위 값
print(df['site_id'].value_counts().head(10))
print(df['device_id'].value_counts().head(10))
```

**특이점**:
- High cardinality: device_id (41K), device_ip (171K)
- Low cardinality: C1 (7), device_type (4)
- 최빈값 분포: 특정 값에 집중되지 않음

---

#### 5️⃣ 시계열 데이터 검증

```python
# 시간 정보 확인
print(df['hour'].unique())
print(df['hour'].value_counts().sort_index())

# hour 파싱 예시
df['year'] = (df['hour'] // 1000000) + 2000
df['month'] = (df['hour'] // 10000) % 100
df['day'] = (df['hour'] // 100) % 100
df['hour_of_day'] = df['hour'] % 100
```

**확인 사항**:
- hour 값: 14102100, 14102101, 14102102, 14102103 (2014년 10월 21일 00시~03시)
- YYMMDDHH 형식으로 정확한 시간 정보 포함
- 4개의 시간대만 포함 (제한적 시계열)
- UTC 기준 시간

---

### 스키마 드리프트 모니터링

```python
# Avro 스키마 버전 확인
# Schema Registry에서 다음 필드를 모니터링:
# - 신규 특성 추가 (C22, C23 등)
# - 필드 삭제
# - 데이터타입 변경
```

---

## 분석 가이드

### 1. 데이터 로드 및 탐색

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# 샘플 데이터 로드
df = pd.read_csv('data/sample/train_sample_50k.csv')

# 기본 정보
print(df.info())        # 데이터타입, null 확인
print(df.describe())    # 통계
print(df.head())        # 첫 5행

# 클래스 분포
print("\n클릭 분포:")
print(df['click'].value_counts())
print(f"CTR: {df['click'].mean()*100:.2f}%")

# 고유값 개수
print("\n고유값 개수:")
print(df.nunique())
```

### 2. 데이터 전처리

```python
# 데이터 타입 변환
df['hour'] = df['hour'].astype(str)

# 파생 특성 생성 (선택)
# - hour에서 시간 추출
# - site_id + site_category 조합 특성
# - device_type + device_conn_type 조합

# 카테고리형 인코딩
from sklearn.preprocessing import LabelEncoder

categorical_cols = ['site_id', 'site_domain', 'site_category', 'app_id',
                   'app_domain', 'app_category', 'device_id', 'device_ip',
                   'device_model', 'hour']

for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
```

### 3. 탐색적 데이터 분석 (EDA)

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 클릭 분포
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
df['click'].value_counts().plot(kind='bar', ax=axes[0], title='Click Distribution')
df['click'].value_counts(normalize=True).plot(kind='pie', ax=axes[1], title='Click Rate')
plt.tight_layout()
plt.show()

# 디바이스별 CTR
device_ctr = df.groupby('device_type')['click'].agg(['sum', 'count', 'mean'])
device_ctr.columns = ['clicks', 'total', 'ctr']
print("\n디바이스별 CTR:")
print(device_ctr)

# 배너 위치별 CTR
banner_ctr = df.groupby('banner_pos')['click'].mean()
banner_ctr.plot(kind='bar', title='CTR by Banner Position')
plt.show()
```

### 4. 모델 개발

```python
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

# 특성과 목표 분리
X = df.drop(['id', 'click'], axis=1)  # ID 제거
y = df['click']

# 훈련/테스트 분할 (클래스 비율 유지)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 모델 1: Logistic Regression
model_lr = LogisticRegression(class_weight='balanced', max_iter=1000)
model_lr.fit(X_train, y_train)
y_pred_lr = model_lr.predict(X_test)
print(f"Logistic Regression AUC: {roc_auc_score(y_test, model_lr.predict_proba(X_test)[:, 1]):.4f}")

# 모델 2: Random Forest
model_rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
model_rf.fit(X_train, y_train)
y_pred_rf = model_rf.predict(X_test)
print(f"Random Forest AUC: {roc_auc_score(y_test, model_rf.predict_proba(X_test)[:, 1]):.4f}")

# 평가
print("\nClassification Report:")
print(classification_report(y_test, y_pred_rf))

# 혼동 행렬
from sklearn.metrics import ConfusionMatrixDisplay
cm = confusion_matrix(y_test, y_pred_rf)
ConfusionMatrixDisplay(cm).plot()
plt.show()
```

---

## 자주 묻는 질문

### Q1. CTR이란 무엇인가?

**A**: CTR (Click Through Rate) = 광고를 클릭한 횟수 / 노출된 횟수
- 예: 1000번 노출 중 164번 클릭 → CTR = 16.4%
- 광고 효과를 측정하는 가장 기본적인 지표

---

### Q2. 왜 정확도(Accuracy)로 평가하면 안 되나?

**A**: 클래스 불균형 때문
- 미클릭(0): 83.59%, 클릭(1): 16.41%
- 무조건 0으로 예측해도 정확도 83.59%
- **올바른 평가 지표**: Precision, Recall, AUC, F1-Score

---

### Q3. 데이터가 한 날짜만 있는데 일반화 가능한가?

**A**: 제한적
- 현재 데이터는 특정 날짜(14102100~14102103)만 포함
- 다양한 시간대, 날씨, 계절 정보 없음
- **해결책**: 더 다양한 시간대 데이터 수집 필요

---

### Q4. C1~C21은 뭔가?

**A**: 익명화된(Anonymized) 카테고리 특성
- 실제 의미 모름 (보안 상 공개 불가)
- 범주형 변수로 취급
- 원핫 인코딩 또는 라벨 인코딩 필요

---

### Q5. device_id와 device_ip의 차이는?

**A**:
- `device_id`: 디바이스 고유 식별자 (기기 정보)
  - 같은 기기 → 같은 device_id
- `device_ip`: 사용자 IP 주소 (네트워크 정보)
  - 같은 네트워크 → 같은 device_ip
- High cardinality로 인해 오버피팅 주의 필요

---

### Q6. 샘플 데이터 vs 전체 데이터 어느 것을 사용하나?

**A**:
- **개발/탐색 단계**: 샘플 (빠른 반복)
  - `train_sample_50k.csv` 추천
- **최종 모델**: 전체 데이터
  - `train.gz` 사용 (시간 걸림)

---

### Q7. hour 필드를 어떻게 파싱하나?

**A**: `hour`는 YYMMDDHH 형식이므로 나누어서 추출 가능

```python
# hour 파싱 예시
df['year'] = 2000 + (df['hour'] // 1000000)
df['month'] = (df['hour'] // 10000) % 100
df['day'] = (df['hour'] // 100) % 100
df['hour_of_day'] = df['hour'] % 100

# 예: 14091123 = 2014년 9월 11일 23시
# 예: 14102100 = 2014년 10월 21일 00시
```

---

### Q8. 왜 C2~C13이 없고 C1, C14-C21만 있나?

**A**: 데이터 공개 특성상 일부 특성만 공개됨
- C1: 제공됨 (7개 고유값)
- C2~C13: 비공개 (데이터에 없음)
- C14~C21: 제공됨 (각각 8~540개 고유값)
- 의도된 데이터 구조 (소스 데이터의 선택)

---

## 기술 스택

### 데이터 처리 및 분석

| 기술 | 역할 | 버전 |
|------|------|------|
| **Python** | 데이터 분석 & 모델 개발 | 3.8+ |
| **Pandas** | 데이터 조작 및 분석 | 1.x |
| **NumPy** | 수치 계산 | 1.x |
| **Scikit-learn** | 머신러닝 모델 | 1.x |
| **Matplotlib** | 시각화 (기본) | 3.x |
| **Seaborn** | 시각화 (고급) | 0.11+ |

### 데이터 파이프라인

| 기술 | 역할 |
|------|------|
| **Kafka** | 실시간 스트리밍 (메시지 브로커) |
| **Schema Registry** | Avro 스키마 관리 및 버전 관리 |
| **PostgreSQL** | 데이터 저장소 (정형 데이터) |
| **Apache Airflow** | ETL 파이프라인 스케줄링 |
| **Docker** | 컨테이너 기반 배포 |

### 개발 환경

```bash
# 필수 설치 패키지
pip install pandas numpy scikit-learn matplotlib seaborn

# 선택 패키지
pip install jupyter notebook ipython xgboost lightgbm

# 환경 실행
docker-compose up -d  # Kafka + Schema Registry 시작
```

---

## 📞 연락처 및 지원

**담당자**: Data Engineering Team
**이메일**: data-team@company.com
**Slack**: #data-engineering

---

## 📚 참고 자료

- [CTR 예측 문제 설명](https://en.wikipedia.org/wiki/Click-through_rate)
- [Class Imbalance 처리](https://imbalanced-learn.org/)
- [Kaggle CTR 대회](https://www.kaggle.com/c/avazu-ctr-prediction)
- [pandas 공식 문서](https://pandas.pydata.org/docs/)
- [Scikit-learn 머신러닝](https://scikit-learn.org/)

---

**마지막 업데이트**: 2025-12-09
**라이선스**: MIT
