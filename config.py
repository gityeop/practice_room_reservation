import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    # 환경 변수에서 비밀 키 가져오기 (없으면 기본값 사용)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-replace-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///lab_reservation.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 예약 관련 설정
    MAX_HOURS_PER_DAY = 3
    CANCEL_PENALTY_THRESHOLD = 3
    
    # 관리자 계정 정보 (환경 변수에서 가져오기)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'default-admin-password-change-me')

    # 학과 코드
    CULTURE_CONTENT_DEPT = os.environ.get('CULTURE_CONTENT_DEPT', '문화콘텐츠학과')
    
    # 세션 쿠키 보안 설정 추가
    SESSION_COOKIE_SECURE = True  # HTTPS에서만 쿠키 전송
    SESSION_COOKIE_HTTPONLY = True  # JavaScript에서 쿠키 접근 방지
