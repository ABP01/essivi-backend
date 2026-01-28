#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.users.models import AgentProfile

def check_agents():
    try:
        agents = AgentProfile.objects.all()
        print(f"Total agents: {agents.count()}")

        online = agents.filter(is_online=True)
        print(f"Online agents: {online.count()}")

        coords = agents.filter(latitude__isnull=False, longitude__isnull=False)
        print(f"Agents with coordinates: {coords.count()}")

        print("\nAgent details:")
        for agent in agents:
            print(f"Agent {agent.user.username}: online={agent.is_online}, lat={agent.latitude}, lng={agent.longitude}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_agents()