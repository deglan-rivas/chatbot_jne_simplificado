# Imagen base oficial de Ubuntu 22.04
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
    && rm /tmp/instantclient-basic-linux.x64-23.8.0.25.04.zip \
    && ln -s /opt/oracle/libclntsh.so.21.1 /opt/oracle/libclntsh.so

RUN echo /opt/oracle/instantclient_23_8 > /etc/ld.so.conf.d/oracle-instantclient.conf \
    && ldconfig

# Configurar variables de entorno
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_23_8:$LD_LIBRARY_PATH
ENV PATH=/opt/oracle/instantclient_23_8:$PATH
ENV UV_PROJECT_ENVIRONMENT=.venv


# Instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install uv

# Copiar el archivo requirements.txt al directorio de trabajo
COPY pyproject.toml .
COPY uv.lock .

# Instalar las dependencias de Python
RUN uv venv
RUN uv sync

# Copiar el resto del código al directorio de trabajo
COPY . .

# Exponer el puerto 8001
EXPOSE 8001

ENV PYTHONUNBUFFERED=1

# Ejecutar la aplicación

CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]


# CMD ["tail", "-f", "/dev/null"]