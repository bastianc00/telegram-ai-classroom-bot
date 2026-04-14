"""
Gunicorn configuration for production
Optimizado para prevenir bloqueo del backend durante generación de IA
"""
import os

# Server socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = 4  # Reducido para evitar sobrecarga de CPU y RAM
worker_class = 'sync'  # Sync workers - más estable para SocketIO
threads = 6  # 6 threads: 3 para IA, 3 para requests normales/control
worker_connections = 1000
timeout = 120  # 2 minutos para procesos AI largos
graceful_timeout = 50  # 50 segundos para terminar gracefully
keepalive = 5

# Worker lifecycle - Balanceado: prevenir memory leaks sin romper WebSockets
max_requests = 400  # Reiniciar workers cada 200 requests (balance entre estabilidad y uptime)
max_requests_jitter = 40  # Randomness para evitar restarts simultáneos
worker_tmp_dir = '/dev/shm'  # Usar RAM para temp files (más rápido y menos I/O)

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'pds_backend'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = None
certfile = None
