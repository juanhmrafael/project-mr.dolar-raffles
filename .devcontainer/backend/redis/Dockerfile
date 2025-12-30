# =======================================================================================
# DockerGuard v4.2 - Dockerfile para Imagen de Redis de Producción
# Propósito: Construir una imagen de Redis que incluya las herramientas de cliente
#            necesarias para un healthcheck robusto, manteniendo una base mínima.
# Fuente Canónica de APK: https://wiki.alpinelinux.org/wiki/Alpine_Linux_package_management
# =======================================================================================

# Usamos la misma base oficial, específica y segura.
FROM redis:7-alpine

# Principio de Provisión Explícita:
# Se instala el paquete 'redis', que en Alpine Linux incluye tanto el servidor
# como las herramientas de cliente (redis-cli). Esto resuelve la dependencia del healthcheck.
# '--no-cache' asegura que no se guarde el índice de paquetes, manteniendo la imagen pequeña.
RUN apk add --no-cache redis