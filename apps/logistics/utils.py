"""
Utilitaires pour les calculs de géolocalisation
"""
from math import radians, cos, sin, asin, sqrt

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance entre deux points GPS en kilomètres
    Utilise la formule de Haversine
    
    Args:
        lat1, lon1: Coordonnées du premier point
        lat2, lon2: Coordonnées du deuxième point
    
    Returns:
        Distance en kilomètres
    """
    # Convertir en radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Formule de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Rayon de la Terre en km
    r = 6371
    
    return c * r

def estimate_delivery_time(agent_lat, agent_lng, client_lat, client_lng, avg_speed=25):
    """
    Estime le temps de livraison en minutes
    
    Args:
        agent_lat, agent_lng: Position de l'agent
        client_lat, client_lng: Position du client
        avg_speed: Vitesse moyenne en km/h (défaut: 25 km/h en ville)
    
    Returns:
        Temps estimé en minutes
    """
    distance = calculate_distance(agent_lat, agent_lng, client_lat, client_lng)
    time_hours = distance / avg_speed
    time_minutes = time_hours * 60
    return round(time_minutes)

def find_nearest_agents(client_lat, client_lng, agents, max_agents=5):
    """
    Trouve les agents les plus proches d'un client
    
    Args:
        client_lat, client_lng: Position du client
        agents: QuerySet ou liste d'AgentProfile
        max_agents: Nombre maximum d'agents à retourner
    
    Returns:
        Liste de tuples (agent, distance_km)
    """
    agents_with_distance = []
    
    for agent in agents:
        if agent.latitude and agent.longitude and agent.is_online:
            distance = calculate_distance(
                agent.latitude, agent.longitude,
                client_lat, client_lng
            )
            agents_with_distance.append((agent, distance))
    
    # Trier par distance
    agents_with_distance.sort(key=lambda x: x[1])
    
    # Retourner les N plus proches
    return agents_with_distance[:max_agents]
