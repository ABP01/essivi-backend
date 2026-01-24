# Traefik Configuration

Ce dossier contient la configuration statique de Traefik pour le projet Essivi Backend.

## Fichiers

- `traefik.yml` : Configuration dynamique des routes et services Traefik

## Routes Configurées

### API Backend
- **URL** : `http://localhost/api/` ou `http://api.localhost/api/`
- **Service** : `backend:8000`
- **Middlewares** : CORS headers

### WebSocket
- **URL** : `ws://api.localhost/ws/`
- **Service** : `backend:8000`

### Dashboard Traefik
- **URL** : `http://traefik.localhost/`
- **Service** : API interne Traefik

## Headers CORS

Les headers suivants sont automatiquement ajoutés :
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, OPTIONS, PUT, POST, DELETE, PATCH`
- `Access-Control-Allow-Headers: *`

## Modification

Pour modifier la configuration :
1. Éditer le fichier `traefik.yml`
2. Redémarrer Traefik : `docker-compose restart traefik`

## Structure

```
infrastructure/
├── docker/
│   ├── docker-compose.yml
│   └── ...
└── traefik/
    ├── traefik.yml
    └── README.md
```