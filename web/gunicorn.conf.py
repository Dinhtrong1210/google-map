import os

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
timeout = 120
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "access.log")
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "error.log")
