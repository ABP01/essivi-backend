# Instructions de Déploiement - Suivi de Livraison GPS

## Scripts créés

### 1. `populate_agent_locations.py` 
Script de management Django pour générer des données GPS de test.

**Utilisation :**
```bash
# Via Django management command
python manage.py populate_agent_locations --agents 5 --history 10

# Via Docker (si le backend tourne dans Docker)
docker compose -f infrastructure/docker/docker-compose.yml exec backend \
  python manage.py populate_agent_locations --agents 5 --history 10
```

**Paramètres :**
- `--agents N` : Nombre d'agents à mettre à jour (par défaut: tous)
- `--history N` : Nombre de points d'historique à créer par agent (par défaut: 5)

### 2. `simulate_agent_movement.py`
Script pour simuler le mouvement des agents en temps réel.

**Utilisation :**
```bash
# Simulation de 60 secondes avec mise à jour toutes les 5 secondes
python manage.py simulate_agent_movement --duration 60 --interval 5
```

**Paramètres :**
- `--duration N` : Durée de la simulation en secondes (par défaut: 60)
- `--interval N` : Intervalle de mise à jour en secondes (par défaut: 5)

## Endpoints API ajoutés

### `/api/logistics/agents/test_location/` (GET)
Endpoint de débogage qui retourne des statistiques sur les agents traçables.

**Réponse :**
```json
{
  "stats": {
    "total_agents": 10,
    "online_agents": 5,
    "agents_with_location": 5,
    "agents_trackable": 5
  },
  "trackable_agents": [
    {
      "id": 1,
      "username": "agent1",
      "latitude": 6.1234,
      "longitude": 1.2234,
      "last_update": "2026-01-10T10:45:00Z",
      "speed": 25.5
    }
  ],
  "message": "5 agents are currently trackable"
}
```

## Modifications Frontend Mobile

### `track_delivery_screen.dart`
- Amélioration de la gestion d'erreurs
- Messages clairs quand aucun agent n'est disponible
- Meilleur logging pour le débogage

## Workflow de Test

1. **Générer les données :**
   ```bash
   cd /home/vladmir/Documents/Projet_py/backend
   python manage.py populate_agent_locations
   ```

2. **Vérifier via API :**
   ```bash
   curl http://localhost:8000/api/logistics/agents/test_location/
   ```

3. **Tester dans l'app mobile :**
   - Naviguer vers une livraison
   - Ouvrir l'écran de suivi
   - Vérifier que la carte et les marqueurs s'affichent

4. **Démo avec simulation (optionnel) :**
   ```bash
   python manage.py simulate_agent_movement --duration 120
   ```

## Dépannage

**Problème:** `service "backend" is not running`
**Solution:** Le backend doit tourner pour exécuter les commandes Django. Démarrez-le avec :
```bash
cd /home/vladmir/Documents/Projet_py
docker compose -f infrastructure/docker/docker-compose.yml up -d backend
```

**Problème:** `ModuleNotFoundError: No module named 'corsheaders'`
**Solution:** Installez les dépendances :
```bash
cd backend
pip install -r requirements.txt
```

**Problème:** Aucun agent n'apparaît dans l'app
**Solution:** 
1. Vérifiez que les agents sont en ligne : `GET /api/logistics/agents/test_location/`
2. Vérifiez que l'app mobile pointe vers la bonne URL API
3. Vérifiez les logs de l'app mobile pour les erreurs réseau
