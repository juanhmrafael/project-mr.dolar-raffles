# Dockerfile de Desarrollo para el Backend (Django)
# =======================================================================================
# Propósito: Construir una imagen de Docker autocontenida y rica en herramientas,
# diseñada específicamente para el desarrollo de la aplicación Django. Esta imagen
# servirá como el entorno de ejecución para el Dev Container de VS Code.
# =======================================================================================

# Propósito: Especificar la imagen base sobre la cual construiremos nuestro entorno.
# 'python:3.13-bullseye' nos proporciona una base de Debian 11 ("Bullseye") con Python 3.13
# ya instalado. Se elige Debian sobre Alpine por su amplia compatibilidad con
# herramientas de desarrollo y extensiones de VS Code precompiladas.
FROM python:3.13-bullseye

# Propósito: Configurar variables de entorno estándar para optimizar la ejecución de Python.
# - PYTHONDONTWRITEBYTECODE=1: Evita que Python genere archivos .pyc, manteniendo el
#   directorio del proyecto limpio.
# - PYTHONUNBUFFERED=1: Asegura que la salida de Python se envíe directamente a la
#   terminal sin ser almacenada en un búfer, lo cual es crucial para ver los logs en tiempo real.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Propósito: Instalar las dependencias a nivel del sistema operativo.
# Se usa 'apt-get' (el gestor de paquetes de Debian) para añadir herramientas esenciales.
# - postgresql-client: Proporciona el comando 'psql', permitiendo la conexión manual
#   a la base de datos desde la terminal del contenedor para depuración.
# - redis-tools: Proporciona el comando 'redis-cli', útil para inspeccionar la
#   caché o el broker de mensajes de Redis.
# - git: Esencial para que VS Code y sus extensiones (como GitLens) puedan interactuar
#   con el control de versiones directamente desde el entorno de desarrollo.
# '--no-install-recommends' evita instalar paquetes opcionales, manteniendo la imagen ligera.
# 'rm -rf /var/lib/apt/lists/*' limpia la caché de apt para optimizar el tamaño final de la imagen.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gettext \
        postgresql-client \
        redis-tools \
        git \
    && rm -rf /var/lib/apt/lists/*
# Propósito: Instalar 'pip-tools', una herramienta fundamental para una gestión de
# dependencias de Python robusta y reproducible. Se usará para compilar los archivos de requerimientos.
RUN pip install --no-cache-dir pip-tools==7.4.1 -U djlint

# Propósito: Establecer el directorio de trabajo por defecto dentro del contenedor.
# Todas las operaciones subsiguientes (como COPY y los comandos en la terminal) se
# ejecutarán desde esta ruta. Es la raíz de nuestro código de aplicación.
WORKDIR /workspaces/backend

# Propósito: Copiar los archivos de definición de dependencias desde el host local
# hacia el contenedor.
# - Origen ('backend/requirements/'): Es la ruta relativa al contexto de build (la raíz del proyecto).
# - Destino ('./requirements/'): Es la ruta relativa al WORKDIR actual, resultando en
#   '/workspaces/backend/requirements/'.
COPY backend/requirements/ ./requirements/

# Propósito: Compilar los archivos de requerimientos y luego instalar las dependencias.
# Este es un proceso de dos pasos para asegurar la consistencia.
# - 'pip-compile': Lee los archivos .in (donde defines tus dependencias directas) y
#   genera archivos .txt con todas las sub-dependencias fijadas a versiones específicas.
# - 'pip install -r ...': Instala todas las dependencias listadas en el archivo .txt,
#   asegurando que el entorno de desarrollo tenga todas las herramientas necesarias.
RUN pip-compile requirements/base.in -o requirements/base.txt && \
    pip-compile requirements/development.in -o requirements/development.txt && \
    pip install --no-cache-dir -r requirements/development.txt