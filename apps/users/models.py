from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('gestionnaire', 'Gestionnaire'),
        ('agent', 'Agent'),
        ('client', 'Client'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone_number = models.CharField(max_length=20, blank=True, null=True)

from core.utils.images import compress_image

class AgentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='agent_profile')
    photo = models.ImageField(upload_to='agents/', null=True, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    tricycle = models.ForeignKey('logistics.Tricycle', on_delete=models.SET_NULL, null=True, blank=True)
    zone_assignee = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if self.photo and not self.photo.name.endswith('.webp'):
            self.photo = compress_image(self.photo)
        super().save(*args, **kwargs)

    latitude = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(-90.0, message="Latitude must be >= -90"),
            MaxValueValidator(90.0, message="Latitude must be <= 90")
        ],
        help_text="Latitude entre -90 et 90"
    )
    longitude = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(-180.0, message="Longitude must be >= -180"),
            MaxValueValidator(180.0, message="Longitude must be <= 180")
        ],
        help_text="Longitude entre -180 et 180"
    )
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
    nom_point_vente = models.CharField(max_length=100, blank=True, default="N/A")
    nom_proprietaire = models.CharField(max_length=100, blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    # Using simple chars for GPS for now, can upgrade to GeoDjango PointField later if PostGIS is set up
    gps_lat = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(-90.0),
            MaxValueValidator(90.0)
        ]
    )
    gps_lng = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(-180.0),
            MaxValueValidator(180.0)
        ]
    )
    solde = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0, message="Solde cannot be negative")]
    )
    
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

class PasswordResetToken(models.Model):
    """Token for password reset functionality"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.email}"

