# syntax=docker/dockerfile:1
# Build: docker build -t frontend .
# Run:   docker run -p 8080:8080 -e BACKEND_URL=http://host.docker.internal:8000 -e API_KEY=change-me frontend

FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY index.html vite.config.ts tsconfig.json ./
COPY src ./src
COPY public ./public
ARG VITE_BRAND=lms
ENV VITE_BRAND=$VITE_BRAND
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine
# nginx renders this template with the container's environment at start (BACKEND_URL, API_KEY).
ENV BACKEND_URL=http://api:8000 API_KEY=""
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD ["wget", "-qO-", "http://localhost:8080/"]
