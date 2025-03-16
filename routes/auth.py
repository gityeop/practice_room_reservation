from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import re
from functools import wraps

auth_bp = Blueprint('auth', __name__)

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
            
        user = User.check_token(token)
        if not user:
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
        
        # 이미 등록된 학번인지 확인
        user = User.query.filter_by(student_id=student_id).first()
        if user:
            flash('이미 등록된 학번입니다.', 'error')
            return redirect(url_for('auth.register'))
        
        # 새 사용자 생성
        new_user = User(name=name, student_id=student_id, department=major)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다!', 'success')
        return redirect(url_for('auth.login'))
    
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
    
    # 데이터베이스에서 학번 조회
    user = User.query.filter_by(student_id=student_id).first()
    
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
            
        user = User.query.filter_by(student_id=student_id).first()
        
        if not user or not user.check_password(password):
            flash('학번 또는 비밀번호가 올바르지 않습니다.', 'error')
            return redirect(url_for('auth.login'))
        
        # 이미 로그인된 세션이 있는지 확인
        existing_user = User.check_token(user.token)
        if existing_user:
            # 기존 세션 무효화 (선택적으로 구현 가능)
            existing_user.revoke_token()
            flash('다른 기기에서의 로그인 세션이 종료되었습니다.', 'warning')
        
        # 새 토큰 발급
        token = user.get_token()
        
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
    # 토큰 무효화
    if current_user:
        current_user.revoke_token()
    
    # 세션에서 토큰 제거
    session.pop('token', None)
    
    # 로그아웃
    logout_user()
    
    flash('로그아웃 되었습니다.', 'success')
    return redirect(url_for('auth.login'))

# 세션 검증 API
@auth_bp.route('/validate-session', methods=['GET'])
@login_required
def validate_session():
    token = session.get('token')
    if not token:
        return jsonify({'valid': False}), 401
        
    user = User.check_token(token)
    if not user or user.id != current_user.id:
        return jsonify({'valid': False}), 401
        
    return jsonify({'valid': True}), 200

# 내 계정 정보 보기 및 편집
@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@token_required
def profile():
    if request.method == 'POST':
        # 현재는 비밀번호 변경만 허용
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 현재 비밀번호 확인
        if not current_user.check_password(current_password):
            flash('현재 비밀번호가 올바르지 않습니다.', 'error')
            return redirect(url_for('auth.profile'))
        
        # 새 비밀번호 확인
        if new_password != confirm_password:
            flash('새 비밀번호가 일치하지 않습니다.', 'error')
            return redirect(url_for('auth.profile'))
        
        # 비밀번호 변경
        current_user.set_password(new_password)
        db.session.commit()
        
        # 토큰 갱신 (선택적 보안 조치)
        token = current_user.get_token()
        session['token'] = token
        
        flash('비밀번호가 성공적으로 변경되었습니다.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html')
