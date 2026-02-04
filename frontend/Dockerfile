# syntax=docker/dockerfile:1.5
# Production multi-stage Dockerfile for Kolibri Frontend

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (cache layer)
COPY package*.json ./
RUN npm ci --no-audit --no-fund

# Copy source files
COPY . .

# Build the production bundle
RUN npm run build

# Stage 2: Production
FROM nginx:1.25-alpine

# Security: run as non-root user
RUN addgroup -g 1001 -S kolibri && \
    adduser -S -u 1001 -G kolibri kolibri && \
    chown -R kolibri:kolibri /var/cache/nginx && \
    chown -R kolibri:kolibri /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R kolibri:kolibri /var/run/nginx.pid

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built assets from builder stage
COPY --from=builder --chown=kolibri:kolibri /app/dist /usr/share/nginx/html

# Use non-root user
USER kolibri

EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
