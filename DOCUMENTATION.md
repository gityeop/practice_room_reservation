# 실험실 예약 시스템 기술 문서

## 기술 스택

### 백엔드
- **프레임워크**: Flask (Python)
- **데이터베이스**: 
  - **주 데이터베이스**: Supabase (PostgreSQL 기반)
  - **백업 데이터베이스**: SQLite
- **사용자 인증**: Flask-Login, 자체 토큰 시스템
- **ORM**: SQLAlchemy
- **배포**: Gunicorn (WSGI 서버)

### 프론트엔드
- **템플릿 엔진**: Jinja2 (Flask 내장)
- **UI 프레임워크**: Bootstrap
- **JavaScript**: 바닐라 JS

## 시스템 구조

### 데이터베이스 구조

#### 테이블
1. **users** - 사용자 정보
   - id, name, student_id, department, password_hash, is_admin, cancel_count, token, token_expiration

2. **reservations** - 예약 정보
   - id, user_id, date, start_time, end_time, status, created_at, purpose

3. **blocked_times** - 예약 불가능 시간대
   - id, date, start_time, end_time, reason

### 주요 모듈

1. **routes/**
   - **auth.py**: 인증 관련 기능 (로그인, 회원가입, 로그아웃)
   - **admin.py**: 관리자 기능
   - **reservation.py**: 예약 관련 기능

2. **models.py**: 데이터베이스 모델 정의
3. **repository.py**: Supabase 데이터 접근 계층
4. **app.py**: 애플리케이션 메인 파일
5. **config.py**: 애플리케이션 설정

## 특징 및 기능

### 사용자 관리
- 회원가입 및 로그인
- 관리자/일반 사용자 권한 구분
- 토큰 기반 인증 시스템

### 예약 관리
- 실험실 시간대별 예약
- 예약 승인/거절 시스템
- 예약 취소 기능
- 취소 횟수 관리 (페널티 시스템)

### 관리자 기능
- 모든 예약 조회 및 관리
- 사용 불가능 시간대 설정
- 사용자 관리

## 설치 및 설정 방법

### 필수 요구사항
- Python 3.7 이상
- pip (Python 패키지 관리자)
- Supabase 계정 및 프로젝트

### 설치 과정

1. 저장소 복제:
```bash
git clone <저장소 URL>
cd lab_reservation
```

2. 가상 환경 설정 (권장):
```bash
python -m venv venv
source venv/bin/activate  # 리눅스/Mac
venv\Scripts\activate    # 윈도우
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
   - `.env` 파일 생성 또는 시스템 환경 변수 설정
   - 필요한 환경 변수:
     - `SUPABASE_URL`: Supabase 프로젝트 URL
     - `SUPABASE_KEY`: Supabase API 키
     - `SECRET_KEY`: Flask 보안 키
     - `ADMIN_USERNAME`: 관리자 계정 학번

5. 데이터베이스 초기화:
```bash
python init_db.py
```

6. 서버 실행:
```bash
# 개발 모드
python app.py

# 프로덕션 모드
gunicorn --config gunicorn.conf.py app:app
```

## 사용 방법

### 일반 사용자

1. **회원가입**
   - 이름, 학번, 학과, 비밀번호 입력
   - 학번은 9자리여야 함

2. **로그인**
   - 학번과 비밀번호로 로그인

3. **예약 생성**
   - 대시보드에서 날짜와 시간 선택
   - 예약 목적 입력
   - 제출 후 승인 대기

4. **예약 관리**
   - 마이페이지에서 예약 조회
   - 예약 취소 (취소 횟수에 제한이 있을 수 있음)

### 관리자

1. **관리자 로그인**
   - 관리자 계정으로 로그인

2. **예약 관리**
   - 모든 예약 조회
   - 예약 승인/거절
   - 필터링 및 검색 기능

3. **사용 불가능 시간 관리**
   - 특정 시간대 차단 (수업, 회의 등의 이유로)
   - 차단된 시간 조회 및 관리

4. **사용자 관리**
   - 사용자 목록 조회
   - 관리자 권한 부여/해제

## 문제 해결

### 일반적인 문제

1. **로그인 문제**
   - 세션이 만료되었을 경우 재로그인 필요
   - 다른 기기에서 로그인 시 기존 세션 종료

2. **예약 충돌**
   - 같은 시간대에 이미 예약이 있는 경우 예약 불가
   - 관리자가 설정한 차단 시간과 충돌할 경우 예약 불가

### 연락처

기술적인 문제나 질문이 있을 경우 다음으로 연락해주세요:
- 이메일: freiheit517@icloud.com