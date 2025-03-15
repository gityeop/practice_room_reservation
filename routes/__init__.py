# routes 패키지 초기화 파일

# 이 파일은 routes 패키지를 초기화하고 필요한 블루프린트를 가져옵니다.
# 각 블루프린트는 app.py에서 직접 등록되므로 여기서는 추가 작업이 필요하지 않습니다.

# 이 파일이 비어 있어도 Python은 이 디렉토리를 패키지로 인식합니다.
# 필요한 경우 공통 유틸리티 함수나 상수를 여기에 정의할 수 있습니다.

from datetime import datetime, time

# 시간 형식 변환 유틸리티 함수
def format_time(time_obj):
    """Time 객체를 HH:MM 형식의 문자열로 변환합니다."""
    if isinstance(time_obj, time):
        return time_obj.strftime("%H:%M")
    return time_obj

def parse_time(time_str):
    """HH:MM 형식의 문자열을 Time 객체로 변환합니다."""
    if time_str and isinstance(time_str, str):
        return datetime.strptime(time_str, "%H:%M").time()
    return time_str

# 날짜 형식 변환 유틸리티 함수
def format_date(date_obj):
    """Date 객체를 YYYY-MM-DD 형식의 문자열로 변환합니다."""
    if date_obj:
        return date_obj.strftime("%Y-%m-%d")
    return ""

def parse_date(date_str):
    """YYYY-MM-DD 형식의 문자열을 Date 객체로 변환합니다."""
    if date_str and isinstance(date_str, str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    return None