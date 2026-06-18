import logging
import os
import socket

from flask import Flask, jsonify, request

app = Flask(__name__)

# Port d'écoute configurable via PING_LISTEN_PORT, sinon 2456 par défaut.
DEFAULT_PORT = 2456

# Hostname du conteneur : avec plusieurs réplicas, il diffère d'un conteneur à
# l'autre, ce qui permet d'observer l'équilibrage de charge dans les logs.
HOSTNAME = socket.gethostname()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ping")


@app.get("/ping")
def ping():
    """Retourne les headers de la requête au format JSON + log du hostname."""
    logger.info("Requête /ping traitée par le conteneur %s", HOSTNAME)
    response = jsonify(dict(request.headers))
    # En-tête pratique pour observer l'équilibrage de charge côté client (curl -i).
    response.headers["X-Served-By"] = HOSTNAME
    return response


@app.errorhandler(404)
@app.errorhandler(405)
def not_found(_error):
    """Réponse vide avec code 404 pour tout sauf GET /ping."""
    return "", 404


if __name__ == "__main__":
    port = int(os.environ.get("PING_LISTEN_PORT", DEFAULT_PORT))
    app.run(host="0.0.0.0", port=port)
