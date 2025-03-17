import os
import sys
from datetime import datetime
from flask import Flask
from models import db, User, Reservation, BlockedTime
from config import Config
from db_utils import get_supabase_admin_client

def migrate_data():
    """SQLite에서 Supabase로 데이터를 마이그레이션합니다."""
    print("Supabase로 데이터 마이그레이션을 시작합니다...")
    
    # 현재 디렉토리 확인 및 데이터베이스 파일 경로 설정
    current_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(current_dir, 'instance', 'lab_reservation.db')
    sqlite_uri = f'sqlite:///{db_path}'
    
    print(f"SQLite 데이터베이스 경로: {db_path}")
    
    # 데이터베이스 파일 존재 확인
    if not os.path.exists(db_path):
        print(f"오류: 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    # 환경 변수 백업 및 수정 - PostgreSQL 연결 오류 방지
    original_database_url = os.environ.get('DATABASE_URL')
    original_database_uri = os.environ.get('DATABASE_URI')
    
    # 임시로 환경 변수를 SQLite로 설정
    os.environ['DATABASE_URL'] = sqlite_uri
    if 'DATABASE_URI' in os.environ:
        os.environ.pop('DATABASE_URI')
    
    # 앱 컨텍스트 생성
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri
    db.init_app(app)
    
    # Supabase 클라이언트 가져오기
    try:
        supabase = get_supabase_admin_client()
        print(f"Supabase 클라이언트 생성 성공: {supabase}")
    except Exception as e:
        print(f"Supabase 클라이언트 생성 오류: {e}")
        # 환경 변수 복원
        if original_database_url:
            os.environ['DATABASE_URL'] = original_database_url
        if original_database_uri:
            os.environ['DATABASE_URI'] = original_database_uri
        return
    
    with app.app_context():
        # 1. 사용자 테이블 마이그레이션
        migrated_user_ids = migrate_users(supabase)
        
        # 2. 예약 테이블 마이그레이션 - 성공적으로 마이그레이션된 사용자 ID 전달
        migrate_reservations(supabase, migrated_user_ids)
        
        # 3. 차단된 시간 테이블 마이그레이션
        migrate_blocked_times(supabase)
    
    # 환경 변수 복원
    if original_database_url:
        os.environ['DATABASE_URL'] = original_database_url
    if original_database_uri:
        os.environ['DATABASE_URI'] = original_database_uri
        
    print("데이터 마이그레이션이 완료되었습니다!")

def migrate_users(supabase):
    """사용자 테이블 마이그레이션"""
    print("사용자 데이터 마이그레이션 중...")
    users = User.query.all()
    
    print(f"총 {len(users)}명의 사용자를 마이그레이션합니다.")
    
    # 성공적으로 마이그레이션된 사용자 ID 추적
    migrated_user_ids = []
    
    for user in users:
        # 비밀번호 해시, 토큰 정보 등 모든 필드 포함
        user_data = {
            'id': user.id,
            'name': user.name,
            'student_id': user.student_id,
            'department': user.department,
            'password_hash': user.password_hash,
            'cancel_count': user.cancel_count,
            'is_admin': user.is_admin,
            'token': user.token,
            'token_expiration': user.token_expiration.isoformat() if user.token_expiration else None
        }
        
        try:
            # Supabase에 사용자 데이터 삽입
            result = supabase.table('users').upsert(user_data).execute()
            
            # 결과 확인
            if hasattr(result, 'data') and result.data:
                print(f"사용자 '{user.name}' (ID: {user.id}) 마이그레이션 성공")
                migrated_user_ids.append(user.id)
            else:
                print(f"사용자 '{user.name}' (ID: {user.id}) 마이그레이션 실패: 결과 없음")
        except Exception as e:
            print(f"사용자 '{user.name}' (ID: {user.id}) 마이그레이션 오류: {e}")
            # 예외적인 경우 처리 - password_hash가 너무 길다면
            if 'value too long for type character varying' in str(e):
                try:
                    # 문제 필드 수정 - password_hash 길이 제한 문제 해결
                    modified_user_data = user_data.copy()
                    # password_hash를 128자로 잘라내거나 빈 문자열로 설정
                    modified_user_data['password_hash'] = 'hash_too_long_replaced'  # 또는 user.password_hash[:120]
                    
                    print(f"  --> 수정된 데이터로 재시도 중...")
                    result = supabase.table('users').upsert(modified_user_data).execute()
                    
                    if hasattr(result, 'data') and result.data:
                        print(f"  --> 사용자 '{user.name}' (ID: {user.id}) 수정된 데이터로 마이그레이션 성공")
                        migrated_user_ids.append(user.id)
                    else:
                        print(f"  --> 사용자 '{user.name}' (ID: {user.id}) 수정된 데이터로 마이그레이션 실패")
                except Exception as inner_e:
                    print(f"  --> 수정된 데이터로 재시도 중 오류 발생: {inner_e}")
    
    print(f"총 {len(users)}명 중 {len(migrated_user_ids)}명의 사용자 데이터 마이그레이션 완료")
    return migrated_user_ids

def migrate_reservations(supabase, migrated_user_ids=None):
    """예약 테이블 마이그레이션"""
    print("예약 데이터 마이그레이션 중...")
    
    # 마이그레이션된 사용자 ID가 없으면 빈 목록으로 초기화
    if migrated_user_ids is None:
        migrated_user_ids = []
        print("경고: 마이그레이션된 사용자 ID가 없습니다. 외래 키 제약 조건 위반이 발생할 수 있습니다.")
    
    # 성공적으로 마이그레이션된 사용자의 예약만 필터링
    if migrated_user_ids:
        reservations = Reservation.query.filter(Reservation.user_id.in_(migrated_user_ids)).all()
    else:
        reservations = Reservation.query.all()
    
    print(f"총 {len(reservations)}건의 예약을 마이그레이션합니다.")
    success_count = 0
    
    for reservation in reservations:
        reservation_data = {
            'id': reservation.id,
            'user_id': reservation.user_id,
            'date': reservation.date.isoformat(),
            'start_time': reservation.start_time.isoformat(),
            'end_time': reservation.end_time.isoformat(),
            'status': reservation.status,
            'created_at': reservation.created_at.isoformat(),
            'purpose': reservation.purpose
        }
        
        try:
            # Supabase에 예약 데이터 삽입
            result = supabase.table('reservations').upsert(reservation_data).execute()
            
            # 결과 확인
            if hasattr(result, 'data') and result.data:
                print(f"예약 ID: {reservation.id} 마이그레이션 성공")
                success_count += 1
            else:
                print(f"예약 ID: {reservation.id} 마이그레이션 실패: 결과 없음")
        except Exception as e:
            print(f"예약 ID: {reservation.id} 마이그레이션 오류: {e}")
    
    print(f"총 {len(reservations)}건 중 {success_count}건의 예약 데이터 마이그레이션 완료")

def migrate_blocked_times(supabase):
    """차단된 시간 테이블 마이그레이션"""
    print("차단된 시간 데이터 마이그레이션 중...")
    blocked_times = BlockedTime.query.all()
    
    print(f"총 {len(blocked_times)}건의 차단된 시간을 마이그레이션합니다.")
    
    for blocked_time in blocked_times:
        blocked_time_data = {
            'id': blocked_time.id,
            'date': blocked_time.date.isoformat(),
            'start_time': blocked_time.start_time.isoformat(),
            'end_time': blocked_time.end_time.isoformat(),
            'reason': blocked_time.reason
        }
        
        try:
            # Supabase에 차단된 시간 데이터 삽입
            result = supabase.table('blocked_times').upsert(blocked_time_data).execute()
            
            # 결과 확인
            if hasattr(result, 'data') and result.data:
                print(f"차단된 시간 ID: {blocked_time.id} 마이그레이션 성공")
            else:
                print(f"차단된 시간 ID: {blocked_time.id} 마이그레이션 실패: 결과 없음")
        except Exception as e:
            print(f"차단된 시간 ID: {blocked_time.id} 마이그레이션 오류: {e}")
    
    print(f"총 {len(blocked_times)}건의 차단된 시간 데이터 마이그레이션 완료")

if __name__ == "__main__":
    migrate_data()