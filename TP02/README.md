# WIK-DPS-TP02

Conteneurisation de l'API HTTP du TP01 (Flask — renvoie les headers de la
requête en JSON sur `GET /ping`, sinon `404`).

Ce TP fournit :

1. une image Docker **mono-stage** optimisée et exécutée en utilisateur non-root ;
2. une image Docker **multi-stage** (build / runtime) encore plus optimisée ;
3. un **scan de vulnérabilités** des deux images ;
4. un **Docker Compose** mettant en place l'application complète
   (reverse-proxy + API + base de données, avec réseaux et volume).

## Arborescence

```
TP02/
├── app.py                  # l'API Flask (reprise du TP01)
├── requirements.txt        # Flask + gunicorn (serveur web de prod)
├── Dockerfile              # image mono-stage
├── Dockerfile.multistage   # image multi-stage (build + runtime)
├── .dockerignore           # contexte de build minimal
├── docker-compose.yml      # stack proxy + api + db
├── nginx/default.conf      # config du reverse-proxy
└── SECURITY-SCAN.md        # résultats du scan Trivy
```

## 1. Image mono-stage

Fichier : [`Dockerfile`](Dockerfile) — base `python:3.13-slim`.

```bash
docker build -t tp02-api:single -f Dockerfile .
docker run --rm -p 2456:2456 tp02-api:single
curl http://localhost:2456/ping
```

**Optimisation de l'ordre des layers** (du moins volatil au plus volatil), pour
que modifier `app.py` ne réinstalle pas les dépendances :

1. base + création de l'utilisateur (quasi jamais modifié) ;
2. `COPY requirements.txt` + `pip install` (rejoué seulement si les deps changent) ;
3. `COPY app.py` (layer le plus volatil, donc en dernier).

**Utilisateur dédié** : un utilisateur non-root `appuser` (UID/GID 1000) est créé
et activé via `USER appuser` avant le lancement du serveur web.

## 2. Image multi-stage

Fichier : [`Dockerfile.multistage`](Dockerfile.multistage) — base `python:3.13-alpine`.

```bash
docker build -t tp02-api:multi -f Dockerfile.multistage .
docker run --rm -p 2456:2456 tp02-api:multi
```

- **Stage `builder`** : Alpine + chaîne de compilation (`build-base`). Installe
  les dépendances dans un virtualenv `/opt/venv`.
- **Stage `runtime`** : Alpine **sans** toolchain. Récupère uniquement le
  virtualenv (`COPY --from=builder /opt/venv /opt/venv`). Le runtime ne contient
  **ni gcc, ni cache pip, ni `requirements.txt`, ni sources de build**, seulement
  `app.py` et les dépendances prêtes à l'emploi.
- Même optimisation de l'ordre des layers et même utilisateur non-root `appuser`.

### Comparaison des tailles

| Image                       | Base                | Taille  |
| --------------------------- | ------------------- | ------- |
| `tp02-api:single`           | `python:3.13-slim`  | ~211 MB |
| `tp02-api:multi`            | `python:3.13-alpine`| ~100 MB |

## 3. Scan de vulnérabilités

Scan réalisé avec **Trivy** (sans authentification, contrairement à
`docker scout` qui exige une connexion Docker Hub). Détails et tableau complet
dans [`SECURITY-SCAN.md`](SECURITY-SCAN.md).

```bash
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v trivy-cache:/root/.cache/ \
  aquasec/trivy:latest image --scanners vuln tp02-api:multi
```

| Image             | CRITICAL | HIGH | MEDIUM | LOW |
| ----------------- | :------: | :--: | :----: | :-: |
| `tp02-api:single` |    2     |  7   |   31   | 65  |
| `tp02-api:multi`  |    0     |  0   |   5    |  2  |

> Les CRITICAL/HIGH de l'image mono-stage proviennent de la base Debian
> (`perl-base`, `ncurses`). L'image multi-stage Alpine les élimine entièrement.

## 4. Docker Compose

Fichier : [`docker-compose.yml`](docker-compose.yml).

```bash
docker compose up -d --build
curl http://localhost:8080/ping      # via le reverse-proxy nginx
docker compose down                  # (ajouter -v pour supprimer le volume)
```

Met en place l'application complète :

| Service | Image                | Rôle                         | Réseaux             |
| ------- | -------------------- | ---------------------------- | ------------------- |
| `proxy` | `nginx:1.27-alpine`  | reverse-proxy (port 8080)    | `frontend`          |
| `api`   | build multi-stage    | l'API Flask                  | `frontend`+`backend`|
| `db`    | `postgres:17-alpine` | base de données              | `backend`           |

- **Deux réseaux** cloisonnent les flux : `frontend` (proxy ↔ api) et `backend`
  (api ↔ db). La base **n'est jamais joignable** depuis le proxy ni depuis l'hôte.
- **Un volume nommé** `db-data` assure la persistance des données PostgreSQL.
- Seul `proxy` expose un port sur l'hôte (`8080`) ; `api` et `db` restent internes.
- `api` attend que `db` soit *healthy* (`depends_on` + `healthcheck`).

## API — comportement (rappel TP01)

| Méthode | Route   | Réponse                                |
| ------- | ------- | -------------------------------------- |
| `GET`   | `/ping` | `200` — JSON des headers de la requête |
| *autre* | *autre* | `404` — corps vide                     |

Port d'écoute configurable via la variable d'environnement `PING_LISTEN_PORT`
(par défaut `2456`).
