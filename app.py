import os

from flask import Flask, jsonify, request

app = Flask(__name__)

# Port d'écoute configurable via PING_LISTEN_PORT, sinon 2456 par défaut.
DEFAULT_PORT = 2456


@app.get("/ping")
def ping():
    """Retourne les headers de la requête au format JSON."""
    return jsonify(dict(request.headers))


@app.errorhandler(404)
@app.errorhandler(405)
def not_found(_error):
    """Réponse vide avec code 404 pour tout sauf GET /ping."""
    return "", 404


if __name__ == "__main__":
    port = int(os.environ.get("PING_LISTEN_PORT", DEFAULT_PORT))
    app.run(host="0.0.0.0", port=port)
