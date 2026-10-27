# MindScope landing site: build the Vite SPA, serve it with nginx on Cloud Run.
FROM node:22-slim AS build
WORKDIR /site
COPY website/package.json website/package-lock.json ./
RUN npm ci
COPY website/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /site/dist /usr/share/nginx/html
ARG VERSION=dev
RUN echo "$VERSION" > /usr/share/nginx/html/version.txt
EXPOSE 8080
