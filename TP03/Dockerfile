# syntax=docker/dockerfile:1
###############################################################################
# Image multi-stage de l'API (reprise du Dockerfile multi-stage du TP02).
#
#   Stage 1 (builder) : Alpine + toolchain, installe les deps dans un venv.
#   Stage 2 (runtime) : Alpine sans toolchain, ne récupère que le venv + app.py.
#
# Ordre des layers optimisé : deps avant le code pour profiter du cache.
###############################################################################

# --- Stage 1 : build -------------------------------------------------------
FROM python:3.13-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apk add --no-cache build-base

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2 : runtime -----------------------------------------------------
FROM python:3.13-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    PING_LISTEN_PORT=2456

# Utilisateur non-root dédié à l'exécution du serveur web.
RUN addgroup -g 1000 appuser \
    && adduser -u 1000 -G appuser -D -H -s /sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY app.py .

USER appuser

EXPOSE 2456

CMD exec gunicorn --bind "0.0.0.0:${PING_LISTEN_PORT}" --workers 2 app:app
