from .base import *

# Propósito: La clave MÁS IMPORTANTE para producción detrás de un proxy.
# Tu Nginx está configurado para pasar la IP real en la cabecera X-Real-IP.
# Django la recibe como 'HTTP_X_REAL_IP' en el objeto META.
# Esto asegura que el límite se aplique al usuario final, no al proxy de Nginx.
RATELIMIT_IP_META_KEY = "HTTP_X_REAL_IP"

# --- CONFIGURACIÓN DE COOKIES SEGURAS PARA PRODUCCIÓN ---

# --- CONFIGURACIONES SEGURAS PARA TODOS LOS ENTORNOS ---
# Estas opciones se pueden activar de forma segura, ya que no dependen de HTTPS.

# Impide que el navegador intente "adivinar" el tipo de contenido de un recurso si el servidor no lo especifica claramente.
SECURE_CONTENT_TYPE_NOSNIFF = True

# Activa el filtro de XSS integrado en algunos navegadores más antiguos.
SECURE_BROWSER_XSS_FILTER = True

# Protección crítica contra XSS. Impide que cualquier script de JavaScript en el navegador acceda a la cookie de sesión. Si un atacante lograra inyectar un script, no podría robar la sesión del usuario.
SESSION_COOKIE_HTTPONLY = True

# Restringe el envío de la cookie a peticiones del mismo sitio (protección CSRF).
# 'Strict' es la opción más segura contra ataques CSRF.
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Le dice a Django que confíe en la cabecera X-Forwarded-Proto enviada por nuestro Nginx.
# ¡CRÍTICO para que las comprobaciones de 'is_secure()' funcionen!
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Le dice a Django que construya URLs usando la cabecera X-Forwarded-Host.
USE_X_FORWARDED_HOST = True


# --- CONFIGURACIONES SOLO PARA PRODUCCIÓN REAL CON HTTPS ---
# ADVERTENCIA: NO DESCOMENTE estas líneas hasta que su sitio esté funcionando
# correctamente detrás de Nginx con un certificado SSL/TLS válido.
# Descomentarlas en un entorno HTTP romperá su sitio.

# Redirige todo el tráfico HTTP a HTTPS.
# SECURE_SSL_REDIRECT = True

# Solo permite enviar la cookie de sesión a través de conexiones HTTPS.
# SESSION_COOKIE_SECURE = True

# Solo permite enviar la cookie CSRF a través de conexiones HTTPS.
# CSRF_COOKIE_SECURE = True

# SECURE_HSTS_SECONDS = 31536000

# SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# SECURE_HSTS_PRELOAD = True
