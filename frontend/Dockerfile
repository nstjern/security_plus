# syntax=docker/dockerfile:1
#
# Build context is this directory.
#   docker build -t security-plus-web frontend

FROM node:20-alpine AS build

WORKDIR /app

# Dependencies are installed before the source is copied so the layer caches.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite inlines this at build time, so the image is tied to one API origin.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build


# Serves as an unprivileged user on 8080; nothing here needs root or port 80.
FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime

# Refresh Alpine packages so Trivy does not flag fixable OS CVEs in the base image.
USER root
RUN apk upgrade --no-cache
USER 101

ENV API_ORIGIN=http://localhost:8000

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --spider http://127.0.0.1:8080/ || exit 1
