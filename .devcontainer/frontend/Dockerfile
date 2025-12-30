# .devcontainer/frontend/Dockerfile
FROM node:22-bookworm-slim

# Instalar herramientas para file watching mejorado
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/frontend

ENV PATH="/workspaces/frontend/node_modules/.bin:$PATH"

# Copiar archivos de dependencias
COPY frontend/package.json frontend/package-lock.json* ./

# Instalar dependencias
RUN npm ci --only=development --silent

# Copiar código fuente
COPY frontend/ ./

CMD ["sleep", "infinity"]