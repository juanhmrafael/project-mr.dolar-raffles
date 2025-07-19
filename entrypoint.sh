#!/bin/sh
# entrypoint.sh para PRODUCCIÓN
# ====================================================================================================
# Propósito: Este script es el punto de entrada para los contenedores de Django (backend y worker).
# Se ejecuta como 'root' al inicio para realizar tareas de configuración privilegiadas y luego
# transfiere la ejecución a un usuario sin privilegios para una operación segura.
# ====================================================================================================

# --- Directiva de Seguridad: Salida Inmediata en Caso de Error ---
# Propósito: Asegurar que el script se detenga inmediatamente si cualquier comando falla.
# Funcionamiento: 'set -e' es una directiva del shell que causa que el script termine si un
# comando devuelve un código de salida distinto de cero (un error). Esto previene comportamientos
# inesperados, como intentar ejecutar migraciones si el paso anterior falló.
set -e

# --- Paso 1: Verificación de Dependencias (Defensa en Profundidad) ---
# Propósito: Asegurar que la base de datos esté aceptando conexiones antes de continuar.
# Funcionamiento: Aunque el 'healthcheck' de Docker Compose ya maneja esto, este bucle actúa
# como una capa adicional de resiliencia (defensa en profundidad). El comando 'nc' (netcat)
# sondea el host y puerto de la base de datos. El bucle 'while' no permitirá que el script
# continúe hasta que el sondeo sea exitoso. Las variables $DB_HOST y $DB_PORT son inyectadas
# desde el archivo .env.
echo "Entrypoint: Esperando a que PostgreSQL inicie..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Entrypoint: PostgreSQL iniciado correctamente."


# --- Paso 2: Despacho basado en el Rol ---
# Propósito: Leer el primer argumento pasado al script para determinar el rol.
# Si no se pasa ningún argumento, saldrá con un error para evitar un comportamiento indefinido.
role="$1"
if [ -z "$role" ]; then
    echo "Error: No se ha especificado un rol (web o worker)."
    exit 1
fi

# El comando 'shift' elimina el primer argumento ($1), de modo que "$@" ahora contiene
# solo los argumentos del comando principal (como gunicorn o celery).
shift


# --- Lógica para el Rol 'web' ---
if [ "$role" = "web" ]; then
    echo "Entrypoint: Rol 'web' detectado. Ejecutando tareas de despliegue..."

    # Propósito: Garantizar permisos en los volúmenes, solo para el rol 'web'.
    echo "Entrypoint: Estableciendo permisos de volúmenes..."
    if [ -d "/home/appuser/app/staticfiles" ]; then
        chown -R appuser:appuser /home/appuser/app/staticfiles
    fi
    if [ -d "/home/appuser/app/mediafiles" ]; then
        chown -R appuser:appuser /home/appuser/app/mediafiles
    fi
    echo "Entrypoint: Permisos establecidos."

    # Propósito: Ejecutar migraciones y recolectar estáticos, solo para el rol 'web'.
    echo "Entrypoint: Ejecutando migraciones de base de datos..."
    su-exec appuser python manage.py migrate --no-input

    echo "Entrypoint: Recolectando archivos estáticos..."
    su-exec appuser python manage.py collectstatic --no-input --clear

    echo "Entrypoint: Entregando control al servidor Gunicorn..."
    # 'exec' reemplaza el proceso del script con el de Gunicorn.
    exec su-exec appuser "$@"

# --- Lógica para el Rol 'worker' ---
elif [ "$role" = "worker" ]; then
    echo "Entrypoint: Rol 'worker' detectado. Iniciando trabajador de Celery..."
    # El worker no necesita 'chown' ni 'collectstatic'. Simplemente inicia Celery.
    # El comando de Celery se pasa a través de "$@".
    echo "Entrypoint: Entregando control al trabajador de Celery..."
    exec su-exec appuser "$@"
# --- Lógica para el Rol 'beat' ---
elif [ "$role" = "beat" ]; then
    echo "Entrypoint: Rol 'beat' detectado. Iniciando planificador de Celery..."
    # Eliminación segura del archivo pid para prevenir errores al reiniciar.
    rm -f /home/appuser/app/celerybeat.pid
    echo "Entrypoint: Entregando control a Celery Beat..."
    exec su-exec appuser "$@"
else
    echo "Error: Rol desconocido '$role'. Use 'web' o 'worker' o 'beat'."
    exit 1
fi