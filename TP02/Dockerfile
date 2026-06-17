# syntax=docker/dockerfile:1
###############################################################################
# Image mono-stage pour l'API WIK-DPS-TP01 (Flask).
#
# Ordre des layers optimisé pour le cache :
#   1. base + dépendances système (changent très rarement)
#   2. requirements.txt + pip install (ne se rejoue que si les deps changent)
#   3. code applicatif (change souvent -> placé en dernier)
# Ainsi, une simple modification de app.py ne réinstalle PAS les dépendances.
###############################################################################
FROM python:3.13-slim

# Bonnes pratiques Python en conteneur :
#   - pas de fichiers .pyc
#   - sortie non bufferisée (logs visibles en temps réel)
#   - pas de cache pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PING_LISTEN_PORT=2456

# Utilisateur non-root dédié à l'exécution du serveur web.
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# 1) Dépendances : copiées et installées AVANT le code pour profiter du cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Code applicatif : layer le plus volatil, donc placé en dernier.
COPY app.py .

# Bascule sur l'utilisateur non privilégié.
USER appuser

EXPOSE 2456

# Serveur web de production (gunicorn). `exec` => gunicorn devient PID 1
# et reçoit correctement les signaux (SIGTERM lors d'un `docker stop`).
CMD exec gunicorn --bind "0.0.0.0:${PING_LISTEN_PORT}" --workers 2 app:app
