"""
Django management command to simulate real-time agent movement.
Useful for testing and demonstrations of the GPS tracking feature.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import AgentProfile
from apps.logistics.models import LocationHistory
import random
import time
import sys


class Command(BaseCommand):
    help = 'Simulate real-time agent movement for testing GPS tracking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Duration of simulation in seconds (default: 60)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Update interval in seconds (default: 5)',
        )

    def handle(self, *args, **options):
        duration = options['duration']
        interval = options['interval']

        # Get all online agents
        agents = AgentProfile.objects.filter(
            is_online=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('user')

        if not agents.exists():
            self.stdout.write(
                self.style.WARNING(
                    'No online agents with GPS coordinates found. '
                    'Run populate_agent_locations first.'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting simulation for {agents.count()} agents for {duration}s'
            )
        )

        start_time = time.time()
        iterations = 0

        try:
            while (time.time() - start_time) < duration:
                iterations += 1
                updated = 0

                for agent in agents:
                    # Simulate small movement (approx 50-200m per update)
                    # 0.001 degrees ≈ 111 meters
                    delta_lat = random.uniform(-0.002, 0.002)
                    delta_lng = random.uniform(-0.002, 0.002)

                    new_lat = agent.latitude + delta_lat
                    new_lng = agent.longitude + delta_lng

                    # Update agent position
                    agent.latitude = new_lat
                    agent.longitude = new_lng
                    agent.current_speed = random.uniform(5, 35)  # 5-35 km/h
                    agent.heading = random.uniform(0, 360)
                    agent.last_location_update = timezone.now()
                    agent.save()

                    # Save to history
                    LocationHistory.objects.create(
                        agent=agent,
                        latitude=new_lat,
                        longitude=new_lng,
                        accuracy=random.uniform(5, 15),
                        speed=agent.current_speed,
                        heading=agent.heading,
                    )

                    updated += 1

                elapsed = int(time.time() - start_time)
                self.stdout.write(
                    f'[{elapsed}s] Iteration {iterations}: Updated {updated} agents',
                    ending='\r'
                )
                sys.stdout.flush()

                # Wait for next interval
                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write('\n\nSimulation interrupted by user')

        total_time = int(time.time() - start_time)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Simulation completed: {iterations} iterations in {total_time}s'
            )
        )
