# ===================================================================================================
# DockerGuard v4.4 - Dockerfile de Desarrollo Fusionado y Endurecido
# Propósito: Integrar el flujo de trabajo de desarrollo existente con el principio de seguridad
#            de ejecución como usuario no-root. ESTA ES LA VERSIÓN FINAL RECOMENDADA.
# ===================================================================================================

# Se respeta la elección de imagen base Debian "Bullseye" por su compatibilidad de herramientas.
FROM python:3.13-bullseye

# --- ARGUMENTOS DE BUILD ---
# Permite pasar UIDs/GIDs desde el exterior para evitar problemas de permisos con volúmenes.
ARG UID=1000
ARG GID=1000

# Se mantienen las variables de entorno estándar para la optimización de Python.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- CREACIÓN DE USUARIO SIN PRIVILEGIOS (Principio de Seguridad como Fundamento) ---
# Se ejecuta temprano en el build. Es el pilar de la seguridad del contenedor.
RUN groupadd -g ${GID} -o appgroup && \
    useradd -m -u ${UID} -g appgroup -s /bin/sh appuser

# --- INSTALACIÓN DE DEPENDENCIAS DEL SISTEMA (FUSIÓN) ---
# Se combinan las dependencias del usuario (herramientas) y las de compilación (build-essentials).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gettext \
        postgresql-client \
        redis-tools \
        git \
        gcc \
        libpq-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# --- INSTALACIÓN DE HERRAMIENTAS DE PYTHON (FLUJO DE TRABAJO PRESERVADO) ---
# Se mantiene la instalación de pip-tools y djlint como fue especificado.
RUN pip install --no-cache-dir pip-tools==7.4.1 && \
    pip install --no-cache-dir -U djlint

# --- CONFIGURACIÓN DEL WORKDIR (FLUJO DE TRABAJO PRESERVADO) ---
WORKDIR /workspaces/backend

# --- GESTIÓN DE DEPENDENCIAS DE PYTHON (FLUJO DE TRABAJO PRESERVADO) ---
# Se copia la definición de dependencias.
COPY backend/requirements/ ./requirements/

# Se compilan y se instalan las dependencias usando el método de pip-tools.
# Esta lógica se mantiene intacta para no alterar el flujo de desarrollo.
RUN pip-compile requirements/base.in -o requirements/base.txt && \
    pip-compile requirements/development.in -o requirements/development.txt && \
    pip install --no-cache-dir -r requirements/development.txt

# --- COPIA DEL CÓDIGO FUENTE (BUENA PRÁCTICA) ---
# Aunque el volumen montado en desarrollo sobreescribirá esto, hace que la imagen
# sea auto-contenida y funcional por sí misma. Se asigna propiedad al usuario no-root.
COPY --chown=appuser:appgroup ./backend .

# --- CAÍDA DE PRIVILEGIOS (PASO FINAL DE SEGURIDAD) ---
# A partir de este punto, el contenedor se ejecutará como 'appuser'.
# Esto resuelve la advertencia de Celery y aplica el Principio de Mínimo Privilegio.
USER appuser

# El 'command' del docker-compose.yml (ej: 'sleep infinity') se ejecutará bajo este usuario.