proc_name = 'gunicorn.pid'
bind = "0.0.0.0:80"
backlog = 2048
timeout = 30
#worker_class = 'gevent'
worker_connections = 1000

# 启动的进程数
workers = 1
threads = 1
daemon = False

# debug = True
loglevel = 'debug'
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
accesslog = "logs/web_access.log"
errorlog = "logs/web_err.log"

x_forwarded_for_header = 'X-FORWARDED-FOR'
