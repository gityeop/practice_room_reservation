from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        department = request.form.get('department')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # 비밀번호 일치 여부 확인
        if password != password_confirm:
            flash('비밀번호가 일치하지 않습니다.')
            return redirect(url_for('auth.register'))
        
        # 이미 등록된 학번인지 확인
        user = User.query.filter_by(student_id=student_id).first()
        if user:
            flash('이미 등록된 학번입니다.')
            return redirect(url_for('auth.register'))
        
        # 새 사용자 생성
        new_user = User(name=name, student_id=student_id, department=department)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다!')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

# 학번 중복 확인 API
@auth_bp.route('/check-student-id', methods=['POST'])
def check_student_id():
    student_id = request.form.get('student_id')
    
    if not student_id:
        return {'exists': False, 'message': '학번을 입력해주세요.'}, 400
    
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
        
        user = User.query.filter_by(student_id=student_id).first()
        
        if not user or not user.check_password(password):
            flash('학번 또는 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('reservation.dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('로그아웃 되었습니다.')
    return redirect(url_for('auth.login'))

# 내 계정 정보 보기 및 편집
@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # 현재는 비밀번호 변경만 허용
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 현재 비밀번호 확인
        if not current_user.check_password(current_password):
            flash('현재 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('auth.profile'))
        
        # 새 비밀번호 확인
        if new_password != confirm_password:
            flash('새 비밀번호가 일치하지 않습니다.')
            return redirect(url_for('auth.profile'))
        
        # 비밀번호 변경
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('비밀번호가 성공적으로 변경되었습니다.')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html')
