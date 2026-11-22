# Imagen base oficial de Python ligera para produccion
FROM python:3.11-slim

# Evita que Python almacene archivos de cache .pyc y fuerza salida de consola en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalacion de dependencias del sistema requeridas para compilacion
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copia e instalacion de librerias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia del codigo fuente del backend al contenedor
COPY . .

# Puerto expuesto por el servidor Flask
EXPOSE 5000

# Comando de arranque del servidor API REST
CMD ["python", "app.py"]
