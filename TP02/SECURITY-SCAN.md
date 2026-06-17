# Rapport de scan de vulnérabilités

Scan réalisé avec **Trivy** (via l'image officielle `aquasec/trivy`, sans
authentification) le 2026-06-04.

> Trivy a été préféré à `docker scout` qui nécessite une connexion Docker Hub.
> La commande utilisée est documentée plus bas et reproductible.

## Commande

```bash
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v trivy-cache:/root/.cache/ \
  aquasec/trivy:latest image --scanners vuln <image>
```

## Résultats

| Image                         | Base                | CRITICAL | HIGH | MEDIUM | LOW |
| ----------------------------- | ------------------- | :------: | :--: | :----: | :-: |
| `tp02-api:single` (mono-stage)| `python:3.13-slim`  |    2     |  7   |   31   | 65  |
| `tp02-api:multi`  (multi-stage)| `python:3.13-alpine`|    0     |  0   |   5    |  2  |
| `tp02-bonus`      (scratch)   | `scratch`           |    0     |  0   |   0    |  0  |

## Analyse

- Les vulnérabilités **CRITICAL/HIGH** de l'image mono-stage proviennent
  exclusivement de la **base Debian (`slim`)** : paquets `perl-base`
  (Archive::Tar, IO-Compress) et `ncurses` (`libncursesw6`, `libtinfo6`...).
  Elles ne sont pas introduites par notre code ni par nos dépendances Python.
- L'image **multi-stage sur Alpine** élimine 100 % des CRITICAL/HIGH : Alpine
  embarque beaucoup moins de paquets système, et le runtime ne contient ni
  toolchain de compilation ni cache de build (grâce au multi-stage).
- L'image **bonus** est basée sur `scratch` : aucun paquet système, donc
  aucune surface d'attaque détectable.

## Pistes de remédiation pour l'image mono-stage

- Migrer la base vers `python:3.13-alpine` (comme la multi-stage) ou
  `gcr.io/distroless/python3`.
- Reconstruire régulièrement pour récupérer les correctifs amont (`apt`).
