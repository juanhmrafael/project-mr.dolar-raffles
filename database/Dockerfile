# =========================================================
# Dockerfile para la Imagen de PostgreSQL con Soporte de Locale en Alpine
# ========================================================================
# Propósito: Construir una imagen de PostgreSQL personalizada sobre Alpine
# que incluye soporte completo para locales glibc Y que aplica parches de
# seguridad críticos en tiempo de construcción.
# ========================================================================

# Usamos la imagen base oficial de PostgreSQL sobre Alpine.
FROM postgres:17-alpine

# PASO 1: ENDURECIMIENTO DE SEGURIDAD.
# Propósito: Aplicar inmediatamente las últimas actualizaciones de seguridad
# disponibles en los repositorios de Alpine. Este comando actualiza todos los
# paquetes del sistema operativo base (como libcrypto, openssl, etc.) a sus
# versiones parcheadas, mitigando muchas de las vulnerabilidades encontradas
# en la imagen base original. Se ejecuta primero para asegurar que el resto
# de la construcción se realice sobre una base segura.
RUN apk upgrade --no-cache

# PASO 2: Declarar el argumento de construcción para la versión de glibc.
ARG GLIBC_VER="2.35-r1"

# PASO 3: Instalar dependencias y descargar los TRES paquetes de glibc.
RUN apk add --no-cache --virtual=.build-deps wget ca-certificates && \
    wget -q -O /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub && \
    wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/${GLIBC_VER}/glibc-${GLIBC_VER}.apk && \
    wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/${GLIBC_VER}/glibc-bin-${GLIBC_VER}.apk && \
    wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/${GLIBC_VER}/glibc-i18n-${GLIBC_VER}.apk

# PASO 4: Instalar los paquetes de glibc.
RUN apk add --no-cache --force-overwrite glibc-${GLIBC_VER}.apk glibc-bin-${GLIBC_VER}.apk glibc-i18n-${GLIBC_VER}.apk

# PASO 5: Configurar y generar el locale.
RUN echo "export GCONV_PATH=/usr/glibc-compat/lib/gconv" > /etc/profile.d/gconv.sh && \
    /usr/glibc-compat/bin/localedef -i es_VE -f UTF-8 es_VE.UTF-8

# PASO 6: Limpiar las dependencias de construcción y los archivos descargados.
RUN rm glibc-${GLIBC_VER}.apk glibc-bin-${GLIBC_VER}.apk glibc-i18n-${GLIBC_VER}.apk && \
    apk del .build-deps

# PASO 7: Establecer las variables de entorno para la ejecución.
ENV LANG="es_VE.UTF-8"
ENV LC_ALL="es_VE.UTF-8"