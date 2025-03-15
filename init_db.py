from app import app, db
from models import User
from config import Config

# 데이터베이스 초기화 함수
def initialize_database():
    """데이터베이스를 초기화하고 관리자 계정을 생성합니다."""
    with app.app_context():
        # 기존 데이터베이스 삭제
        print("기존 데이터베이스 삭제 중...")
        db.drop_all()
        
        # 새 데이터베이스 스키마 생성
        print("새 데이터베이스 스키마 생성 중...")
        db.create_all()
        
        # 관리자 계정 생성
        print("관리자 계정 생성 중...")
        admin = User(
            name="관리자",
            student_id=Config.ADMIN_USERNAME,
            department="관리자",
            is_admin=True
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        
        print("데이터베이스 초기화 완료!")
        print(f"관리자 로그인 정보: {Config.ADMIN_USERNAME} / {Config.ADMIN_PASSWORD}")

# 스크립트가 직접 실행될 때만 초기화 수행
if __name__ == "__main__":
    # 사용자 확인
    print("경고: 이 작업은 모든 데이터를 삭제합니다!")
    confirmation = input("계속 진행하시겠습니까? (y/n): ")
    
    if confirmation.lower() == 'y':
        initialize_database()
    else:
        print("작업이 취소되었습니다.")
