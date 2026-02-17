# =============================================================================
# Multi-stage Dockerfile for The World frontend
# Build context: project root (not ./frontend)
# =============================================================================

# -- Build stage --
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files for dependency caching
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy shared types (@shared alias resolves to ../shared -> /shared)
COPY shared/ /shared/

# Copy frontend source code
COPY frontend/ ./

# Build the application
RUN npm run build

# -- Production stage --
FROM nginx:alpine AS production

# Copy custom nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
