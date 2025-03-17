import os
from flask import Flask, send_from_directory
from flask_login import LoginManager
from config import Config
from models import db, User
from routes.auth import auth_bp
from routes.reservation import reservation_bp
from routes.admin import admin_bp
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

# 데이터베이스 초기화
db.init_app(app)

# 마이그레이션 설정
migrate = Migrate(app, db)

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

# favicon.ico uc81cucacf5 ub77cuc6b0ud2b8 ucd94uac00
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images', 'characters'),
                               'cc_logo.png', mimetype='image/png')

# 데이터베이스 생성 및 관리자 계정 생성
with app.app_context():
    # 새 칼럼 추가 위해 db.create_all() 실행
    db.create_all()
    
    # 관리자 계정이 없으면 생성 (token 필드 오류 방지)
    try:
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
    except Exception as e:
        print(f"관리자 계정 확인 중 오류 발생: {e}")
        # 데이터베이스 스키마 변경 후 재시도 필요

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
