from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.sales.models import Commande, Livraison
from apps.logistics.models import Tricycle
from apps.users.models import AgentProfile, ClientProfile
from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDay, Coalesce
from django.utils import timezone
from datetime import timedelta

from drf_spectacular.utils import extend_schema

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: dict},
        description="Get dashboard statistics (count of orders, deliveries, etc.)"
    )
    def get(self, request):
        # Only allow the admin user 'elom' or users with role 'admin' / is_superuser
        user = request.user
        user_role = getattr(user, 'role', None)
        if not (user.username == 'elom' or user.username == 'admin' or user.is_superuser or user_role == 'admin'):
            return Response({'detail': 'Accès au dashboard réservé à l\'administrateur.'}, status=403)

        now = timezone.now()
        
        # 1. Summary KPIs
        # Revenue: Sum of montant for delivered orders
        total_revenue = Commande.objects.filter(statut='delivered').aggregate(
            total=Coalesce(Sum('montant'), 0, output_field=models.DecimalField())
        )['total']
        
        total_livraisons = Livraison.objects.count()
        total_pending_orders = Commande.objects.filter(statut='pending').count()
        
        active_agents = AgentProfile.objects.count()
        active_clients = ClientProfile.objects.count()
        # Tricycle model uses `status` with choices ('active','maintenance','inactive')
        active_tricycles = Tricycle.objects.filter(status='active').count()

        # 2. Advanced Metrics
        delivered_orders = Commande.objects.filter(statut='delivered')
        avg_delivery_time_minutes = 0
        if delivered_orders.exists():
            # Calculate average time in minutes between creation and delivery
            total_seconds = sum((o.updated_at - o.created_at).total_seconds() for o in delivered_orders)
            avg_delivery_time_minutes = int((total_seconds / delivered_orders.count()) / 60)

        # Agent Performance
        agent_perf = AgentProfile.objects.annotate(
            delivery_count=Count('user__commandes_agent', filter=models.Q(user__commandes_agent__statut='delivered'))
        ).select_related('user').order_by('-delivery_count')[:5]

        formatted_agent_perf = [
            {
                "name": f"{a.user.first_name} {a.user.last_name}" if a.user.first_name else a.user.username,
                "deliveries": a.delivery_count,
                "photo": a.photo.url if a.photo else None
            } for a in agent_perf
        ]

        # 3. Revenue Chart (Last 6 months)
        six_months_ago = now - timedelta(days=30*6)
        revenue_data = Commande.objects.filter(
            statut='delivered',
            updated_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('updated_at')
        ).values('month').annotate(
            revenue=Coalesce(Sum('montant'), 0, output_field=models.DecimalField())
        ).order_by('month')
        
        formatted_revenue_chart = [
            {
                "month": item['month'].strftime("%b"), 
                "revenue": float(item['revenue'])
            } for item in revenue_data
        ]
        
        # 4. Delivery Chart (Last 7 days)
        seven_days_ago = now - timedelta(days=6) # 7 days including today
        delivery_data = Livraison.objects.filter(
            timestamp__gte=seven_days_ago
        ).annotate(
            day=TruncDay('timestamp')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Fill in missing days
        formatted_delivery_chart = []
        delivery_map = {item['day'].date(): item['count'] for item in delivery_data}
        
        for i in range(7):
            day = (now - timedelta(days=6-i)).date()
            formatted_delivery_chart.append({
                "day": day.strftime("%a"),
                "deliveries": delivery_map.get(day, 0)
            })

        return Response({
            'kpis': {
                'total_revenue': float(total_revenue),
                'total_deliveries': total_livraisons,
                'total_pending_orders': total_pending_orders,
                'active_agents': active_agents,
                'active_clients': active_clients,
                'active_tricycles': active_tricycles,
                'avg_delivery_time': avg_delivery_time_minutes,
            },
            'charts': {
                'revenue': formatted_revenue_chart,
                'deliveries': formatted_delivery_chart
            },
            'agent_performance': formatted_agent_perf
        })
