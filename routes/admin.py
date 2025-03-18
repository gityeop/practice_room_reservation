from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import User
from datetime import datetime, timedelta
import traceback
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 플라스크 애플리케이션에서 리포지토리 가져오기
def get_repo():
    from app import get_repo as app_get_repo
    return app_get_repo()

@admin_bp.before_request
def restrict_to_admins():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('auth.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # 현재 날짜 가져오기
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    # 필터 파라미터 처리
    filter_type = request.args.get('filter', 'all')  # 기본값은 'all'
    date_range = request.args.get('range', 'week')   # 기본값은 'week'
    
    # Supabase 리포지토리 가져오기
    repo = get_repo()
    
    # 날짜 범위 설정
    week_later = today + timedelta(days=7)
    week_later_str = week_later.strftime('%Y-%m-%d')
    
    # Supabase에서 예약 데이터 가져오기
    all_reservations = []
    try:
        if date_range == 'week':
            # 오늘부터 7일 후까지
            all_reservations = repo.get_reservations_by_date_range(today_str, week_later_str, filter_type)
        else:
            # 'all'인 경우, 모든 예약 가져오기
            all_reservations = repo.get_all_reservations(filter_type if filter_type != 'all' else None)
    except Exception as e:
        flash(f'데이터 로딩 중 오류가 발생했습니다: {str(e)}', 'error')
        traceback.print_exc()  # 로그에 상세 오류 출력
    
    # 데이터 그룹화 및 정렬
    dates = set()  # datetime 객체 저장
    grouped_reservations = {}
    pending_reservations = []
    approved_reservations = []
    rejected_reservations = []
    canceled_reservations = []
    
    # 정렬 함수 정의
    def sort_reservations(res_list):
        # Supabase 데이터와 SQLite 데이터 모두 처리
        if res_list and isinstance(res_list[0], dict):
            return sorted(res_list, key=lambda x: (x.get('date'), x.get('start_time')))
        else:
            return sorted(res_list, key=lambda x: (x.date, x.start_time))
    
    for res in all_reservations:
        # Supabase에서 가져온 데이터인 경우
        if isinstance(res, dict):
            date_str = res.get('date')
            status = res.get('status')
            
            # 날짜 문자열을 datetime 객체로 변환
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                dates.add(date_obj)  # datetime 객체 저장
            except (ValueError, TypeError):
                # 날짜 변환 실패 시 오늘 날짜 사용
                date_obj = today
                dates.add(date_obj)
            
            # 날짜별 그룹화 처리 (datetime 객체를 문자열로 변환하여 키로 사용)
            date_key = date_obj.strftime('%Y-%m-%d')
            if date_key not in grouped_reservations:
                grouped_reservations[date_key] = []
            grouped_reservations[date_key].append(res)
            
            # 상태별 분류
            if status == 'pending':
                pending_reservations.append(res)
            elif status == 'approved':
                approved_reservations.append(res)
            elif status == 'rejected':
                rejected_reservations.append(res)
            elif status == 'canceled':
                canceled_reservations.append(res)
        else:  # SQLite 객체인 경우
            date_obj = res.date  # 이미 datetime 객체
            dates.add(date_obj)  # datetime 객체 저장
            
            # 날짜별 그룹화 처리 (datetime 객체를 문자열로 변환하여 키로 사용)
            date_key = date_obj.strftime('%Y-%m-%d')
            if date_key not in grouped_reservations:
                grouped_reservations[date_key] = []
            grouped_reservations[date_key].append(res)
            
            # 상태별 분류
            if res.status == 'pending':
                pending_reservations.append(res)
            elif res.status == 'approved':
                approved_reservations.append(res)
            elif res.status == 'rejected':
                rejected_reservations.append(res)
            elif res.status == 'canceled':
                canceled_reservations.append(res)
    
    # 날짜 정렬 (최신순)
    sorted_dates = sorted(list(dates), reverse=True)
    
    # 각 리스트 정렬
    pending_reservations = sort_reservations(pending_reservations)
    approved_reservations = sort_reservations(approved_reservations)
    rejected_reservations = sort_reservations(rejected_reservations)
    canceled_reservations = sort_reservations(canceled_reservations)
    
    # 각 날짜별 예약 정렬
    for date_key in grouped_reservations:
        grouped_reservations[date_key] = sort_reservations(grouped_reservations[date_key])
    
    # 템플릿으로 모든 데이터 전달
    return render_template('admin/dashboard.html', 
                           grouped_reservations=grouped_reservations,
                           dates=sorted_dates,  # 정렬된 datetime 객체 목록
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
    # Supabase 업데이트
    repo = get_repo()
    try:
        result = repo.update_reservation(reservation_id, {'status': 'approved'})
        if result:
            flash('예약이 승인되었습니다.', 'success')
        else:
            flash('예약 승인 중 오류가 발생했습니다.', 'error')
    except Exception as e:
        flash(f'예약 승인 중 오류: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reject/<int:reservation_id>', methods=['POST'])
@login_required
def reject_reservation(reservation_id):
    # Supabase 업데이트
    repo = get_repo()
    try:
        result = repo.update_reservation(reservation_id, {'status': 'rejected'})
        if result:
            flash('예약이 거부되었습니다.', 'success')
        else:
            flash('예약 거부 중 오류가 발생했습니다.', 'error')
    except Exception as e:
        flash(f'예약 거부 중 오류: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/block-time', methods=['GET', 'POST'])
@login_required
def block_time():
    repo = get_repo()
    
    if request.method == 'POST':
        # 기존 단일 차단 방식 외에도 배치 차단도 처리
        if 'batch' in request.form:
            # JSON 데이터로 여러 시간대 차단 처리
            time_blocks = json.loads(request.form.get('time_blocks'))
            batch_success = True
            
            for block in time_blocks:
                date_str = block.get('date')
                start_time_str = block.get('start_time')
                end_time_str = block.get('end_time')
                reason = block.get('reason')
                
                # Supabase에 차단 시간 추가
                blocked_data = {
                    'date': date_str,
                    'start_time': start_time_str,
                    'end_time': end_time_str,
                    'reason': reason
                }
                
                try:
                    # Supabase에 저장
                    result = repo.create_blocked_time(blocked_data)
                    if not result:
                        batch_success = False
                except Exception as e:
                    batch_success = False
                    print(f"Error creating blocked time: {e}")
            
            if batch_success:
                flash('선택한 모든 시간대가 차단되었습니다.', 'success')
            else:
                flash('일부 시간대 차단 중 오류가 발생했습니다.', 'warning')
                
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
                flash('날짜 또는 시간 형식이 올바르지 않습니다.', 'error')
                return redirect(url_for('admin.block_time'))
            
            # Supabase에 차단 시간 추가
            blocked_data = {
                'date': date_str,
                'start_time': start_time_str,
                'end_time': end_time_str,
                'reason': reason
            }
            
            try:
                result = repo.create_blocked_time(blocked_data)
                if result:
                    flash('시간이 차단되었습니다.', 'success')
                else:
                    flash('시간 차단 중 오류가 발생했습니다.', 'error')
            except Exception as e:
                flash(f'시간 차단 중 오류: {str(e)}', 'error')
            
            return redirect(url_for('admin.block_time'))
    
    # 캘린더에 표시할 데이터 준비 (Supabase 사용)
    try:
        blocked_times = repo.get_all_blocked_times()
        # 예약 데이터도 함께 전달 (Supabase 사용)
        all_reservations = repo.get_all_reservations(['pending', 'approved'])
    except Exception as e:
        flash(f'데이터를 불러오는 중 오류가 발생했습니다: {str(e)}', 'error')
        blocked_times = []
        all_reservations = []
    
    # JavaScript에서 사용할 수 있도록 JSON 형태로 변환
    blocked_times_json = []
    for block in blocked_times:
        # Supabase 데이터로 변환
        blocked_times_json.append({
            'id': block.get('id'),
            'date': block.get('date'),
            'start_time': block.get('start_time'),
            'end_time': block.get('end_time'),
            'reason': block.get('reason')
        })
    
    reservations_json = []
    for reservation in all_reservations:
        user_id = reservation.get('user_id')
        user_data = repo.get_user_by_id(user_id)
        
        if user_data:
            reservations_json.append({
                'id': reservation.get('id'),
                'date': reservation.get('date'),
                'start_time': reservation.get('start_time'),
                'end_time': reservation.get('end_time'),
                'status': reservation.get('status'),
                'purpose': reservation.get('purpose'),
                'user_name': user_data.get('name', 'Unknown'),
                'user_department': user_data.get('department', 'Unknown')
            })
    
    return render_template('admin/block_time.html', 
                          blocked_times=blocked_times,
                          blocked_times_json=blocked_times_json,
                          reservations_json=reservations_json)

@admin_bp.route('/unblock/<int:block_id>', methods=['POST'])
@login_required
def unblock_time(block_id):
    # Supabase에서 차단 시간 삭제
    repo = get_repo()
    try:
        result = repo.delete_blocked_time(block_id)
        if result:
            flash('차단된 시간이 해제되었습니다.', 'success')
        else:
            flash('차단 시간 해제 중 오류가 발생했습니다.', 'error')
    except Exception as e:
        flash(f'차단 시간 해제 중 오류: {str(e)}', 'error')
    
    return redirect(url_for('admin.block_time'))

@admin_bp.route('/stats')
@login_required
def stats():
    repo = get_repo()
    
    # Supabase에서 통계 데이터 조회 시도
    try:
        # 학과별 통계
        dept_stats = repo.get_department_stats()
        
        # 시간대별 통계
        hour_stats = repo.get_hour_stats()
        
        # 데이터가 없는 경우 (빈 리스트인 경우) 정보 메시지 표시
        if (dept_stats is not None and len(dept_stats) == 0) and \
           (hour_stats is not None and len(hour_stats) == 0):
            flash('현재 통계를 위한 예약 데이터가 없습니다.', 'info')
    except Exception as e:
        flash(f'통계 데이터를 가져오는 중 오류 발생: {str(e)}', 'error')
        # 오류 발생 시 빈 데이터 제공
        dept_stats = []
        hour_stats = []
    
    return render_template('admin/stats.html', dept_stats=dept_stats, hour_stats=hour_stats)

@admin_bp.route('/users')
@login_required
def manage_users():
    """회원 관리 페이지를 출력합니다."""
    repo = get_repo()
    
    try:
        # Supabase에서 사용자 데이터 가져오기 (관리자 제외)
        users = repo.get_all_non_admin_users()
        
        # 각 사용자별 예약 횟수 정보 가져오기
        user_stats = {}
        for user in users:
            user_id = user.get('id')
            user_stats[user_id] = {
                'total_reservations': repo.count_user_reservations(user_id),
                'cancel_count': user.get('cancel_count', 0)
            }
    except Exception as e:
        flash(f'사용자 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}', 'error')
        users = []
        user_stats = {}
    
    return render_template('admin/users.html', users=users, user_stats=user_stats)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """회원 탈퇴 처리를 합니다."""
    repo = get_repo()
    
    try:
        # Supabase에서 사용자 정보 가져오기
        user_data = repo.get_user_by_id(user_id)
        
        if not user_data:
            flash('해당 사용자를 찾을 수 없습니다.', 'error')
            return redirect(url_for('admin.manage_users'))
        
        # 관리자 계정은 삭제할 수 없음
        if user_data.get('is_admin'):
            flash('관리자 계정은 삭제할 수 없습니다.', 'error')
            return redirect(url_for('admin.manage_users'))
        
        # 현재나 미래의 예약이 있는지 확인
        # 예약 정보 가져오기
        active_reservations = repo.get_active_reservations_by_user(user_id)
        
        if active_reservations and len(active_reservations) > 0:
            flash('사용자에게 진행 중이거나 예정된 예약이 있습니다. 예약을 취소하거나 완료한 후 다시 시도해주세요.', 'error')
            return redirect(url_for('admin.manage_users'))
        
        # 사용자의 모든 예약 삭제 처리
        repo.delete_all_user_reservations(user_id)
        
        # 사용자 삭제 처리
        result = repo.delete_user(user_id)
        
        if result:
            flash(f"사용자 {user_data.get('name')}({user_data.get('student_id')})이(가) 삭제되었습니다.", 'success')
        else:
            flash('사용자 삭제 중 오류가 발생했습니다.', 'error')
    except Exception as e:
        flash(f'사용자 삭제 중 오류가 발생했습니다: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_users'))
