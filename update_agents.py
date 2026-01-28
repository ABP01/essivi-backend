#!/usr/bin/env python
import os
import sys
import django
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.users.models import AgentProfile

def update_agents():
    agents = AgentProfile.objects.all()
    base_lat, base_lng = 6.1319, 1.2228  # Lomé, Togo

    print(f"Updating {agents.count()} agents with coordinates...")

    for i, agent in enumerate(agents):
        # Add some random variation around Lomé
        lat = base_lat + random.uniform(-0.02, 0.02)
        lng = base_lng + random.uniform(-0.02, 0.02)

        agent.latitude = lat
        agent.longitude = lng
        agent.is_online = True
        agent.save()

        print(f"Updated agent {agent.user.username}: lat={lat:.4f}, lng={lng:.4f}, online=True")

    print("Agent update completed!")

if __name__ == '__main__':
    update_agents()