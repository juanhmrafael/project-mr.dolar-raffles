
---

# Manual de Operaciones: Arquitectura Full-Stack (Django + Angular) para Producción

**Filosofía:** Este documento es la fuente de verdad canónica para construir, desplegar y mantener la aplicación full-stack. La arquitectura, aunque desarrollada en un monorepo, está diseñada para un despliegue de producción puro y desacoplado, donde la reproducibilidad, la inmutabilidad de los artefactos y la seguridad son los pilares fundamentales. Todos los comandos deben ejecutarse desde la **raíz del proyecto**.

---

## Índice

- [Arquitectura de Producción: Django API + Angular SPA con Docker](#arquitectura-de-producción-django-api--angular-spa-con-docker)
  - [Filosofía de Diseño](#filosofía-de-diseño)
  - [Stack Tecnológico](#stack-tecnológico)
- [1. Configuración Inicial para Despliegue](#1-configuración-inicial-para-despliegue)
  - [1.1. Estructura de Directorios Clave](#11-estructura-de-directorios-clave)
  - [1.2. Clonar el Repositorio](#12-clonar-el-repositorio)
  - [1.3. Configurar el Archivo de Entorno de Producción](#13-configurar-el-archivo-de-entorno-de-producción)
- [2. Ciclo de Vida del Despliegue en Producción](#2-ciclo-de-vida-del-despliegue-en-producción)
  - [2.1. Flujo de Despliegue Estándar (Desde Cero o para Actualizaciones)](#21-flujo-de-despliegue-estándar-desde-cero-o-para-actualizaciones)
    - [Paso 1: Construir los Artefactos Inmutables](#paso-1-construir-los-artefactos-inmutables)
    - [Paso 2: Lanzar la Pila de Servicios](#paso-2-lanzar-la-pila-de-servicios)
  - [2.2. Accediendo a la Aplicación en Producción](#22-accediendo-a-la-aplicación-en-producción)
  - [2.3. Deteniendo el Entorno para Mantenimiento](#23-deteniendo-el-entorno-para-mantenimiento)
  - [2.4. Reseteo Completo del Entorno (Operación de Alto Riesgo)](#24-reseteo-completo-del-entorno-operación-de-alto-riesgo)
- [3. Guías de Referencia y Tareas Administrativas](#3-guías-de-referencia-y-tareas-administrativas)
  - [3.1. Tareas Comunes de la Aplicación en Producción](#31-tareas-comunes-de-la-aplicación-en-producción)
  - [3.2. Comandos Útiles de Docker para la Gestión del Entorno](#32-comandos-útiles-de-docker-para-la-gestión-del-entorno)

---

# Arquitectura de Producción: Django API + Angular SPA con Docker

Este repositorio contiene una aplicación web moderna y escalable, compuesta por una **API de Django** y una **Aplicación de Página Única (SPA) de Angular**. El sistema está dockerizado siguiendo un enfoque de "producción primero", optimizado para la seguridad, el rendimiento y la estabilidad.

## Filosofía de Diseño

*   **Desacoplamiento Puro:** El backend (Django) y el frontend (Angular) son proyectos independientes que se comunican exclusivamente a través de una API REST.
*   **Orquestación Única para Producción:** Un único `docker-compose.yml` en la raíz del proyecto define y gestiona el ciclo de vida de todos los servicios (backend, frontend, base de datos, etc.) para el entorno de producción. No hay perfiles ni complejidad de entornos múltiples a este nivel.
*   **Seguridad por Defecto:** Nginx actúa como un proxy inverso robusto y endurecido, siendo el único punto de entrada a la aplicación. Sirve la aplicación Angular compilada y reenvía de forma segura el tráfico de la API al backend. Las imágenes de contenedor son mínimas y se ejecutan como usuarios sin privilegios.
*   **Artefactos Inmutables:** El proceso de despliegue se basa en la construcción de imágenes de Docker autocontenidas. Una vez construida, una imagen no se modifica, garantizando que lo que se prueba es exactamente lo que se despliega.

## Stack Tecnológico

*   **Backend:** Django (Modo Asíncrono con ASGI)
*   **Frontend:** Angular
*   **Servidor de Aplicaciones:** Gunicorn + Uvicorn
*   **Servidor Web/Proxy Inverso:** Nginx
*   **Base de Datos:** PostgreSQL
*   **Tareas en Segundo Plano:** Celery
*   **Broker de Mensajes / Caché:** Redis
*   **Contenerización:** Docker & Docker Compose

---

## 1. Configuración Inicial para Despliegue

Siga estos pasos para preparar el proyecto en un servidor de producción.

### 1.1. Estructura de Directorios Clave

La organización del proyecto es fundamental para el despliegue:

```plaintext
/
├── 📁.devcontainer/         # Contiene todo el código de para entornos de Desarrollo con Dev Containers.
├── 📁backend/               # Contiene todo el código de Django.
├── 📁database/              # Contiene todo el código de PostgreSQL.
├── 📁frontend/              # Contiene todo el código de Angular.
├── 📁nginx/                 # Contiene la configuración de Nginx para producción.
├── .dockerignore            # Ignora archivos durante la construcción de las imágenes.
├── docker-compose.yml       # El orquestador principal para los servicios de producción.
├── Dockerfile.backend       # Receta para construir la imagen de Django.
├── Dockerfile.frontend      # Receta para construir la imagen de Angular.
└── .env                     # Archivo ÚNICO con las variables de entorno para producción.
```

### 1.2. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/tu-nuevo-proyecto.git
cd tu-nuevo-proyecto
```

### 1.3. Configurar el Archivo de Entorno de Producción

Este es el paso más crítico para la seguridad y el funcionamiento del proyecto.

1.  **Crear el Archivo `.env`:** Este archivo NO debe existir en el repositorio. Créelo manualmente en la raíz del proyecto. Puede usar el archivo `.env.prod` (si existe como ejemplo) como plantilla, pero el archivo final debe llamarse `.env`.
    ```bash
    # Si tiene un archivo de ejemplo: cp .env.prod.example .env
    # Si no, créelo:
    touch .env
    ```

2.  **Poblar el Archivo `.env`:** Abra el archivo `.env` y añada las siguientes variables, reemplazando los valores con sus credenciales y configuraciones de producción.

3.  **Generar una Clave Secreta Robusta:**
    ```bash
    # Ejecute este comando y copie la salida en la variable SECRET_KEY de su archivo .env
    docker run --rm python:3.13-alpine python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    ```

4.  **Completar y Revisar:** Asegúrese de que todas las variables en `.env` son correctas. Preste especial atención a:
    *   `ALLOWED_HOSTS`: Debe contener su dominio real (ej: `tudominio.com,www.tudominio.com`).
    *   `DB_PASSWORD`: Debe ser una contraseña larga y segura.
    *   `CORS_ALLOWED_ORIGINS` y `TRUSTED_ORIGINS_FOR_CSRF`: Deben apuntar a su dominio final, usando `https://`.

---

## 2. Ciclo de Vida del Despliegue en Producción

### 2.1. Flujo de Despliegue Estándar (Desde Cero o para Actualizaciones)

Este proceso de dos pasos es el método canónico para desplegar la aplicación. Debe ejecutarse cada vez que haya cambios en el código (backend o frontend) o en la configuración de Docker.

#### Paso 1: Construir los Artefactos Inmutables

Este comando construye las imágenes finales y optimizadas que se ejecutarán en el servidor.

```bash
# Propósito: Construye TODAS las imágenes definidas en el docker-compose.yml.
# Docker Compose es lo suficientemente inteligente para entender las dependencias de construcción.
# Construirá 'backend' y 'frontend' primero, y luego 'nginx' que depende de la imagen del frontend.
docker-compose build
```

**Análisis del Proceso:**
1.  Docker Compose lee `docker-compose.yml` y el archivo `.env`.
2.  Construye la imagen `fullstack-raffle:backend-prod` usando `Dockerfile.backend`.
3.  Construye la imagen `fullstack-raffle:frontend-prod` usando `Dockerfile.frontend`.
4.  Construye la imagen `fullstack-raffle:nginx-prod` usando `nginx/Dockerfile.nginx`, que internamente copia los artefactos de la imagen del frontend recién creada.

#### Paso 2: Lanzar la Pila de Servicios

Una vez que las imágenes están construidas, este comando las pone en marcha.

```bash
# Propósito: Inicia o actualiza la pila de producción en segundo plano.
# -d (detached): Esencial para producción. Ejecuta los contenedores en segundo plano.
# --remove-orphans: Si ha renombrado o eliminado un servicio, este flag limpia los contenedores antiguos.
docker-compose up -d --remove-orphans
```

**Análisis del Proceso:**
1.  Docker Compose revisa los servicios definidos. Si un servicio usa una imagen que ha sido reconstruida, recreará el contenedor para usar la nueva imagen.
2.  El `entrypoint.sh` del contenedor `backend` se ejecuta, aplicando migraciones y recolectando estáticos.
3.  El contenedor `nginx` actúa como el único punto de entrada, sirviendo la aplicación Angular y redirigiendo el tráfico de `/api/` al backend.

### 2.2. Accediendo a la Aplicación en Producción

*   **Aplicación Completa:** `http://su-dominio.com` (o la IP de su servidor).

### 2.3. Deteniendo el Entorno para Mantenimiento

Este comando detiene la aplicación de forma segura.

```bash
# Propósito: Detiene y elimina los contenedores, pero preserva los volúmenes de datos críticos.
docker-compose down
```

### 2.4. Reseteo Completo del Entorno (Operación de Alto Riesgo)

**ADVERTENCIA:** Este comando es destructivo y eliminará permanentemente todos los datos de producción (base de datos, archivos subidos). Úselo con extrema precaución.

```bash
# --volumes: Instruye a 'down' para eliminar también los volúmenes de datos asociados.
docker-compose down --volumes
```

---

## 3. Guías de Referencia y Tareas Administrativas

### 3.1. Tareas Comunes de la Aplicación en Producción

| Propósito y Cuándo Usarlo                               | Comando                                                            |
| :------------------------------------------------------ | :----------------------------------------------------------------- |
| **Aplicar cambios a la estructura de la DB**            | `docker-compose exec backend python manage.py migrate`             |
| **Crear un superusuario para el admin de Django**       | `docker-compose exec backend python manage.py createsuperuser`     |
| **Acceder a un shell interactivo dentro del backend**   | `docker-compose exec backend /bin/sh`                              |
| **Acceder a la consola de la base de datos (psql)**     | `docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB`    |

### 3.2. Comandos Útiles de Docker para la Gestión del Entorno

| Propósito y Cuándo Usarlo                               | Comando                                                            |
| :------------------------------------------------------ | :----------------------------------------------------------------- |
| **Ver el estado de todos los contenedores en ejecución**| `docker-compose ps`                                                |
| **Ver los logs de todos los servicios en tiempo real**  | `docker-compose logs -f`                                           |
| **Ver los logs de un servicio específico (ej. backend)**| `docker-compose logs -f backend`                                   |
| **Forzar la reconstrucción de una imagen específica**   | `docker-compose build --no-cache backend`                          |
| **Ver todas las imágenes de Docker en el sistema**      | `docker image ls`                                                  |
| **Ver todos los volúmenes de datos gestionados**        | `docker volume ls`                                                 |
| **Limpieza profunda del sistema (¡Destructivo!)**       | `docker system prune -a --volumes`                                 |