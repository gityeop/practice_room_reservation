import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Supabase 클라이언트 생성 함수
def get_supabase_client() -> Client:
    """Supabase 클라이언트 인스턴스를 반환합니다."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL 또는 SUPABASE_KEY가 환경 변수에 설정되지 않았습니다.")
    
    return create_client(url, key)

# 서비스 키를 사용하는 Supabase 클라이언트 생성 함수 (관리자 작업용)
def get_supabase_admin_client() -> Client:
    """관리자 권한을 가진 Supabase 클라이언트 인스턴스를 반환합니다."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL 또는 SUPABASE_SERVICE_KEY가 환경 변수에 설정되지 않았습니다.")
    
    return create_client(url, key)