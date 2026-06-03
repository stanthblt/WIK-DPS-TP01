# WIK-DPS-TP01

Petite API HTTP en Python / Flask qui renvoie les headers de la requête au format JSON.

## Comportement

| Méthode | Route   | Réponse                                      |
| ------- | ------- | -------------------------------------------- |
| `GET`   | `/ping` | `200` - JSON des headers de la requête       |
| *autre* | *autre* | `404` — corps vide                           |

## Prérequis

- Python 3.11+
- Flask

## Installation

```bash
# Créer et activer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Lancement

```bash
python app.py
```

Le serveur écoute par défaut sur le port **2456**.

### Port configurable

Port configurable avec la var d'environnement `PING_LISTEN_PORT` :

```bash
PING_LISTEN_PORT=2456 python app.py
```

## Test

```bash
# 200 + headers en JSON
curl -i http://localhost:2456/ping

# 404 corps vide (autre route)
curl -i http://localhost:2456/autre

# 404 corps vide (autre méthode)
curl -i -X POST http://localhost:2456/ping
```
