
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.users.models import CustomUser, AgentProfile

print("-" * 50)
print("Listing all users with role='agent':")
agents = CustomUser.objects.filter(role='agent')
for u in agents:
    print(f"User: {u.id} | {u.username} | {u.email} | Active: {u.is_active}")
    try:
        profile = u.agent_profile
        print(f"  > Profile found: ID {profile.id}")
        print(f"  > Tricycle: {profile.tricycle}")
        print(f"  > Zone: {profile.zone_assignee}")
    except AgentProfile.DoesNotExist:
        print("  > NO PROFILE FOUND!")
    except Exception as e:
        print(f"  > Error accessing profile: {e}")

print("-" * 50)
print("Listing all AgentProfiles directly:")
profiles = AgentProfile.objects.all()
for p in profiles:
    print(f"Profile: {p.id} | User: {p.user.username}")

