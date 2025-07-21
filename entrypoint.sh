#!/bin/sh
# entrypoint.sh para PRODUCCIÓN (DockerGuard Standard v4.0 - Gestión de Secretos)
# ====================================================================================================
# Propósito: Este script es el punto de entrada para los contenedores de Django. Su rol principal
# es actuar como un puente seguro entre los Docker Secrets y la aplicación, además de orquestar
# las tareas de arranque (migraciones, etc.) y la caída de privilegios.
# ====================================================================================================

# --- Directiva de Seguridad: Salida Inmediata en Caso de Error ---
# 'set -e' asegura que el script falle inmediatamente si cualquier comando falla.
set -e

# --- PASO 1: CARGA Y EXPORTACIÓN SEGURA DE SECRETOS ---
# Propósito: Leer las credenciales desde los archivos montados por Docker en /run/secrets/
# y exportarlos como variables de entorno. Este es el único lugar donde los secretos
# se manejan. La aplicación Django los leerá desde el entorno sin saber su origen.
# Fuente Canónica: https://docs.docker.com/compose/use-secrets/
# ----------------------------------------------------------------------------------------------------
echo "Entrypoint: Cargando secretos en el entorno..."

# Verifica que el archivo del secreto exista antes de intentar leerlo.
# Si no existe, sale con un error claro. Esto previene fallos silenciosos.
if [ -f /run/secrets/postgres_user ]; then
    export POSTGRES_USER=$(cat /run/secrets/postgres_user)
else
    echo "Error: El secreto 'postgres_user' no se encontró." >&2
    exit 1
fi

if [ -f /run/secrets/postgres_password ]; then
    export POSTGRES_PASSWORD=$(cat /run/secrets/postgres_password)
else
    echo "Error: El secreto 'postgres_password' no se encontró." >&2
    exit 1
fi

if [ -f /run/secrets/postgres_db ]; then
    export POSTGRES_DB=$(cat /run/secrets/postgres_db)
else
    echo "Error: El secreto 'postgres_db' no se encontró." >&2
    exit 1
fi

if [ -f /run/secrets/redis_appuser_password ]; then
    export REDIS_PASSWORD=$(cat /run/secrets/redis_appuser_password)
else
    echo "Error: El secreto 'redis_appuser_password' no se encontró." >&2
    exit 1
fi

echo "Entrypoint: Secretos cargados correctamente."


# --- PASO 2: VERIFICACIÓN DE DEPENDENCIAS ---
# Propósito: Asegurar que la base de datos esté aceptando conexiones.
# Aunque Compose maneja esto con 'depends_on: service_healthy', esta es una
# capa adicional de resiliencia (defensa en profundidad).
# Las variables $DB_HOST y $DB_PORT son inyectadas como variables de entorno
# NO secretas desde el docker-compose.yml.
# ----------------------------------------------------------------------------------------------------
echo "Entrypoint: Esperando a que PostgreSQL inicie en $DB_HOST:$DB_PORT..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Entrypoint: PostgreSQL iniciado correctamente."


# --- PASO 3: DESPACHO BASADO EN EL ROL ---
# Propósito: Leer el primer argumento pasado al script ($1) para determinar el rol del contenedor.
# La lógica se mantiene, pero ahora opera en un entorno seguro con credenciales cargadas.
# ----------------------------------------------------------------------------------------------------
role="$1"
if [ -z "$role" ]; then
    echo "Error: No se ha especificado un rol (web, worker o beat)." >&2
    exit 1
fi
shift # Elimina el primer argumento, dejando los argumentos del comando principal en "$@".


# --- Lógica para el Rol 'web' ---
if [ "$role" = "web" ]; then
    echo "Entrypoint: Rol 'web' detectado. Ejecutando tareas de despliegue..."

    # Tarea de 'root': Garantizar permisos en los volúmenes montados.
    echo "Entrypoint: Estableciendo permisos de volúmenes..."
    chown -R appuser:appuser /home/appuser/app/staticfiles
    chown -R appuser:appuser /home/appuser/app/mediafiles
    echo "Entrypoint: Permisos establecidos."

    # Tareas de 'appuser': Ejecutar migraciones y recolectar estáticos.
    # 'su-exec' ejecuta un comando como un usuario específico.
    echo "Entrypoint: Ejecutando migraciones de base de datos..."
    su-exec appuser python manage.py migrate --no-input

    echo "Entrypoint: Recolectando archivos estáticos..."
    su-exec appuser python manage.py collectstatic --no-input --clear

    # Entrega final del control al proceso principal (Gunicorn).
    # 'exec' reemplaza el proceso del script, ahorrando recursos.
    echo "Entrypoint: Entregando control al servidor Gunicorn..."
    exec su-exec appuser "$@"

# --- Lógica para Roles 'worker' y 'beat' ---
elif [ "$role" = "worker" ] || [ "$role" = "beat" ]; then
    echo "Entrypoint: Rol '$role' detectado. Iniciando proceso de Celery..."
    # El worker y el beat no necesitan gestionar volúmenes ni estáticos.

    # Lógica específica para 'beat': eliminar el archivo PID si existe.
    if [ "$role" = "beat" ]; then
        rm -f /home/appuser/app/celerybeat.pid
    fi

    echo "Entrypoint: Entregando control a Celery..."
    exec su-exec appuser "$@"
else
    echo "Error: Rol desconocido '$role'. Use 'web', 'worker' o 'beat'." >&2
    exit 1
fi