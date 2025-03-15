import os
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
from routes.auth import auth_bp
from routes.reservation import reservation_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.config.from_object(Config)

# 데이터베이스 초기화
db.init_app(app)

# 로그인 관리자 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 블루프린트 등록
app.register_blueprint(auth_bp)
app.register_blueprint(reservation_bp)
app.register_blueprint(admin_bp)

# 데이터베이스 생성 및 관리자 계정 생성
with app.app_context():
    db.create_all()
    
    # 관리자 계정이 없으면 생성
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        admin = User(
            name="관리자",
            student_id=Config.ADMIN_USERNAME,
            department="관리자",
            is_admin=True
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()

# 애플리케이션 설정 완료 메시지
print('Lab Reservation System initialized!')

if __name__ == '__main__':
    # 환경 변수에서 실행 모드 확인 (개발/운영)
    is_dev = os.environ.get('FLASK_ENV') == 'development'
    
    # 개발 모드에서만 디버그 활성화
    app.run(
        host='0.0.0.0', 
        port=int(os.environ.get('PORT', 5001)), 
        debug=is_dev
    )
