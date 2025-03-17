# Gunicorn 구성 파일

import multiprocessing

# 최적화된 설정
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 5
bind = "0.0.0.0:$PORT"
worker_class = "sync"
loglevel = "info"

# 정적 파일 설정
raw_env = [
    "STATIC_ROOT=/app/static",
    "STATIC_URL=/static/"
]

# 파비콘 처리를 위한 추가 헤더
forwarded_allow_ips = "*"
secure_scheme_headers = {
    'X-Forwarded-Proto': 'https'
}
