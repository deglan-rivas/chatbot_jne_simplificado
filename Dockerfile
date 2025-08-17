# Imagen base oficial de Python 3.11
FROM python:3.11.12

# Establecer el directorio de trabajo
WORKDIR /app

# Instala herramientas necesarias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libaio1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnotify-dev \
    libnss3 \
    libxss1 \
    libasound2 \
    wget \
    unzip \
    git \
    curl \
    make \
    locales \
     vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the locale
RUN sed -i '/es_ES.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG es_ES.UTF-8
ENV LANGUAGE es_ES:es
ENV LC_ALL es_ES.UTF-8

# Descargar e instalar Oracle Instant Client
RUN wget https://download.oracle.com/otn_software/linux/instantclient/2380000/instantclient-basic-linux.x64-23.8.0.25.04.zip -P /tmp/ \
    && unzip /tmp/instantclient-basic-linux.x64-23.8.0.25.04.zip -d /opt/oracle/ \
    && rm /tmp/instantclient-basic-linux.x64-23.8.0.25.04.zip

# Corregir el enlace simbólico y configuración de Oracle
RUN cd /opt/oracle/instantclient_23_8 && \
    ln -sf libclntsh.so.23.1 libclntsh.so && \
    echo /opt/oracle/instantclient_23_8 > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

# Configurar variables de entorno
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_23_8:$LD_LIBRARY_PATH
ENV PATH=/opt/oracle/instantclient_23_8:$PATH
ENV PYTHONUNBUFFERED=1

# Instalar uv
RUN pip install --upgrade pip && \
    pip install uv

# Copiar archivos de configuración de dependencias
COPY pyproject.toml uv.lock ./

# Método alternativo: usar uv para instalar directamente
RUN uv pip install --system -r pyproject.toml || \
    (uv venv /app/venv && \
     uv pip install --python /app/venv/bin/python -r pyproject.toml)

# Si el método anterior falla, usar pip tradicional
RUN if [ ! -f /usr/local/bin/uvicorn ]; then \
        pip install uvicorn fastapi; \
    fi

# Copiar el resto del código al directorio de trabajo
COPY . .

# Crear script de inicio
RUN echo '#!/bin/bash\n\
# Intentar encontrar uvicorn en diferentes ubicaciones\n\
if [ -f /app/venv/bin/uvicorn ]; then\n\
    exec /app/venv/bin/uvicorn chatbot.main:app --host 0.0.0.0 --port 8001 --reload\n\
elif [ -f /usr/local/bin/uvicorn ]; then\n\
    exec /usr/local/bin/uvicorn chatbot.main:app --host 0.0.0.0 --port 8001 --reload\n\
else\n\
    exec python -m uvicorn chatbot.main:app --host 0.0.0.0 --port 8001 --reload\n\
fi' > /app/start.sh && \
    chmod +x /app/start.sh

# Exponer el puerto 8001
EXPOSE 8001

# Comando por defecto
CMD ["/app/start.sh"]