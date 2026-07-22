# Multi-stage build for the React Operations Dashboard. Build context
# is the REPOSITORY ROOT (see deploy/docker-compose*.yml) - this is
# what lets the production stage pull its nginx config from
# deploy/nginx/production.conf, a sibling of frontend/ rather than a
# file inside it.
#
# Stages:
#   deps       - installs node_modules only
#   dev        - deps + source, runs the Vite dev server (hot reload)
#   build      - deps + source, produces a static production bundle
#   production - nginx serving the static bundle, prod-hardened config
#
# `docker build --target dev` / `--target production` selects which
# one to build; docker-compose.dev.yml / docker-compose.prod.yml pick
# the target for you.

FROM node:22-slim AS deps

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci


FROM deps AS dev

WORKDIR /app

COPY frontend/. .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


FROM deps AS build

WORKDIR /app

COPY frontend/. .

ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_DASHBOARD_SERVICE=rest
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_DASHBOARD_SERVICE=$VITE_DASHBOARD_SERVICE

RUN npm run build


FROM nginx:1.27-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY deploy/nginx/production.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1
