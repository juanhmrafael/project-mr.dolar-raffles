
---
# Documentación del Proyecto
**Filosofía:** Este documento es la fuente de verdad canónica para construir, desplegar y mantener la aplicación full-stack. La arquitectura, aunque desarrollada en un monorepo, está diseñada para un despliegue de producción puro y desacoplado, donde la reproducibilidad, la inmutabilidad de los artefactos y la seguridad son los pilares fundamentales. Todos los comandos deben ejecutarse desde la **raíz del proyecto**.

---

## 📑 Índice de Contenidos

1.  [💻 1. Stack Tecnológico](#1-stack-tecnológico)
2.  [🗺️ 2. Anatomía del Proyecto](#2-anatomía-del-proyecto)
3.  [🔐 3. Protocolo de Seguridad (Paso Cero)](#3-protocolo-de-seguridad-paso-cero)
4.  [⚙️ 4. Configuración de Entornos (.env)](#4-configuración-de-entornos-env)
5.  [🛠️ 5. Guía de Desarrollo (DevContainer)](#5-guía-de-desarrollo-devcontainer)
6.  [🚀 6. Despliegue en Producción](#6-despliegue-en-producción)
7.  [🔧 7. Operaciones y Mantenimiento](#7-operaciones-y-mantenimiento)
8.  [🆘 8. Troubleshooting (Solución de Problemas)](#8-troubleshooting-solución-de-problemas)

---

##  1. Stack Tecnológico

El proyecto utiliza tecnologías de vanguardia enfocadas en rendimiento, mantenibilidad y seguridad.

| Capa | Tecnología | Características Clave |
| :--- | :--- | :--- |
| **Backend** | **Django 5.2** | Enfoque Híbrido (Async/Sync), Arquitectura Modular (DDD), Django REST Framework + Ninja. |
| **Frontend** | **Angular 20+** | Arquitectura **Zoneless** con Signals, Standalone Components, TailwindCSS para estilos. |
| **Base de Datos** | **PostgreSQL 17** | Persistencia relacional robusta. Extensiones activas para búsqueda y geolocalización. |
| **Caché & Broker** | **Redis 7** | Gestión de Caché, Broker de Mensajería (Celery) y almacenamiento de sesiones volátiles. |
| **Infraestructura** | **Docker Compose** | Orquestación de servicios. Uso de **Docker Secrets** para gestión de credenciales (Zero-Trust). |
| **Gateway** | **Nginx 1.25+** | Proxy Inverso, Terminación SSL/TLS, Compresión Gzip/Brotli y Servidor de Estáticos. |
| **Entorno Dev** | **DevContainers** | Entorno de desarrollo estandarizado y reproducible basado en VS Code. |

---

##  2. Anatomía del Proyecto
Entender la estructura de carpetas es vital. El proyecto no es un monolito simple; es un sistema distribuido.
*   📂 **Directorios con Candado (🔒):** Contienen datos sensibles. **NUNCA** se suben a Git. Debes crearlos manualmente.
*   ⚠️ **Archivos Críticos:** Configuraciones que, si faltan, impedirán el arranque.

```text
└── 📁app-raffles
    │
    │   # ---------------------------------------------------------
    │   # 🛠️ ENTORNO DE DESARROLLO (DevContainer)
    │   # Configuración para VS Code Remote Containers.
    │   # Todo lo que ocurre al programar sucede aquí dentro.
    │   # ---------------------------------------------------------
    ├── 📁.devcontainer
    │   ├── 📁backend
    │   │   ├── 📁redis
    │   │   │   ├── Dockerfile          # Imagen Redis optimizada para Dev
    │   │   │   └── redis.conf          # Configuración relajada para Dev
    │   │   ├── .env                # ⚠️ Variables de entorno del contenedor DEV
    │   │   ├── devcontainer.json   # Definición del entorno VS Code
    │   │   ├── docker-compose.yml  # Orquestación local (Backend+DB+Redis)
    │   │   └── Dockerfile          # Entorno Python con herramientas de depuración
    │   └── 📁frontend
    │       ├── devcontainer.json
    │       ├── docker-compose.yml
    │       └── Dockerfile          # Entorno Node.js con Angular CLI
    │
    │   # ---------------------------------------------------------
    │   # 🔐 GESTIÓN DE SECRETOS (Producción / Docker Secrets)
    │   # Archivos planos montados en /run/secrets/ dentro de los contenedores.
    │   # ESTA CARPETA NO EXISTE EN GIT, DEBES CREARLA.
    │   # ---------------------------------------------------------
    ├── 📁secrets                   # 🔒 [CREAR MANUALMENTE]
    │   ├── django_secret_key.txt       # ⚠️ Clave maestra de Django (Prod)
    │   ├── field_encryption_key.txt    # ⚠️ Clave 32-bytes para encriptar DB
    │   ├── postgres_db.txt             # Nombre de la BD Producción
    │   ├── postgres_password.txt       # Password del usuario DB
    │   ├── postgres_user.txt           # Usuario DB
    │   └── redis_appuser_password.txt  # Auth para Redis ACLs
    │
    │   # ---------------------------------------------------------
    │   # 🌐 INFRAESTRUCTURA & GATEWAY
    │   # Nginx actúa como la única puerta de entrada (Puerto 80/443).
    │   # ---------------------------------------------------------
    ├── 📁nginx
    │   ├── 📁certs                 # 🔒 [CREAR MANUALMENTE SI USAS SSL]
    │   │   ├── cert.pem            # ⚠️ Certificado SSL público
    │   │   └── key.pem             # ⚠️ Clave privada SSL
    │   ├── 📁conf.d
    │   │   └── default.conf        # Configuración de VHosts y Upstreams
    │   ├── Dockerfile.nginx        # Construye la imagen final del Proxy
    │   └── nginx.conf              # Configuración base (worker_processes, gzip)
    │
    │   # ---------------------------------------------------------
    │   # 🧠 BACKEND (Django 5.2 - Async/Sync Hybrid)
    │   # ---------------------------------------------------------
    ├── 📁backend
    │   ├── 📁apps                  # Módulos de Negocio (Clean Architecture)
    │   │   ├── 📁auditing          # Logs de Auditoría
    │   │   ├── 📁currencies        # Integración BCV / Tasas
    │   │   ├── 📁participants      # Gestión de Concursantes
    │   │   ├── 📁payments          # Pasarela Modular
    │   │   ├── 📁raffles           # Core del Negocio (Sorteos)
    │   │   ├── 📁tickets           # Generación de Boletos
    │   │   └── ...
    │   ├── 📁config                # Settings (Production vs Development)
    │   │   ├── 📁settings
    │   │   │   ├── base.py         # Configuración común
    │   │   │   ├── development.py  # Usado por .devcontainer
    │   │   │   └── production.py   # Usado por Dockerfile.backend
    │   ├── 📁requirements          # Dependencias Python
    │   └── manage.py
    │
    │   # ---------------------------------------------------------
    │   # 🎨 FRONTEND (Angular 20 - Zoneless)
    │   # ---------------------------------------------------------
    ├── 📁frontend
    │   ├── 📁src                   # Código fuente SPA
    │   │   ├── 📁app               # Componentes y Lógica
    │   │   │   ├── 📁core          # Capa de Infraestructura Frontend
    │   │   │   │   ├── 📁api           # Clientes HTTP Tipados
    │   │   │   │   ├── 📁layout        # Estado de UI Global
    │   │   │   │   ├── 📁state         # Store Global (Signals)
    │   │   │   │   ├── 📁auth          # Interceptors & Guards
    │   │   │   │   └── ...
    │   │   │   │
    │   │   │   ├── 📁features      # Vistas Inteligentes (Smart Components)
    │   │   │   │   ├── 📁home
    │   │   │   │   ├── 📁location-page
    │   │   │   │   └── 📁raffle-detail
    │   │   │   │
    │   │   │   ├── 📁layouts       # Shells de la App
    │   │   │   │
    │   │   │   └── 📁shared        # UI Kit (Dumb Components)
    │   │   │   │   ├── 📁directives
    │   │   │   │   ├── 📁models        # Interfaces TypeScript
    │   │   │   │   └── 📁ui            # Componentes Reutilizables
    │   │   │   │       ├── 📁current-raffle
    │   │   │   │       ├── 📁prize-card
    │   │   │   │       ├── 📁ticket-lookup-modal
    │   │   │   │       └── ...
    │   │   │   │
    │   │   │   ├── app.config.ts       # Configuración Standalone (Providers)
    │   │   │   ├── app.routes.ts       # Definición de Rutas
    │   │   │   └── ...
    │   │   │
    │   │   ├── main.ts             # Bootstrap de la App
    │   │   └── styles.css          # Tailwind Imports
    │   │         
    │   ├── angular.json            # Configuración de Build
    │   ├── package.json            # Dependencias NPM
    │   ├── tailwind.config.js
    │   ├── tsconfig.json
    │   └── proxy.conf.json         # Proxy para Dev Local (CORS)
    │
    │   # ---------------------------------------------------------
    │   # 💾 PERSISTENCIA & CACHE
    │   # ---------------------------------------------------------
    ├── 📁database
    │   └── Dockerfile              # Postgres personalizado (Extensiones, locales)
    ├── 📁redis
    │   ├── Dockerfile
    │   └── redis.conf              # Configuración para producción
    │
    │   # ---------------------------------------------------------
    │   # ⚙️ ORQUESTACIÓN DE PRODUCCIÓN (Raíz)
    │   # Archivos utilizados al desplegar en el servidor real.
    │   # ---------------------------------------------------------
    ├── .env                        # ⚠️ Variables globales para Docker Compose Prod
    ├── docker-compose.yml          # Definición de servicios (Prod)
    ├── Dockerfile.backend          # Imagen Docker final (Python optimizado)
    ├── Dockerfile.frontend         # Imagen Docker final (Builder Stage)
    └── entrypoint.sh               # ⚠️ Script de arranque (Migraciones, Collectstatic auto)
```

---

##  3. Protocolo de Seguridad (Paso Cero)

Antes de intentar ejecutar nada, el sistema requiere configurar la seguridad. Si omites esto, los contenedores se reiniciarán en bucle (CrashLoopBackOff).

### 3.1 ¿Por qué usamos Docker Secrets?
En lugar de variables de entorno (`.env`) para contraseñas, usamos **Docker Secrets**.
*   **Seguridad:** Las variables `.env` pueden verse inspeccionando el proceso o los logs de error.
*   **Aislamiento:** Los *Secrets* se montan como archivos temporales en memoria RAM (`/run/secrets/`) solo visibles por el proceso que los necesita.

### 3.2 Generación de Secretos (`secrets/`)
Ejecuta estos comandos en la raíz del proyecto para crear los archivos necesarios.
*Nota: Se incluyen comandos comentados (`#`) para generar claves criptográficamente seguras si lo deseas.*

```bash
# 1. Crear carpeta (ignorada por git)
mkdir -p secrets

# 2. Base de Datos (PostgreSQL)
# Define aquí tus credenciales reales para producción
echo "app_raffles_db_prod" > secrets/postgres_db.txt
echo "admin_user" > secrets/postgres_user.txt
echo "MI_CONTRASEÑA_SUPER_SEGURA_DB_123" > secrets/postgres_password.txt

# 3. Django Security Keys
# Genera una Secret Key larga y aleatoria
# python3 -c "import secrets; print(secrets.token_urlsafe(64))" > secrets/django_secret_key.txt
echo "django-insecure-prod-key-generada-aleatoriamente" > secrets/django_secret_key.txt

# Genera una clave Fernet (Base64 de 32 bytes) para encriptar columnas sensibles
# python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > secrets/field_encryption_key.txt
echo "5Xs9dbIXf1jSubrxWlehlF7AG89ANzhrqmT5a4dSUhE=" > secrets/field_encryption_key.txt

# 4. Redis Security
# Genera una clave hexadecimal de 32 bytes (64 caracteres): openssl rand -hex 32 > secrets/redis_appuser_password.txt
echo "REDIS_ACL_PASSWORD_123" > secrets/redis_appuser_password.txt
```

### 3.3 Certificados SSL (`nginx/certs/`) - *Solo Producción*
Para que tu dominio `tudominio.com` funcione con HTTPS (Candado verde):

1.  Crea la carpeta: `mkdir -p nginx/certs`
2.  Copia tus certificados (adquiridos o generados con Certbot, Cloudflare, etc):
    *   **`cert.pem`**: El certificado público (incluyendo la cadena intermedia/fullchain).
    *   **`key.pem`**: La clave privada (desencriptada).

---

##  4. Configuración de Entornos (.env)

El proyecto maneja dos contextos totalmente separados. No confundir el archivo `.env` de la raíz con el de la carpeta `.devcontainer`.

### 💻 A. Entorno de Desarrollo (Local / VS Code)
Este archivo ya existe en tu estructura en: `.devcontainer/backend/.env`.
Configura el entorno para trabajar dentro de VS Code.

```ini
# UBICACIÓN: .devcontainer/backend/.env
# =======================================================
# CONFIGURACIÓN DEVCONTAINER (Aislado)
# =======================================================

# ---  Django Core y Seguridad ---
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY="dev-key-solo-para-local"
FIELD_ENCRYPTION_KEY="5Xs9dbIXf1jSubrxWlehlF7AG89ANzhrqmT5a4dSUhE="
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# --- Base de Datos (PostgreSQL) ---
DB_ENGINE=django.db.backends.postgresql
DB_NAME=app_raffles_db_dev
DB_USER=app_raffles_user_dev
DB_PASSWORD=app_raffles_password_dev
DB_HOST=db_dev
DB_PORT=5432

# --- Variables para la Imagen Oficial de Postgres ---
POSTGRES_DB=app_raffles_db_dev
POSTGRES_USER=app_raffles_user_dev
POSTGRES_PASSWORD=app_raffles_password_dev

# --- Redis (Broker y Caché) ---
# Propósito: Estas variables son requeridas por la nueva lógica en `settings/base.py`.
REDIS_HOST=redis_dev
REDIS_PORT=6379
REDIS_USER=appuser_dev
REDIS_PASSWORD=devpassword_e4d3c2b1 # Contraseña para Redis en desarrollo

# URLs base de Redis SIN autenticación. El código Django añadirá las credenciales.
RAW_REDIS_BROKER_URL=redis://redis_dev:6379/0
RAW_REDIS_RESULT_URL=redis://redis_dev:6379/1
RAW_REDIS_CACHE_URL=redis://redis_dev:6379/2
RAW_REDIS_SELECT2_URL=redis://redis_dev:6379/3

# --- CORS y CSRF ---
CORS_ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200

# --- Variables para pgAdmin (PRESERVADAS) ---
# Credenciales para iniciar sesión en la interfaz web de pgAdmin.
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=admin
```

### 🚀 B. Entorno de Producción (Servidor)
Este archivo debe crearse en la **RAÍZ** del proyecto (`./.env`). Configura la orquestación real.

```ini
# UBICACIÓN: ./.env (RAÍZ)
# =======================================================
# CONFIGURACIÓN DE PRODUCCIÓN
# =======================================================

# --- Django Settings ---
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
# ¡IMPORTANTE! Aquí define tu dominio real
ALLOWED_HOSTS=tudominio.com,www.tudominio.com,backend

# --- Conexiones (Nombres de servicio de docker-compose.yml raíz) ---
# Nota: NO poner contraseñas aquí. Se leen de /secrets/
DB_ENGINE=django.db.backends.postgresql
DB_HOST=db
DB_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_USER=appuser

# --- Redis URLs (Sin password, Django lo inyecta desde secrets) ---
RAW_REDIS_BROKER_URL=redis://redis:6379/0
RAW_REDIS_RESULT_URL=redis://redis:6379/3
RAW_REDIS_CACHE_URL=redis://redis:6379/1
RAW_REDIS_SELECT2_URL=redis://redis:6379/2

# --- Seguridad Web (CORS/CSRF) ---
CORS_ALLOWED_ORIGINS=https://tudominio.com,https://www.tudominio.com
CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com
```


---

##  5. Guía de Desarrollo (DevContainer)

El proyecto utiliza **VS Code DevContainers**. Esto significa que no necesitas instalar Python, Node.js, PostgreSQL o Redis en tu máquina local. Todo el entorno de desarrollo se construye automáticamente dentro de un contenedor Docker aislado.

### 5.1 Prerrequisitos
1.  **Docker Desktop** (iniciado).
2.  **Visual Studio Code**.
3.  Extensión **"Dev Containers"** (ms-vscode-remote.remote-containers) instalada en VS Code.

### 5.2 Iniciar el Entorno
1.  Abre la carpeta raíz `app-raffles` en VS Code.
2.  Aparecerá una notificación (o presiona `F1`): **"Dev Containers: Reopen in Container"**.
3.  Selecciona la configuración deseada (generalmente abrirá el espacio de trabajo completo).
4.  ⏳ **Espera:** La primera vez, Docker descargará y construirá las imágenes. Esto puede tomar unos minutos.

Una vez cargado, verás en la esquina inferior izquierda: `Dev Container: App Raffles`.

### 5.3 Ejecutar los Servicios (Hot-Reload)
Dentro del contenedor, abre la terminal integrada de VS Code (`Ctrl + ñ`).

#### **Backend (Django)**
El entorno ya tiene las dependencias instaladas.
```bash
# 1. Navegar al backend
cd backend

# 2. Aplicar migraciones (solo la primera vez o si hay cambios en modelos)
python manage.py migrate

# 3. Crear superusuario (opcional, para entrar al admin)
python manage.py createsuperuser

# 4. Iniciar servidor de desarrollo
python manage.py runserver 0.0.0.0:8000
```
*Acceso API:* `http://localhost:8000`

#### **Frontend (Angular)**
Abre una **nueva terminal** en VS Code (botón `+`).
```bash
# 1. Navegar al frontend
cd frontend

# 2. Instalar dependencias (si es la primera vez)
npm install

# 3. Iniciar servidor de desarrollo (Accesible desde fuera del contenedor)
ng serve --host 0.0.0.0 --disable-host-check
```
*Acceso App:* `http://localhost:4200`

---

##  6. Despliegue en Producción

Esta sección detalla cómo levantar el sistema en un servidor Linux (Ubuntu/Debian) usando la configuración de la raíz.

**Requisitos previos:**
1.  Haber completado el **Paso 3 (Secretos)** y **Paso 4 (.env raíz)** de este manual.
2.  Tener Docker y Docker Compose instalados en el servidor.

### 6.1 Comandos de Despliegue
Ejecuta estos comandos desde la **raíz** del proyecto (`/app-raffles`).

```bash
# 1. Construir e iniciar los contenedores en segundo plano
# --build: Fuerza la reconstrucción de imágenes para asegurar que tienes el último código
docker compose up -d --build

# 2. Verificar el estado de los contenedores
docker compose ps
```

Deberías ver los servicios: `nginx`, `backend`, `frontend`, `db`, `redis` con estado **Up**.

### 6.2 Inicialización de Base de Datos (Solo primera vez)
Aunque el contenedor `backend` intenta migrar al inicio, es recomendable verificar o crear el primer usuario administrador manualmente.

```bash
# Ejecutar migraciones explícitamente en el contenedor de producción
docker compose exec backend python manage.py migrate

# Recolectar archivos estáticos (CSS/JS del admin)
docker compose exec backend python manage.py collectstatic --noinput
```

### 6.3 Verificación
Abre tu navegador y navega a `https://tudominio.com`.
*   Si configuraste SSL correctamente, verás el candado verde.
*   Nginx redirigirá automáticamente el tráfico HTTP a HTTPS.

---

##  7. Operaciones y Mantenimiento

Comandos recurrentes para la administración del sistema en producción.

### 7.1 Gestión de Usuarios y Accesos
Crear un administrador del sistema (Superuser) en producción:

```bash
docker compose exec backend python manage.py createsuperuser
```
Luego accede a: `https://tudominio.com/admin`

### 7.2 Monitoreo de Logs
Si algo falla, lo primero es revisar los registros en tiempo real.

```bash
# Ver logs de todos los servicios
docker compose logs -f

# Ver logs de un servicio específico (ej. backend o nginx)
docker compose logs -f backend
docker compose logs -f nginx
```

### 7.3 Copias de Seguridad (Backups)
Para respaldar la base de datos sin detener el servicio:

```bash
# Genera un archivo SQL comprimido con la fecha actual
docker compose exec db pg_dump -U admin_user app_raffles_db_prod | gzip > backup_$(date +%Y-%m-%d).sql.gz
```
*Nota: Reemplaza `admin_user` y `app_raffles_db_prod` con los valores que definiste en tus `secrets/`.*

### 7.4 Actualización del Sistema
Para desplegar cambios nuevos desde el repositorio:

```bash
# 1. Traer el código nuevo
git pull origin main

# 2. Reconstruir y reiniciar (Solo recreará lo que cambió)
docker compose up -d --build --remove-orphans

# 3. Aplicar migraciones si hubo cambios en base de datos
docker compose exec backend python manage.py migrate
```

---

##  8. Troubleshooting (Solución de Problemas)

### Error: "502 Bad Gateway" en Nginx
*   **Causa:** Django (backend) no está respondiendo o sigue iniciándose.
*   **Solución:** Revisa los logs del backend: `docker compose logs -f backend`.

### Error: "CrashLoopBackOff" o reinicios constantes
*   **Causa:** Faltan archivos en la carpeta `secrets/` o tienen permisos incorrectos.
*   **Solución:** Verifica que existan los archivos `.txt` y que no estén vacíos.

### Error: Database connection failed
*   **Causa:** El nombre del host en `.env` no coincide con el servicio de docker-compose.
*   **Solución:** Asegúrate de que en `.env` (Raíz) tengas `DB_HOST=db` y `REDIS_HOST=redis`.


---