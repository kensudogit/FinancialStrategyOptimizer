FROM node:22-alpine AS frontend-deps
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY --from=frontend-deps /frontend/node_modules ./node_modules
COPY frontend/ .
RUN mkdir -p public
ENV NEXT_PUBLIC_API_URL=/api
ENV API_INTERNAL_URL=http://127.0.0.1:8000
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates xz-utils curl \
  && curl -fsSL https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz \
    | tar -xJ -C /usr/local --strip-components=1 \
  && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend/app /app/backend/app

COPY --from=frontend-build /frontend/public /app/frontend/public
COPY --from=frontend-build /frontend/.next/standalone /app/frontend
COPY --from=frontend-build /frontend/.next/static /app/frontend/.next/static

COPY start.sh /app/start.sh
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

ENV PYTHONUNBUFFERED=1
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=/api
ENV API_INTERNAL_URL=http://127.0.0.1:8000
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
ENV FRONTEND_ORIGINS=*

EXPOSE 3000
CMD ["/app/start.sh"]
