from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from models import User, Reservation, BlockedTime
from db_utils import get_supabase_client
import uuid
import random
import time

class SupabaseRepository:
    """Supabase에 접근하기 위한 리포지토리 클래스"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    # User 관련 메서드
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """ID로 사용자 조회"""
        response = self.supabase.table('users').select('*').eq('id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    def get_user_by_student_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """학번으로 사용자 조회"""
        response = self.supabase.table('users').select('*').eq('student_id', student_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰으로 사용자 조회"""
        response = self.supabase.table('users').select('*').eq('token', token).execute()
        
        if response.data and len(response.data) > 0:
            user_data = response.data[0]
            # 토큰 유효성 검사
            if user_data.get('token_expiration'):
                expiration = datetime.fromisoformat(user_data['token_expiration'])
                if expiration < datetime.utcnow():
                    return None
            return user_data
        return None
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 사용자 생성"""
        response = self.supabase.table('users').insert(user_data).execute()
        return response.data[0] if response.data else None
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 정보 업데이트"""
        response = self.supabase.table('users').update(user_data).eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    # Reservation 관련 메서드
    def get_reservation_by_id(self, reservation_id: int) -> Optional[Dict[str, Any]]:
        """ID로 예약 조회"""
        response = self.supabase.table('reservations').select('*').eq('id', reservation_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    def get_user_reservations(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 모든 예약 조회"""
        response = self.supabase.table('reservations').select('*').eq('user_id', user_id).execute()
        return response.data if response.data else []
    
    def get_date_reservations(self, date: str) -> List[Dict[str, Any]]:
        """특정 날짜의 모든 예약 조회"""
        response = self.supabase.table('reservations').select('*').eq('date', date).execute()
        return response.data if response.data else []
    
    def get_overlapping_reservations(self, date: str, start_time: str, end_time: str, 
                               status_list=['pending', 'approved']) -> List[Dict[str, Any]]:
        """지정된 날짜와 시간에 겹치는 예약을 확인"""
        # 해당 날짜의 모든 예약을 조회합니다
        date_reservations = self.get_date_reservations(date)
        overlapping = []
        
        for reservation in date_reservations:
            # 상태 확인 (승인 대기 중 또는 승인된 예약만 고려)
            if reservation.get('status') in status_list:
                res_start = reservation.get('start_time')
                res_end = reservation.get('end_time')
                
                # 시간 겹침 체크 로직
                # 1. 새 예약이 기존 예약 시간 내에 있는 경우
                # 2. 기존 예약이 새 예약 시간 내에 있는 경우
                # 3. 새 예약이 기존 예약과 일부 겹치는 경우
                if ((start_time >= res_start and start_time < res_end) or
                    (end_time > res_start and end_time <= res_end) or
                    (start_time <= res_start and end_time >= res_end)):
                    overlapping.append(reservation)
        
        return overlapping
    
    def get_overlapping_blocked_times(self, date: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """지정된 날짜와 시간에 겹치는 차단된 시간을 확인"""
        # 해당 날짜의 모든 차단된 시간을 조회합니다
        date_blocked_times = self.get_date_blocked_times(date)
        overlapping = []
        
        for blocked_time in date_blocked_times:
            block_start = blocked_time.get('start_time')
            block_end = blocked_time.get('end_time')
            
            # 시간 겹침 체크 로직
            # 1. 새 예약이 차단된 시간 내에 있는 경우
            # 2. 차단된 시간이 새 예약 시간 내에 있는 경우
            # 3. 새 예약이 차단된 시간과 일부 겹치는 경우
            if ((start_time >= block_start and start_time < block_end) or
                (end_time > block_start and end_time <= block_end) or
                (start_time <= block_start and end_time >= block_end)):
                overlapping.append(blocked_time)
        
        return overlapping
    
    def get_all_reservations(self, status_list=None) -> List[Dict[str, Any]]:
        """ubaa8ub4e0 uc608uc57d uc870ud68c ub610ub294 uc0c1ud0dcuac00 uc8fcuc5b4uc9c4 uc608uc57duc744 uc870ud68c"""
        # uc0acuc6a9uc790 uc815ubcf4ub97c ud3ecud568ud558ub294 ucffc ub9ac uc0dduc131
        query = self.supabase.table('reservations')\
            .select(
                '*,'
                'users!inner(id, name, student_id, department)'
            )
        
        if status_list:
            # status uac00 uc8fcuc5b4uc9c4 ubaa9ub85d uc911 ud558ub098uc640 uc77cuce58ud558ub294 ubaa8ub4e0 uc608uc57d ubc18ud658
            query = query.in_('status', status_list)
        
        # uc704uc5d0uc11c uc0dduc131ub41c uc870uac74uc744 uc801uc6a9ud558uc5ec uccfcub9ac
        response = query.execute()
        
        # uc751ub2f5uc744 ubc1buc558uc744 ub54c uc0acuc6a9uc790 uc815ubcf4ub97c uc608uc57d ub370uc774ud130uc5d0 uc801uc6a9
        result = []
        for res in response.data:
            if 'users' in res and res['users']:
                user_data = res['users']
                res['user_name'] = user_data.get('name', '')
                res['user_student_id'] = user_data.get('student_id', '')
                res['user_department'] = user_data.get('department', '')
            del res['users']  # uc911ubcf5 ub370uc774ud130 uc81cuc678
            result.append(res)
            
        return result if result else []
    
    def get_reservations_by_date_range(self, start_date: str, end_date: str, status_filter: str = 'all') -> List[Dict[str, Any]]:
        """uc9c0uc815ub41c ub0a0uc9dc ubc94uc704uc640 uc0c1ud0dcuc5d0 ub530ub978 uc608uc57d uc870ud68c
        
        Args:
            start_date: uc2dcuc791 ub0a0uc9dc (YYYY-MM-DD ud615uc2dd)
            end_date: uc885ub8cc ub0a0uc9dc (YYYY-MM-DD ud615uc2dd)
            status_filter: uc608uc57d uc0c1ud0dc ud544ud130 ('all', 'pending', 'approved', 'rejected', 'canceled')
            
        Returns:
            ub0a0uc9dc ubc94uc704uc640 uc0c1ud0dcuc5d0 ud574ub2f9ud558ub294 uc608uc57d ubaa9ub85d
        """
        # uc0acuc6a9uc790 uc815ubcf4ub97c ud3ecud568ud558ub294 ucffc ub9ac uc0dduc131
        query = self.supabase.table('reservations')\
            .select(
                '*,'
                'users!inner(id, name, student_id, department)'
            )
        
        # ub0a0uc9dc ubc94uc704 ud544ud130 ucd94uac00
        query = query.gte('date', start_date).lte('date', end_date)
        
        # uc0c1ud0dc ud544ud130 ucd94uac00 (ud544ud130uac00 'all'uc774 uc544ub2cc uacbduc6b0uc5d0ub9cc)
        if status_filter and status_filter != 'all':
            query = query.eq('status', status_filter)
        
        # uc608uc57d ub0a0uc9dc uc21c uc815ub82c
        query = query.order('date', desc=False)
        
        # uc2e4ud589 ubc0f uacb0uacfc ubc18ud658
        response = query.execute()
        
        # uc751ub2f5uc744 ubc1buc558uc744 ub54c uc0acuc6a9uc790 uc815ubcf4ub97c uc608uc57d ub370uc774ud130uc5d0 uc801uc6a9
        result = []
        for res in response.data:
            if 'users' in res and res['users']:
                user_data = res['users']
                res['user_name'] = user_data.get('name', '')
                res['user_student_id'] = user_data.get('student_id', '')
                res['user_department'] = user_data.get('department', '')
            del res['users']  # uc911ubcf5 ub370uc774ud130 uc81cuc678
            result.append(res)
            
        return result if result else []
    
    def create_reservation(self, reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 예약 생성"""
        # ID가 없는 경우 현재 시간 기반 유니크 ID 생성
        if 'id' not in reservation_data:
            # 현재 시간 정수값을 ID로 사용
            import time
            reservation_data['id'] = int(time.time() * 1000)  # 밀리초 단위 타임스탬프
        
        response = self.supabase.table('reservations').insert(reservation_data).execute()
        return response.data[0] if response.data else None
    
    def update_reservation(self, reservation_id: int, reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """예약 정보 업데이트"""
        response = self.supabase.table('reservations').update(reservation_data).eq('id', reservation_id).execute()
        return response.data[0] if response.data else None
    
    def delete_reservation(self, reservation_id: int) -> bool:
        """예약 삭제"""
        response = self.supabase.table('reservations').delete().eq('id', reservation_id).execute()
        return len(response.data) > 0 if response.data else False
    
    # BlockedTime 관련 메서드
    def get_blocked_time_by_id(self, blocked_time_id: int) -> Optional[Dict[str, Any]]:
        """ID로 차단된 시간 조회"""
        response = self.supabase.table('blocked_times').select('*').eq('id', blocked_time_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    def get_date_blocked_times(self, date: str) -> List[Dict[str, Any]]:
        """특정 날짜의 모든 차단된 시간 조회"""
        response = self.supabase.table('blocked_times').select('*').eq('date', date).execute()
        return response.data if response.data else []
    
    def get_all_blocked_times(self) -> List[Dict[str, Any]]:
        """모든 차단된 시간 조회"""
        response = self.supabase.table('blocked_times').select('*').execute()
        return response.data if response.data else []
    
    def create_blocked_time(self, blocked_time_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 차단된 시간 생성"""
        # ID 생성 (Unix 시간 + 랜덤 숫자)
        current_time = int(time.time() * 1000)  # 밀리초 단위 타임스탬프
        random_number = random.randint(1000, 9999)
        blocked_time_data['id'] = current_time * 10000 + random_number
        
        try:
            response = self.supabase.table('blocked_times').insert(blocked_time_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating blocked time: {e}")
            return None
    
    def update_blocked_time(self, blocked_time_id: int, blocked_time_data: Dict[str, Any]) -> Dict[str, Any]:
        """차단된 시간 정보 업데이트"""
        response = self.supabase.table('blocked_times').update(blocked_time_data).eq('id', blocked_time_id).execute()
        return response.data[0] if response.data else None
    
    def delete_blocked_time(self, blocked_time_id: int) -> bool:
        """차단된 시간 삭제"""
        response = self.supabase.table('blocked_times').delete().eq('id', blocked_time_id).execute()
        return len(response.data) > 0 if response.data else False