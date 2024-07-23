"""Gunicorn *production* config file"""

import multiprocessing

# Django WSGI application path in pattern MODULE_NAME:VARIABLE_NAME
wsgi_app = "ARE2.asgi:application"
# The number of worker processes for handling requests
workers = multiprocessing.cpu_count() * 2 + 1
# The socket to bind
bind = "0.0.0.0:8000"
# Write access and error info to /var/log
accesslog = "/var/www/html/log/access.log"
errorlog = "/var/www/html/log/error.log"
# Redirect stdout/stderr to log file
capture_output = True
# PID file so you can easily fetch process ID
pidfile = "/var/www/html/run/prod.pid"
# Daemonize the Gunicorn process (detach & enter background)
daemon = True