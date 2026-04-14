FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libreoffice \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p static/uploads static/presentations

# Exponer puerto
EXPOSE 5000

# Comando para ejecutar la aplicación con Gunicorn en producción
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
