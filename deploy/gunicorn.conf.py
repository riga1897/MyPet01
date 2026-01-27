"""Gunicorn configuration for production deployment."""
import multiprocessing
import os

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

errorlog = "/var/log/mypet/gunicorn-error.log"
accesslog = "/var/log/mypet/gunicorn-access.log"
loglevel = "info"

capture_output = True
enable_stdio_inheritance = True

proc_name = "mypet"

max_requests = 1000
max_requests_jitter = 50

preload_app = True

daemon = False

user = os.environ.get("MYPET_USER", "www-data")
group = os.environ.get("MYPET_GROUP", "www-data")

tmp_upload_dir = "/tmp/mypet-uploads"

forwarded_allow_ips = "*"
secure_scheme_headers = {
    "X-FORWARDED-PROTOCOL": "ssl",
    "X-FORWARDED-PROTO": "https",
    "X-FORWARDED-SSL": "on",
}
