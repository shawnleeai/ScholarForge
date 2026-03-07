# ScholarForge Frontend Dockerfile
# Multi-stage build for production

# ================= Stage 1: Builder =================
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build the application
RUN npm run build

# ================= Stage 2: Production =================
FROM nginx:alpine as production

# Install curl for health check
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1001 -S scholarforge && \
    adduser -S scholarforge -u 1001

# Change ownership of nginx directories
RUN chown -R scholarforge:scholarforge /usr/share/nginx/html && \
    chown -R scholarforge:scholarforge /var/cache/nginx && \
    chown -R scholarforge:scholarforge /var/log/nginx && \
    chown -R scholarforge:scholarforge /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R scholarforge:scholarforge /var/run/nginx.pid

# Switch to non-root user
USER scholarforge

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
