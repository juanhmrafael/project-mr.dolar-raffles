#!/bin/sh
# entrypoint.sh para PRODUCCIÓN (DockerGuard Standard v4.1 - Carga de Configuración y Secretos)
# ====================================================================================================
# Propósito: Este script es el punto de entrada para los contenedores de Django.
# 1. Carga la configuración NO secreta desde el archivo .env.
# 2. Carga las credenciales y claves desde Docker Secrets.
# 3. Verifica la disponibilidad de los servicios dependientes.
# 4. Ejecuta tareas de despliegue (migraciones, etc.) según el rol.
# 5. Entrega el control al proceso principal de la aplicación con privilegios reducidos.
# ====================================================================================================

# --- DIRECTIVA DE SEGURIDAD: FALLO RÁPIDO ---
# 'set -e' asegura que el script falle inmediatamente si cualquier comando falla.
set -e

# --- PASO 1: CARGA DE CONFIGURACIÓN DESDE .env ---
# Propósito: Cargar las variables de configuración no secretas (DJANGO_SETTINGS_MODULE, etc.)
# para asegurar que la aplicación se inicie en el entorno correcto (producción).
# ---------------------------------------------------------------------------------------------
if [ -f .env ]; then
  echo "Entrypoint: Cargando configuración desde .env..."
  set -o allexport
  . ./.env
  set +o allexport
  echo "Entrypoint: Configuración cargada."
else
  echo "Advertencia: Archivo .env no encontrado. Se continuará con las variables de entorno existentes."
fi


# --- PASO 2: CARGA Y EXPORTACIÓN SEGURA DE SECRETOS ---
# Propósito: Leer las credenciales desde los archivos montados por Docker en /run/secrets/
# y exportarlos como variables de entorno para que la aplicación Django los consuma.
# ----------------------------------------------------------------------------------------------------
echo "Entrypoint: Cargando secretos en el entorno..."

# Función auxiliar para cargar un secreto y exportarlo como variable de entorno
load_secret() {
  local secret_name="$1"
  local env_var_name="$2"
  local secret_path="/run/secrets/${secret_name}"

  if [ -f "${secret_path}" ]; then
    export "${env_var_name}"="$(cat "${secret_path}")"
  else
    echo "Error: El secreto '${secret_name}' no se encontró en '${secret_path}'." >&2
    exit 1
  fi
}

# Cargar todos los secretos requeridos por la aplicación
load_secret "django_secret_key" "SECRET_KEY"
load_secret "postgres_user" "POSTGRES_USER"
load_secret "postgres_password" "POSTGRES_PASSWORD"
load_secret "postgres_db" "POSTGRES_DB"
load_secret "redis_appuser_password" "REDIS_PASSWORD"
load_secret "field_encryption_key" "FIELD_ENCRYPTION_KEY"

# Asegurar compatibilidad con la configuración de Django (DB_NAME, DB_USER, etc.)
export DB_NAME="$POSTGRES_DB"
export DB_USER="$POSTGRES_USER"
export DB_PASSWORD="$POSTGRES_PASSWORD"

echo "Entrypoint: Secretos cargados correctamente."


# --- PASO 3: VERIFICACIÓN DE DEPENDENCIAS ---
# Propósito: Asegurar que la base de datos esté aceptando conexiones.
# ----------------------------------------------------------------------------------------------------
echo "Entrypoint: Esperando a que PostgreSQL inicie en $DB_HOST:$DB_PORT..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Entrypoint: PostgreSQL iniciado correctamente."

# --- PASO 4: VERIFICACIÓN DE DEPENDENCIAS (REDIS) ---
# Propósito: Asegurar que Redis esté aceptando conexiones.
# ----------------------------------------------------------------------------------------------------
echo "Entrypoint: Esperando a que Redis inicie en $REDIS_HOST:$REDIS_PORT..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 0.1
done
echo "Entrypoint: Redis iniciado correctamente."


# --- PASO 4: DESPACHO BASADO EN EL ROL ---
# Propósito: Ejecutar lógicas diferentes según el rol del contenedor (web, worker, beat).
# ----------------------------------------------------------------------------------------------------
role="$1"
if [ -z "$role" ]; then
    echo "Error: No se ha especificado un rol (web, worker o beat)." >&2
    exit 1
fi
shift # Elimina el rol de la lista de argumentos, dejando solo el comando principal.


# --- Lógica para el Rol 'web' ---
if [ "$role" = "web" ]; then
    echo "Entrypoint: Rol 'web' detectado. Ejecutando tareas de despliegue..."

    # Tarea de 'root': Garantizar permisos en los volúmenes.
    echo "Entrypoint: Estableciendo permisos de volúmenes..."
    chown -R appuser:appuser /home/appuser/app/staticfiles
    chown -R appuser:appuser /home/appuser/app/mediafiles
    echo "Entrypoint: Permisos establecidos."

    # Tareas de 'appuser': Migraciones y recolección de estáticos.
    echo "Entrypoint: Ejecutando migraciones de base de datos..."
    su-exec appuser python manage.py migrate --no-input

    echo "Entrypoint: Recolectando archivos estáticos..."
    su-exec appuser python manage.py collectstatic --no-input --clear

    # Entrega final del control al proceso principal (Gunicorn).
    echo "Entrypoint: Entregando control al servidor Gunicorn..."
    exec su-exec appuser "$@"

# --- Lógica para Roles 'worker' y 'beat' ---
elif [ "$role" = "worker" ] || [ "$role" = "beat" ]; then
    echo "Entrypoint: Rol '$role' detectado. Iniciando proceso de Celery..."
    
    if [ "$role" = "beat" ]; then
        rm -f /home/appuser/app/celerybeat.pid
    fi

    echo "Entrypoint: Entregando control a Celery..."
    exec su-exec appuser "$@"
else
    echo "Error: Rol desconocido '$role'. Use 'web', 'worker' o 'beat'." >&2
    exit 1
fi