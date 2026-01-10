from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('gestionnaire', 'Gestionnaire'),
        ('agent', 'Agent'),
        ('client', 'Client'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone_number = models.CharField(max_length=20, blank=True, null=True)

class AgentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='agent_profile')
    photo = models.ImageField(upload_to='agents/', null=True, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    tricycle = models.ForeignKey('logistics.Tricycle', on_delete=models.SET_NULL, null=True, blank=True)
    zone_assignee = models.CharField(max_length=100, blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    identification_number = models.CharField(max_length=100, blank=True, null=True)
    tricycle_plate = models.CharField(max_length=50, blank=True, null=True)
    
    # Géolocalisation temps réel
    last_location_update = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)
    current_speed = models.FloatField(null=True, blank=True, help_text="Vitesse en km/h")
    heading = models.FloatField(null=True, blank=True, help_text="Direction en degrés (0-360)")

    def __str__(self):
        return f"Agent: {self.user.username}"

class ClientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='client_profile')
    nom_point_vente = models.CharField(max_length=100)
    nom_proprietaire = models.CharField(max_length=100, blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    # Using simple chars for GPS for now, can upgrade to GeoDjango PointField later if PostGIS is set up
    gps_lat = models.FloatField(null=True, blank=True)
    gps_lng = models.FloatField(null=True, blank=True)
    solde = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Adresse formatée pour affichage
    formatted_address = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.nom_point_vente

class UserPreferences(models.Model):
    """User preferences for settings like notifications and language"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='preferences')
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='fr', choices=[
        ('fr', 'Français'),
        ('en', 'English'),
        ('es', 'Español'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"

