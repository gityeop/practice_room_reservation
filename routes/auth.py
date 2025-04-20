from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, make_response, g
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import re
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# 플라스크 애플리케이션에서 리포지토리 가져오기
def get_repo():
    from app import get_repo as app_get_repo
    return app_get_repo()

# 학번 유효성 검사 함수
def validate_student_id(student_id):
    """학번 형식을 검증하는 함수. 학번은 정확히 9자리여야 함."""
    # Config에서 설정된 관리자 학번일 경우 True 반환
    from config import Config
    if student_id == Config.ADMIN_USERNAME:
        return True
        
    # 학번이 9자리인지 확인
    if not student_id or len(student_id) != 9:
        return False
    # 학번이 숫자인지 확인
    if not student_id.isdigit():
        return False
    return True

# 토큰 인증 데코레이터
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            flash('로그인이 필요합니다.', 'error')
            return redirect(url_for('auth.login'))
        
        repo = get_repo()
        user_data = repo.get_user_by_token(token)
        if not user_data:
            # 토큰이 유효하지 않으면 세션 삭제 후 재로그인
            session.pop('token', None)
            flash('세션이 만료되었습니다. 다시 로그인해주세요.', 'error')
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        major = request.form.get('major')  # department 대신 major 사용
        password = request.form.get('password')
        password2 = request.form.get('password2')  # password_confirm 대신 password2 사용
        
        # 학번 유효성 검사
        if not validate_student_id(student_id):
            flash('학번은 반드시 9자리여야 합니다.', 'error')
            return redirect(url_for('auth.register'))
        
        # 비밀번호 일치 여부 확인
        if password != password2:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return redirect(url_for('auth.register'))
        
        # 이미 등록된 학번인지 확인 (Supabase 사용)
        repo = get_repo()
        existing_user = repo.get_user_by_student_id(student_id)
        if existing_user:
            flash('이미 등록된 학번입니다.', 'error')
            return redirect(url_for('auth.register'))
        
        # 새 사용자 생성 (SQLAlchemy 및 Supabase 모두 사용)
        new_user = User(name=name, student_id=student_id, department=major)
        new_user.set_password(password)
        
        # Supabase에 사용자 저장
        # 현재 시간 기반 유니크 ID 생성
        import time
        user_id = int(time.time() * 1000)  # 밀리초 단위 타임스탬프
        
        user_data = {
            'id': user_id,  # 생성한 ID 추가
            'name': name,
            'student_id': student_id,
            'department': major,
            'password_hash': new_user.password_hash,
            'is_admin': False,
            'cancel_count': 0,
            'token': None,
            'token_expiration': None
        }
        
        try:
            # Supabase에 사용자 생성
            result = repo.create_user(user_data)
            if result:
                # 백업용으로 SQLite에도 저장
                db.session.add(new_user)
                db.session.commit()
                
                flash('회원가입이 완료되었습니다!', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('회원가입 오류가 발생했습니다. 다시 시도해주세요.', 'error')
                return redirect(url_for('auth.register'))
        except Exception as e:
            flash(f'회원가입 오류: {str(e)}', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('register.html')

# 학번 중복 확인 API
@auth_bp.route('/check-student-id', methods=['POST'])
def check_student_id():
    student_id = request.form.get('student_id')
    
    if not student_id:
        return {'exists': False, 'message': '학번을 입력해주세요.'}, 400
    
    # 학번 유효성 검사
    if not validate_student_id(student_id):
        return {'exists': False, 'message': '학번은 9자리여야 합니다.'}, 400
    
    # Supabase에서 학번 조회
    repo = get_repo()
    user = repo.get_user_by_student_id(student_id)
    
    if user:
        return {'exists': True, 'message': '이미 등록된 학번입니다.'}, 200
    else:
        return {'exists': False, 'message': '사용 가능한 학번입니다.'}, 200

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('reservation.dashboard'))
        
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        
        # 학번 유효성 검사
        if not validate_student_id(student_id):
            flash('학번은 반드시 9자리여야 합니다.', 'error')
            return redirect(url_for('auth.login'))
        
        # Supabase에서 사용자 조회
        repo = get_repo()
        user_data = repo.get_user_by_student_id(student_id)
        
        if not user_data:
            flash('학번 또는 비밀번호가 올바르지 않습니다.', 'error')
            return redirect(url_for('auth.login'))
        
        # User 객체 생성
        user = User(
            id=user_data['id'],
            name=user_data['name'],
            student_id=user_data['student_id'],
            department=user_data['department'],
            password_hash=user_data['password_hash'],
            cancel_count=user_data.get('cancel_count', 0),
            is_admin=user_data.get('is_admin', False),
            token=user_data.get('token'),
            token_expiration=user_data.get('token_expiration')
        )
        
        # 비밀번호 확인
        if not user.check_password(password):
            flash('학번 또는 비밀번호가 올바르지 않습니다.', 'error')
            return redirect(url_for('auth.login'))
        
        # 이미 로그인된 세션이 있는지 확인
        if user.token:
            existing_user = repo.get_user_by_token(user.token)
            if existing_user:
                # 기존 토큰 무효화
                token_data = {
                    'token': None,
                    'token_expiration': None
                }
                repo.update_user(user.id, token_data)
                flash('다른 기기에서의 로그인 세션이 종료되었습니다.', 'warning')
        
        # 새 토큰 발급
        expiration = datetime.utcnow() + timedelta(days=1)
        token = user.generate_token()  # 토큰 생성 메서드
        
        # Supabase에 토큰 정보 업데이트
        token_data = {
            'token': token,
            'token_expiration': expiration.isoformat()
        }
        repo.update_user(user.id, token_data)
        
        # 로그인 처리
        login_user(user)
        
        # 세션에 토큰 저장
        session['token'] = token
        
        # 성공 메시지 표시
        flash('로그인되었습니다.', 'success')
        
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('reservation.dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    repo = get_repo()
    
    # 현재 사용자의 토큰 무효화
    if current_user.is_authenticated:
        token_data = {
            'token': None,
            'token_expiration': None
        }
        try:
            repo.update_user(current_user.id, token_data)
        except Exception as e:
            print(f"토큰 무효화 중 오류: {e}")
    
    # 세션에서 토큰 제거
    session.pop('token', None)
    
    # 로그아웃 처리
    logout_user()
    
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('auth.login'))

# 세션 검증 API
@auth_bp.route('/validate-session', methods=['POST'])
def validate_session():
    token = session.get('token')
    
    if not token:
        return jsonify({'valid': False}), 401
    
    # Supabase에서 토큰으로 사용자 조회
    repo = get_repo()
    user_data = repo.get_user_by_token(token)
    
    if user_data:
        return jsonify({'valid': True}), 200
    else:
        # 세션이 만료된 경우 세션 삭제
        session.pop('token', None)
        return jsonify({'valid': False}), 401

# 내 계정 정보 보기 및 편집
@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        
        # 계정 정보 업데이트
        if action == 'update':
            name = request.form.get('name')
            department = request.form.get('department')
            
            if name and department:
                repo = get_repo()
                
                # Supabase 업데이트
                user_data = {
                    'name': name,
                    'department': department
                }
                
                try:
                    result = repo.update_user(current_user.id, user_data)
                    if result:
                        # SQLite도 업데이트 (백업)
                        current_user.name = name
                        current_user.department = department
                        db.session.commit()
                        
                        flash('계정 정보가 업데이트되었습니다.', 'success')
                    else:
                        flash('업데이트 중 오류가 발생했습니다.', 'error')
                except Exception as e:
                    flash(f'업데이트 오류: {str(e)}', 'error')
            else:
                flash('이름과 학과를 입력해주세요.', 'error')
        
        # 비밀번호 변경
        elif action == 'password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_user.check_password(current_password):
                flash('현재 비밀번호가 올바르지 않습니다.', 'error')
            elif new_password != confirm_password:
                flash('새 비밀번호가 일치하지 않습니다.', 'error')
            elif len(new_password) < 4:
                flash('비밀번호는 최소 4자 이상이어야 합니다.', 'error')
            else:
                # 비밀번호 변경 적용
                current_user.set_password(new_password)
                
                repo = get_repo()
                # Supabase 업데이트
                user_data = {'password_hash': current_user.password_hash}
                
                try:
                    result = repo.update_user(current_user.id, user_data)
                    if result:
                        # SQLite도 업데이트 (백업)
                        db.session.commit()
                        
                        flash('비밀번호가 변경되었습니다.', 'success')
                    else:
                        flash('비밀번호 변경 중 오류가 발생했습니다.', 'error')
                except Exception as e:
                    flash(f'비밀번호 변경 오류: {str(e)}', 'error')
        
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html')
