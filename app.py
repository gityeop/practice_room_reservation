import os
from flask import Flask, send_from_directory, g, session, redirect, url_for, flash
from flask_login import LoginManager, current_user, logout_user
from config import Config
from models import db, User
from routes.auth import auth_bp
from routes.reservation import reservation_bp
from routes.admin import admin_bp
from flask_migrate import Migrate
from repository import SupabaseRepository

app = Flask(__name__)
app.config.from_object(Config)

# 데이터베이스 초기화 (SQLAlchemy - 기존 코드와의 호환성 유지)
db.init_app(app)

# 마이그레이션 설정
migrate = Migrate(app, db)

# Supabase 리포지토리 생성 함수
def get_repo():
    """Supabase 리포지토리 인스턴스를 가져오거나 생성합니다."""
    if 'repo' not in g:
        g.repo = SupabaseRepository()
    return g.repo

# 요청이 끝날 때 리소스 정리
@app.teardown_appcontext
def teardown_repo(exception):
    """애플리케이션 컨텍스트가 종료될 때 호출되는 함수입니다."""
    repo = g.pop('repo', None)
    if repo is not None:
        # 필요한 경우 리소스 정리 로직 추가
        pass

# 로그인 관리자 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# ---------------------------------------------------------------------------
# 세션 토큰 검증 훅
# ---------------------------------------------------------------------------
@app.before_request
def enforce_single_session():
    """요청마다 세션 토큰의 유효성을 확인하여 다른 기기에서 로그인 시 기존 세션을 종료합니다."""
    # 로그인 필요 없는 엔드포인트(정적 파일 등)는 무시
    # current_user는 Flask-Login이 제공
    if current_user.is_authenticated:
        token = session.get('token')
        if not token:
            # 세션에 토큰이 없으면 로그아웃 처리
            logout_user()
            flash('세션이 만료되었습니다. 다시 로그인해주세요.', 'warning')
            return redirect(url_for('auth.login'))

        repo = get_repo()
        user_data = repo.get_user_by_token(token)

        # 토큰이 유효하지 않거나 다른 사용자에게 할당된 경우 -> 로그아웃
        if not user_data or user_data.get('id') != current_user.id:
            # 세션 및 로그인 정보 제거
            session.pop('token', None)
            logout_user()
            flash('다른 기기에서 로그인되어 세션이 종료되었습니다.', 'warning')
            return redirect(url_for('auth.login'))

@login_manager.user_loader
def load_user(user_id):
    """사용자 ID로 사용자 객체를 로드합니다. Supabase 사용."""
    try:
        repo = get_repo()
        user_data = repo.get_user_by_id(int(user_id))
        if user_data:
            # Supabase에서 가져온 데이터로 User 객체 생성
            user = User(
                id=user_data['id'],
                name=user_data['name'],
                student_id=user_data['student_id'],
                department=user_data['department'],
                password_hash=user_data['password_hash'],
                is_admin=user_data['is_admin'],
                cancel_count=user_data['cancel_count'],
                token=user_data['token'],
                token_expiration=user_data['token_expiration']
            )
            return user
        return None
    except Exception as e:
        print(f"사용자 로드 중 오류 발생: {e}")
        # 오류 발생 시 기존 SQLAlchemy 방식으로 시도
        return User.query.get(int(user_id))

# 블루프린트 등록
app.register_blueprint(auth_bp)
app.register_blueprint(reservation_bp)
app.register_blueprint(admin_bp)

# Supabase 리포지토리를 애플리케이션 컨텍스트에 추가
@app.context_processor
def inject_repo():
    """모든 템플릿에 리포지토리를 제공합니다."""
    return dict(repo=get_repo())

# favicon.ico uc81cucacf5 ub77cuc6b0ud2b8 ucd94uac00
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images', 'characters'),
                               'cc_logo.png', mimetype='image/png')

# 데이터베이스 생성 및 관리자 계정 생성 (SQLAlchemy 사용, 백업 목적으로 유지)
with app.app_context():
    # SQLite 백업용 DB에만 테이블을 생성 (원격 Postgres에는 생성하지 않음)
    try:
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            db.create_all()
    except Exception as e:
        print(f"로컬 DB 테이블 생성 중 오류: {e}")
    
    # 관리자 계정이 없으면 생성 (token 필드 오류 방지)
    try:
        # Supabase에서 관리자 계정 확인
        repo = get_repo()
        admin = repo.get_user_by_student_id(Config.ADMIN_USERNAME)
        
        if not admin:
            # SQLAlchemy로 확인
            admin = User.query.filter_by(is_admin=True).first()
            
            if not admin:
                # 관리자 계정 생성
                admin = User(
                    name="관리자",
                    student_id=Config.ADMIN_USERNAME,
                    department="관리자",
                    is_admin=True
                )
                admin.set_password(Config.ADMIN_PASSWORD)
                
                # Supabase에 추가
                admin_data = {
                    'name': admin.name,
                    'student_id': admin.student_id,
                    'department': admin.department,
                    'password_hash': admin.password_hash,
                    'is_admin': admin.is_admin,
                    'cancel_count': 0,
                    'token': None,
                    'token_expiration': None
                }
                repo.create_user(admin_data)
                
                # SQLite에도 추가 (백업)
                db.session.add(admin)
                db.session.commit()
    except Exception as e:
        print(f"관리자 계정 확인 중 오류 발생: {e}")
        # 데이터베이스 스키마 변경 후 재시도 필요

# 애플리케이션 설정 완료 메시지
print('Lab Reservation System initialized with Supabase!')

if __name__ == '__main__':
    # 환경 변수에서 실행 모드 확인 (개발/운영)
    is_dev = os.environ.get('FLASK_ENV') == 'development'
    
    # 개발 모드에서만 디버그 활성화
    app.run(
        host='0.0.0.0', 
        port=int(os.environ.get('PORT', 5001)), 
        debug=is_dev
    )
