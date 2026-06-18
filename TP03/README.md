# WIK-DPS-TP03

Mise à l'échelle de l'API du TP02 : **4 réplicas** derrière un **reverse-proxy
nginx** qui **équilibre la charge**. Seul le reverse-proxy est exposé sur l'hôte
(port **8080**).

## Arborescence

```
TP03/
├── app.py               # API Flask : log du hostname à chaque /ping
├── requirements.txt     # Flask + gunicorn
├── Dockerfile           # image multi-stage (reprise du TP02)
├── .dockerignore
├── docker-compose.yaml  # service api (x4) + proxy nginx
└── nginx/nginx.conf     # configuration du load-balancer
```

## Lancement

```bash
docker compose up -d --build
docker compose ps                 # 4 conteneurs api + 1 proxy
```

## Test de l'équilibrage de charge

```bash
# L'en-tête X-Served-By indique quel conteneur a répondu.
for i in $(seq 1 12); do curl -s -i http://localhost:8080/ping | grep X-Served-By; done

# Observer le hostname dans les logs, réplica par réplica :
docker compose logs -f api
```

Exemple de répartition observée sur 20 requêtes (4 hostnames distincts) :

```
   4 3e3628ba23c7
   3 58ad00a9f9db
   7 84ab5f5d6568
   6 f98b691dec40
```

Et dans les logs :

```
api-2  | ... [INFO] Requête /ping traitée par le conteneur 58ad00a9f9db
api-3  | ... [INFO] Requête /ping traitée par le conteneur 84ab5f5d6568
```

## Comment ça marche

### 4 réplicas (`docker-compose.yaml`)

```yaml
api:
  build: { context: ., dockerfile: Dockerfile }
  expose: ["2456"]      # interne uniquement, PAS publié sur l'hôte
  deploy:
    replicas: 4         # honoré par `docker compose up`
```

Le service `api` n'a **aucun port publié** : il n'est joignable que via le réseau
interne `appnet`. Vérification : `curl http://localhost:2456/ping` échoue, seul
`http://localhost:8080` (le proxy) répond.

### Reverse-proxy / load-balancer (`nginx/nginx.conf`)

```nginx
http {
    resolver 127.0.0.11 valid=1s ipv6=off;   # DNS interne de Docker
    server {
        listen 80;
        location / {
            set $backend "api:2456";          # variable => résolution à l'exécution
            proxy_pass http://$backend;
            ...
        }
    }
}
```

Avec plusieurs réplicas, Docker enregistre le nom de service `api` dans son DNS
interne avec **une entrée par réplica**. En passant par une **variable** dans
`proxy_pass` + le **resolver** Docker, nginx ré-interroge le DNS à chaque requête
(TTL `valid=1s`) : le DNS Docker fait tourner la liste des conteneurs, ce qui
**répartit la charge** sur les 4 réplicas.

### Log du hostname (`app.py`)

```python
HOSTNAME = socket.gethostname()   # = ID du conteneur, différent par réplica

@app.get("/ping")
def ping():
    logger.info("Requête /ping traitée par le conteneur %s", HOSTNAME)
    response = jsonify(dict(request.headers))
    response.headers["X-Served-By"] = HOSTNAME   # observable côté client
    return response
```

## API — comportement (rappel)

| Méthode | Route   | Réponse                                                   |
| ------- | ------- | -------------------------------------------------------- |
| `GET`   | `/ping` | `200` — JSON des headers (+ en-tête `X-Served-By`)       |
| *autre* | *autre* | `404` — corps vide                                       |

## Arrêt

```bash
docker compose down
```
