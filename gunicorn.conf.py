# Gunicorn uad6cuc131 ud30cuc77c

import multiprocessing

# ucd5cuc801ud654ub41c uc124uc815
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 5
bind = "0.0.0.0:$PORT"
worker_class = "sync"
loglevel = "info"
