from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Reservation, BlockedTime, User
from datetime import datetime, timedelta
from config import Config

reservation_bp = Blueprint('reservation', __name__)

# 플라스크 애플리케이션에서 리포지토리 가져오기
def get_repo():
    from app import get_repo as app_get_repo
    return app_get_repo()

@reservation_bp.route('/')
@reservation_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    # Supabase에서 예약 데이터 가져오기
    repo = get_repo()
    user_reservations = repo.get_user_reservations(current_user.id)
    
    return render_template('dashboard.html', reservations=user_reservations)

@reservation_bp.route('/reserve', methods=['GET', 'POST'])
@login_required
def reserve():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
        
    # 현재 날짜와 시간
    now = datetime.now()
    
    # 테스트 모드
    TEST_MODE = True
    
    if TEST_MODE:
        # 테스트 모드일 때는 항상 예약 가능
        is_saturday = True
        is_sunday = True
        is_culture_content = True
        is_booking_time = True
    else:
        # 일반 모드일 때는 실제 날짜와 시간을 확인
        is_saturday = now.weekday() == 5  # 토요일
        is_sunday = now.weekday() == 6    # 일요일
        is_culture_content = current_user.department == Config.CULTURE_CONTENT_DEPT
        
        # 예약 가능 시간 확인 (10AM-10PM)
        is_booking_time = 10 <= now.hour < 24
    
    # 예약 가능 여부 확인 (수정됨)
    # 일요일: 다음 주의 모든 날짜를 예약 가능
    # 토요일: 문화콘텐츠학과 학생만 다음 주 모든 날짜 예약 가능
    can_book = ((is_saturday and is_culture_content) or is_sunday) and is_booking_time
    
    if not can_book and not current_user.is_admin:
        flash('예약은 일요일 오전 10시부터 오후 10시 사이, 문화콘텐츠학과 학생의 경우 토요일 동일 시간대에 가능합니다. 선택한 요일에 다음 주 전체 날짜를 예약할 수 있습니다.', 'error')
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
            flash('날짜 또는 시간 형식이 올바르지 않습니다.', 'error')
            return redirect(url_for('reservation.reserve'))
        
        # 시간 검증
        start_datetime = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)
        
        # 예약 시간이 3시간을 초과하는지 확인
        duration = (end_datetime - start_datetime).total_seconds() / 3600
        if duration > Config.MAX_HOURS_PER_DAY:
            flash(f'하루 최대 예약 시간은 {Config.MAX_HOURS_PER_DAY}시간입니다.', 'error')
            return redirect(url_for('reservation.reserve'))
        
        if start_time >= end_time:
            flash('종료 시간은 시작 시간보다 나중이어야 합니다.', 'error')
            return redirect(url_for('reservation.reserve'))
        
        # Supabase 리포지토리 가져오기
        repo = get_repo()
        
        # 이미 예약된 시간과 겹치는지 확인 (Supabase 사용)
        existing_reservations = repo.get_overlapping_reservations(
            date_str,
            start_time_str,
            end_time_str
        )
        
        if existing_reservations and len(existing_reservations) > 0:
            flash('선택한 시간에 이미 예약이 있습니다.', 'error')
            return redirect(url_for('reservation.reserve'))
        
        # 차단된 시간과 겹치는지 확인 (Supabase 사용)
        blocked_times = repo.get_overlapping_blocked_times(
            date_str,
            start_time_str,
            end_time_str
        )
        
        if blocked_times and len(blocked_times) > 0:
            reasons = [block.get('reason', '알 수 없는 이유') for block in blocked_times]
            flash(f"선택한 시간은 {', '.join(reasons)}으로 인해 예약할 수 없습니다.", 'error')
            return redirect(url_for('reservation.reserve'))
        
        # 예약 데이터 준비
        reservation_data = {
            'user_id': current_user.id,
            'date': date_str,
            'start_time': start_time_str,
            'end_time': end_time_str,
            'purpose': purpose,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Supabase에 예약 추가
        result = repo.create_reservation(reservation_data)
        
        if result:
            flash('예약이 신청되었습니다. 관리자 승인을 기다려주세요.', 'success')
        else:
            flash('예약 신청 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
        
        return redirect(url_for('reservation.dashboard'))
    
    # 캘린더 뷰에 필요한 데이터 준비
    repo = get_repo()
    
    # 1. 차단된 시간 가져오기 (Supabase 사용)
    blocked_times = repo.get_all_blocked_times()
    
    # 2. 예약 현황 조회 (Supabase 사용)
    existing_reservations = repo.get_all_reservations(['pending', 'approved'])
    
    # JavaScript에서 사용할 수 있도록 JSON 형태로 변환
    blocked_times_json = []
    for block in blocked_times:
        # Supabase에서 가져온 데이터 형식 확인
        if isinstance(block, dict):
            date_str = block.get('date')
            start_time_str = block.get('start_time')
            end_time_str = block.get('end_time')
            blocked_times_json.append({
                'id': block.get('id'),
                'date': date_str,
                'start_time': start_time_str,
                'end_time': end_time_str,
                'reason': block.get('reason')
            })
    
    existing_reservations_json = []
    for res in existing_reservations:
        # Supabase에서 가져온 데이터 형식 확인
        if isinstance(res, dict):
            user_id = res.get('user_id')
            user_data = repo.get_user_by_id(user_id)
            user_name = user_data.get('name', 'Unknown') if user_data else 'Unknown'
            
            existing_reservations_json.append({
                'id': res.get('id'),
                'date': res.get('date'),
                'start_time': res.get('start_time'),
                'end_time': res.get('end_time'),
                'status': res.get('status'),
                'purpose': res.get('purpose'),
                'user_name': user_name,
                'user_id': user_id
            })
    
    return render_template('reservation.html', 
                           blocked_times=blocked_times,
                           blocked_times_json=blocked_times_json,
                           existing_reservations_json=existing_reservations_json,
                           max_hours=Config.MAX_HOURS_PER_DAY)

@reservation_bp.route('/cancel/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    # Supabase와 SQLite 모두에서 예약 정보 가져오기
    repo = get_repo()
    reservation_data = repo.get_reservation_by_id(reservation_id)
    
    # Supabase에서 예약을 찾지 못한 경우 SQLite에서 확인
    if not reservation_data:
        reservation = Reservation.query.get_or_404(reservation_id)
        user_id = reservation.user_id
    else:
        user_id = reservation_data.get('user_id')
    
    # 사용자 소유의 예약인지 확인
    if user_id != current_user.id and not current_user.is_admin:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('reservation.dashboard'))
    
    # 관리자는 제한 없이 예약 취소 가능, 일반 사용자는 하루 전까지만 취소 가능
    if not current_user.is_admin and reservation_data:
        now = datetime.now()
        reservation_date_str = reservation_data.get('date')
        reservation_time_str = reservation_data.get('start_time')
        
        # 날짜와 시간 문자열을 datetime 객체로 변환
        reservation_datetime_str = f"{reservation_date_str} {reservation_time_str}"
        
        # 시간 형식 처리 (HH:MM 또는 HH:MM:SS)
        try:
            # 기본 파싱 시도 (%Y-%m-%d %H:%M)
            reservation_datetime = datetime.strptime(reservation_datetime_str, '%Y-%m-%d %H:%M')
        except ValueError:
            try:
                # 초 포함된 형식으로 시도 (%Y-%m-%d %H:%M:%S)
                reservation_datetime = datetime.strptime(reservation_datetime_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # 만약 그래도 실패하면 시간 문자열을 수정하여 다시 시도
                if ':00' in reservation_time_str:
                    clean_time = reservation_time_str.replace(':00', '')
                    clean_datetime_str = f"{reservation_date_str} {clean_time}"
                    reservation_datetime = datetime.strptime(clean_datetime_str, '%Y-%m-%d %H:%M')
                else:
                    # 그래도 실패하면 예외 발생 - 결과적으로 취소 불가
                    flash('날짜 형식을 처리할 수 없습니다.', 'error')
                    return redirect(url_for('reservation.dashboard'))
        
        if (reservation_datetime - now).total_seconds() < 24 * 3600:
            flash('예약은 하루 전까지만 취소할 수 있습니다.', 'error')
            return redirect(url_for('reservation.dashboard'))
    
    # 취소 횟수 증가 (관리자가 아닌 경우)
    if not current_user.is_admin:
        current_user.cancel_count += 1
        # Supabase에 취소 횟수 업데이트
        repo.update_user(current_user.id, {'cancel_count': current_user.cancel_count})
    
    # Supabase에서 예약 상태 업데이트
    repo.update_reservation(reservation_id, {'status': 'canceled'})
    
    flash('예약이 취소되었습니다.', 'success')
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('reservation.dashboard'))
