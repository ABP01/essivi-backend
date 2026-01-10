"""
Django management command to populate agent locations with test data.
This creates realistic GPS coordinates for agents in Lomé, Togo.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import CustomUser, AgentProfile
from apps.logistics.models import LocationHistory
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Populate agent locations with test data for GPS tracking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--agents',
            type=int,
            default=None,
            help='Number of agents to update (default: all agents)',
        )
        parser.add_argument(
            '--history',
            type=int,
            default=5,
            help='Number of historical location points to create per agent',
        )

    def handle(self, *args, **options):
        # Lomé, Togo coordinates (approximate city bounds)
        LOME_LAT_MIN = 6.100
        LOME_LAT_MAX = 6.180
        LOME_LNG_MIN = 1.180
        LOME_LNG_MAX = 1.280

        # Get all agents or limit by count
        agents = AgentProfile.objects.select_related('user').all()
        if options['agents']:
            agents = agents[:options['agents']]

        if not agents.exists():
            self.stdout.write(self.style.WARNING('No agents found in database'))
            return

        updated_count = 0
        history_count = 0

        for agent in agents:
            # Generate random location in Lomé
            latitude = random.uniform(LOME_LAT_MIN, LOME_LAT_MAX)
            longitude = random.uniform(LOME_LNG_MIN, LOME_LNG_MAX)
            
            # Update agent profile
            agent.latitude = latitude
            agent.longitude = longitude
            agent.is_online = True
            agent.current_speed = random.uniform(0, 40)  # 0-40 km/h
            agent.heading = random.uniform(0, 360)  # Random direction
            agent.last_location_update = timezone.now()
            agent.save()

            updated_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Updated {agent.user.username}: {latitude:.6f}, {longitude:.6f}'
                )
            )

            # Create location history (simulate past movements)
            for i in range(options['history']):
                # Generate nearby coordinates (simulate movement)
                hist_lat = latitude + random.uniform(-0.01, 0.01)
                hist_lng = longitude + random.uniform(-0.01, 0.01)
                
                LocationHistory.objects.create(
                    agent=agent,
                    latitude=hist_lat,
                    longitude=hist_lng,
                    accuracy=random.uniform(5, 20),  # 5-20 meters
                    speed=random.uniform(0, 40),
                    heading=random.uniform(0, 360),
                    timestamp=timezone.now() - timedelta(minutes=i * 5)
                )
                history_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully updated {updated_count} agents'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Created {history_count} location history entries'
            )
        )
