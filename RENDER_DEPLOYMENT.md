# Essivi Backend - Render Deployment

## 🚀 Déploiement sur Render

### Configuration requise

1. **Service Web** :
   - Type : `Docker`
   - Dockerfile : `./infrastructure/docker/Dockerfile`
   - Health Check : `/health/`

2. **Variables d'environnement secrètes** (dans Render Dashboard) :
   ```
   ALLOWED_HOSTS=votre-domaine.onrender.com
   POSTGRES_USER=postgres.jnctexyelciszovwurxn
   POSTGRES_PASSWORD=essivivi2026
   POSTGRES_HOST=aws-1-eu-west-3.pooler.supabase.com
   MONGO_URI=mongodb+srv://armel:essivivi2026@cluster0.tbovg5b.mongodb.net/?appName=Cluster0
   REDIS_HOST=redis-16087.crce202.eu-west-3-1.ec2.cloud.redislabs.com
   REDIS_PORT=16087
   REDIS_PASSWORD=ZhTieGsmKADyHge0M17mPxbVIcOGTxZG
   APPWRITE_PROJECT_ID=697487ca003040b21700
   APPWRITE_API_KEY=standard_606a41923ff9ff9de1608429667e895cf0de95e87fd4000d125c095abc998ddddf11562afa0e72d2a686501ea9f94640b974117e6110cca9067df7ce6d3c6f7525d47b5d6a90404d869ef4ffaaa9123ddeed7e317fadffb7d41d12c05406bb684cf95b17b60c847b036a44cddc1385ab958ab38e589162e79e39f4aecf01a5bf
   CORS_ALLOWED_ORIGINS=https://essivivi.vercel.app,https://essivi-mobile.onrender.com
   ```

### Commandes de déploiement

```bash
# Commit les changements
git add .
git commit -m "feat: configure Render deployment"
git push origin main

# Render détectera automatiquement render.yaml
```

### Points importants

- **ASGI Support** : Utilise Daphne pour les WebSockets
- **Health Check** : `/health/` endpoint pour monitoring
- **Services distants** : Supabase, MongoDB Atlas, Redis Cloud
- **Auto-scaling** : Render gère automatiquement la scalabilité

### Dépannage

Si le déploiement échoue :
1. Vérifiez les logs dans le dashboard Render
2. Assurez-vous que toutes les variables secrètes sont définies
3. Vérifiez la connectivité aux services distants

### URLs après déploiement

- **API** : `https://votre-app.onrender.com/api/`
- **Health** : `https://votre-app.onrender.com/health/`
- **Dashboard Traefik** : Non utilisé (Render gère le proxy)