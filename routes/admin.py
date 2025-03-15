from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Reservation, BlockedTime, User
from datetime import datetime
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def restrict_to_admins():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자 권한이 필요합니다.')
        return redirect(url_for('auth.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # 현재 날짜 가져오기
    today = datetime.now().date()
    
    # 필터 파라미터 처리
    filter_type = request.args.get('filter', 'all')  # 기본값은 'all'
    date_range = request.args.get('range', 'week')   # 기본값은 'week'
    
    # 기본 쿼리 생성
    query = Reservation.query
    
    # 날짜 범위 필터링
    if date_range == 'week':
        # 오늘부터 7일 후까지
        from datetime import timedelta
        week_later = today + timedelta(days=7)
        query = query.filter(Reservation.date >= today, Reservation.date <= week_later)
    else:
        # 'all'인 경우
        # 지난 예약도 모두 보여줌
        pass
    
    # 상태 필터링
    if filter_type != 'all':
        query = query.filter_by(status=filter_type)
    
    # 최신순으로 날짜 가져오기 (중복 없이)
    dates = query.with_entities(Reservation.date).distinct().order_by(Reservation.date.desc()).all()
    dates = [date[0] for date in dates]  # 튜플에서 날짜만 추출
    
    # 날짜별 예약 그룹화
    grouped_reservations = {}
    for date in dates:
        # 각 날짜에 해당하는 예약을 시간순으로 정렬
        date_reservations = query.filter(Reservation.date == date).order_by(Reservation.start_time).all()
        grouped_reservations[date] = date_reservations
    
    # 상태별 예약 정보 가져오기 (화면 아래쪽 목록용)
    pending_reservations = Reservation.query.filter_by(status='pending').order_by(Reservation.date, Reservation.start_time).all()
    approved_reservations = Reservation.query.filter_by(status='approved').order_by(Reservation.date, Reservation.start_time).all()
    rejected_reservations = Reservation.query.filter_by(status='rejected').order_by(Reservation.date, Reservation.start_time).all()
    canceled_reservations = Reservation.query.filter_by(status='canceled').order_by(Reservation.date, Reservation.start_time).all()
    
    # 템플릿으로 모든 데이터 전달
    return render_template('admin/dashboard.html', 
                           grouped_reservations=grouped_reservations,
                           dates=dates,  # 정렬된 날짜 목록
                           pending_reservations=pending_reservations,
                           approved_reservations=approved_reservations,
                           rejected_reservations=rejected_reservations,
                           canceled_reservations=canceled_reservations,
                           filter_type=filter_type,
                           date_range=date_range,
                           today=today)

@admin_bp.route('/approve/<int:reservation_id>', methods=['POST'])
@login_required
def approve_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = 'approved'
    db.session.commit()
    flash('예약이 승인되었습니다.')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reject/<int:reservation_id>', methods=['POST'])
@login_required
def reject_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = 'rejected'
    db.session.commit()
    flash('예약이 거부되었습니다.')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/block-time', methods=['GET', 'POST'])
@login_required
def block_time():
    if request.method == 'POST':
        # 기존 단일 차단 방식 외에도 배치 차단도 처리
        if 'batch' in request.form:
            # JSON 데이터로 여러 시간대 차단 처리
            import json
            time_blocks = json.loads(request.form.get('time_blocks'))
            
            for block in time_blocks:
                date_str = block.get('date')
                start_time_str = block.get('start_time')
                end_time_str = block.get('end_time')
                reason = block.get('reason')
                
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    start_time = datetime.strptime(start_time_str, '%H:%M').time()
                    end_time = datetime.strptime(end_time_str, '%H:%M').time()
                    
                    blocked_time = BlockedTime(
                        date=date,
                        start_time=start_time,
                        end_time=end_time,
                        reason=reason
                    )
                    
                    db.session.add(blocked_time)
                except ValueError:
                    continue  # 잘못된 형식은 건너뛰기
            
            db.session.commit()
            flash('선택한 모든 시간대가 차단되었습니다.')
            return redirect(url_for('admin.block_time'))
        else:
            # 단일 시간대 차단 (기존 방식)
            date_str = request.form.get('date')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            reason = request.form.get('reason')
            
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
            except ValueError:
                flash('날짜 또는 시간 형식이 올바르지 않습니다.')
                return redirect(url_for('admin.block_time'))
            
            blocked_time = BlockedTime(
                date=date,
                start_time=start_time,
                end_time=end_time,
                reason=reason
            )
            
            db.session.add(blocked_time)
            db.session.commit()
            
            flash('시간이 차단되었습니다.')
            return redirect(url_for('admin.block_time'))
    
    # 캘린더에 표시할 데이터 준비
    blocked_times = BlockedTime.query.all()
    
    # 예약 데이터도 함께 전달 (예약된 시간은 차단 불가)
    all_reservations = Reservation.query.filter(
        Reservation.status.in_(['pending', 'approved'])
    ).all()
    
    # JavaScript에서 사용할 수 있도록 JSON 형태로 변환
    blocked_times_json = []
    for block in blocked_times:
        blocked_times_json.append({
            'id': block.id,
            'date': block.date.strftime('%Y-%m-%d'),
            'start_time': block.start_time.strftime('%H:%M'),
            'end_time': block.end_time.strftime('%H:%M'),
            'reason': block.reason
        })
    
    reservations_json = []
    for reservation in all_reservations:
        user = User.query.get(reservation.user_id)
        reservations_json.append({
            'id': reservation.id,
            'date': reservation.date.strftime('%Y-%m-%d'),
            'start_time': reservation.start_time.strftime('%H:%M'),
            'end_time': reservation.end_time.strftime('%H:%M'),
            'status': reservation.status,
            'purpose': reservation.purpose,
            'user_name': user.name,
            'user_department': user.department
        })
    
    return render_template('admin/block_time.html', 
                           blocked_times=blocked_times,
                           blocked_times_json=blocked_times_json,
                           reservations_json=reservations_json)

@admin_bp.route('/unblock/<int:block_id>', methods=['POST'])
@login_required
def unblock_time(block_id):
    blocked_time = BlockedTime.query.get_or_404(block_id)
    db.session.delete(blocked_time)
    db.session.commit()
    flash('차단된 시간이 해제되었습니다.')
    return redirect(url_for('admin.block_time'))

@admin_bp.route('/stats')
@login_required
def stats():
    # 학과별 통계
    dept_stats = db.session.query(
        User.department,
        func.count(Reservation.id).label('reservation_count')
    ).join(Reservation, Reservation.user_id == User.id)\
     .filter(Reservation.status == 'approved')\
     .group_by(User.department).all()
    
    # 시간대별 통계
    hour_stats = db.session.query(
        func.extract('hour', Reservation.start_time).label('hour'),
        func.count(Reservation.id).label('reservation_count')
    ).filter(Reservation.status == 'approved')\
     .group_by('hour').all()
    
    return render_template('admin/stats.html', dept_stats=dept_stats, hour_stats=hour_stats)

@admin_bp.route('/users')
@login_required
def manage_users():
    """회원 관리 페이지를 출력합니다."""
    # 관리자를 제외한 모든 사용자 가져오기
    users = User.query.filter(User.is_admin == False).order_by(User.name).all()
    
    # 각 사용자별 예약 횟수 정보 가져오기
    user_stats = {}
    for user in users:
        reservation_count = Reservation.query.filter_by(user_id=user.id).count()
        user_stats[user.id] = {
            'total_reservations': reservation_count,
            'cancel_count': user.cancel_count
        }
    
    return render_template('admin/users.html', users=users, user_stats=user_stats)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """회원 탈퇴 처리를 합니다."""
    user = User.query.get_or_404(user_id)
    
    # 관리자 계정은 삭제할 수 없음
    if user.is_admin:
        flash('관리자 계정은 삭제할 수 없습니다.')
        return redirect(url_for('admin.manage_users'))
    
    # 회원의 예약 정보를 삭제하거나 업데이트
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    
    # 현재나 미래의 예약이 있는지 확인
    has_active_reservations = False
    for reservation in reservations:
        if reservation.date >= datetime.now().date() and reservation.status in ['pending', 'approved']:
            has_active_reservations = True
            break
    
    if has_active_reservations:
        flash('사용자에게 진행 중이거나 예정된 예약이 있습니다. 예약을 취소하거나 완료한 후 다시 시도해주세요.')
        return redirect(url_for('admin.manage_users'))
    
    # 사용자 삭제 처리
    try:
        # 예약 정보 삭제
        for reservation in reservations:
            db.session.delete(reservation)
        
        # 사용자 삭제
        db.session.delete(user)
        db.session.commit()
        flash(f'사용자 {user.name}({user.student_id})이(가) 삭제되었습니다.')
    except Exception as e:
        db.session.rollback()
        flash(f'사용자 삭제 중 오류가 발생했습니다: {str(e)}')
    
    return redirect(url_for('admin.manage_users'))
