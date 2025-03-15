from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Reservation, BlockedTime
from datetime import datetime, timedelta
from config import Config

reservation_bp = Blueprint('reservation', __name__)

@reservation_bp.route('/')
@reservation_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
        
    user_reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', reservations=user_reservations)

@reservation_bp.route('/reserve', methods=['GET', 'POST'])
@login_required
def reserve():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
        
    # 현재 날짜와 시간
    now = datetime.now()
    is_saturday = now.weekday() == 5  # 토요일
    is_sunday = now.weekday() == 6    # 일요일
    is_culture_content = current_user.department == Config.CULTURE_CONTENT_DEPT
    
    # 예약 가능 시간 확인 (10AM-10PM)
    is_booking_time = 10 <= now.hour < 24
    
    # 예약 가능 여부 확인 (수정됨)
    # 일요일: 다음 주의 모든 날짜를 예약 가능
    # 토요일: 문화콘텐츠학과 학생만 다음 주 모든 날짜 예약 가능
    can_book = ((is_saturday and is_culture_content) or is_sunday)  and is_booking_time
    
    if not can_book and not current_user.is_admin:
        flash('예약은 일요일 오전 10시부터 오후 10시 사이, 문화콘텐츠학과 학생의 경우 토요일 동일 시간대에 가능합니다. 선택한 요일에 다음 주 전체 날짜를 예약할 수 있습니다.')
        return redirect(url_for('reservation.dashboard'))
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        purpose = request.form.get('purpose')
        
        # 문자열을 datetime 객체로 변환
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            flash('날짜 또는 시간 형식이 올바르지 않습니다.')
            return redirect(url_for('reservation.reserve'))
        
        # 시간 검증
        start_datetime = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)
        
        # 예약 시간이 3시간을 초과하는지 확인
        duration = (end_datetime - start_datetime).total_seconds() / 3600
        if duration > Config.MAX_HOURS_PER_DAY:
            flash(f'하루 최대 예약 시간은 {Config.MAX_HOURS_PER_DAY}시간입니다.')
            return redirect(url_for('reservation.reserve'))
        
        if start_time >= end_time:
            flash('종료 시간은 시작 시간보다 나중이어야 합니다.')
            return redirect(url_for('reservation.reserve'))
        
        # 이미 예약된 시간과 겹치는지 확인
        existing_reservations = Reservation.query.filter(
            Reservation.date == date,
            Reservation.status.in_(['pending', 'approved']),
            Reservation.start_time < end_time,
            Reservation.end_time > start_time
        ).all()
        
        if existing_reservations:
            flash('선택한 시간에 이미 예약이 있습니다.')
            return redirect(url_for('reservation.reserve'))
        
        # 차단된 시간과 겹치는지 확인
        blocked_times = BlockedTime.query.filter(
            BlockedTime.date == date,
            BlockedTime.start_time < end_time,
            BlockedTime.end_time > start_time
        ).all()
        
        if blocked_times:
            reasons = [block.reason for block in blocked_times]
            flash(f'선택한 시간은 {", ".join(reasons)}으로 인해 예약할 수 없습니다.')
            return redirect(url_for('reservation.reserve'))
        
        # 예약 추가
        new_reservation = Reservation(
            user_id=current_user.id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            purpose=purpose
        )
        
        db.session.add(new_reservation)
        db.session.commit()
        
        flash('예약이 신청되었습니다. 관리자 승인을 기다려주세요.')
        return redirect(url_for('reservation.dashboard'))
    
    # 캘린더 뷰에 필요한 데이터 준비
    # 1. 차단된 시간 가져오기
    blocked_times = BlockedTime.query.all()
    
    # 2. 예약 현황 조회
    existing_reservations = Reservation.query.filter(
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
    
    existing_reservations_json = []
    for res in existing_reservations:
        from models import User  # User 모델 임포트
        user = User.query.get(res.user_id)
        existing_reservations_json.append({
            'id': res.id,
            'date': res.date.strftime('%Y-%m-%d'),
            'start_time': res.start_time.strftime('%H:%M'),
            'end_time': res.end_time.strftime('%H:%M'),
            'status': res.status,
            'purpose': res.purpose,
            'user_name': user.name if user else 'Unknown',
            'user_id': user.id if user else 0
        })
    
    return render_template('reservation.html', 
                           blocked_times=blocked_times,
                           blocked_times_json=blocked_times_json,
                           existing_reservations_json=existing_reservations_json,
                           max_hours=Config.MAX_HOURS_PER_DAY)

@reservation_bp.route('/cancel/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    # 사용자 소유의 예약인지 확인
    if reservation.user_id != current_user.id and not current_user.is_admin:
        flash('접근 권한이 없습니다.')
        return redirect(url_for('reservation.dashboard'))
    
    # 관리자는 제한 없이 예약 취소 가능, 일반 사용자는 하루 전까지만 취소 가능
    if not current_user.is_admin:
        now = datetime.now()
        reservation_date = datetime.combine(reservation.date, reservation.start_time)
        if (reservation_date - now).total_seconds() < 24 * 3600:
            flash('예약은 하루 전까지만 취소할 수 있습니다.')
            return redirect(url_for('reservation.dashboard'))
    
    # 취소 횟수 증가 (관리자가 아닌 경우)
    if not current_user.is_admin:
        current_user.cancel_count += 1
        
    reservation.status = 'canceled'
    db.session.commit()
    
    flash('예약이 취소되었습니다.')
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('reservation.dashboard'))
