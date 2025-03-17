# 실험실 예약 시스템

실험실 예약 관리를 위한 웹 애플리케이션입니다. 학생들이 실험실 시간을 예약하고 관리자가 이를 승인하는 기능을 제공합니다.

## 기능

- 사용자 등록 및 로그인
- 실험실 예약 시스템
- 관리자 승인 시스템
- 시간별 차단 관리
- 사용자 관리

## 기술 스택

- **백엔드**: Flask, Flask-SQLAlchemy, Flask-Login
- **프론트엔드**: HTML, CSS, JavaScript, FullCalendar
- **데이터베이스**: SQLite (로컬), PostgreSQL (배포)

## 배포 가이드 (Render)

### 배포 준비

1. GitHub에 코드 업로드
2. [Render](https://render.com/) 가입
3. New Web Service 선택 및 GitHub 저장소 연결

### 환경 변수 설정

- `ADMIN_USERNAME`: 관리자 아이디
- `ADMIN_PASSWORD`: 관리자 비밀번호
- `SECRET_KEY`: 액세스 토큰 암호화용 키
- `CULTURE_CONTENT_DEPT`: 문화콘텐츠학과 이름

### 배포 후 초기 설정

1. Render의 쉘에서 데이터베이스 초기화:
```
python init_db.py
```

## 로컬 개발 환경 설정

1. 저장소 복제:
```
git clone <저장소 URL>
cd lab_reservation
```

2. 가상 환경 설정 (선택사항):
```
python -m venv venv
source venv/bin/activate  # 리눅스/Mac
venv\Scripts\activate    # 윈도우
```

3. 패키지 설치:
```
pip install -r requirements.txt
```

4. 데이터베이스 초기화:
```
python init_db.py
```

5. 서버 실행:
```
python app.py
```
