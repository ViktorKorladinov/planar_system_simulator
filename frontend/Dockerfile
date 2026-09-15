# ==========================================
# Stage 1: Build Frontend Assets
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests first for layer caching
COPY package.json package-lock.json ./

# Install clean dependencies
RUN npm ci

# Copy project configuration and source files
COPY tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts index.html ./
COPY public ./public
COPY src ./src

# Build-time environment variables (defaulting to relative path for reverse proxy routing)
ARG VITE_BACKEND_URL=/api/v1
ARG VITE_SIMULATOR_URL=http://localhost:3000

ENV VITE_BACKEND_URL=$VITE_BACKEND_URL \
    VITE_SIMULATOR_URL=$VITE_SIMULATOR_URL

# Build production SPA
RUN npm run build

# ==========================================
# Stage 2: Serve with Lightweight Nginx
# ==========================================
FROM nginx:1.27-alpine AS runner

# Remove default configuration and install custom config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
