from django.db import models

class Commande(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('validated', 'Validée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    )
    
    client = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='commandes_client')
    # Agent might be null initially
    agent = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes_agent')
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_souhaitee = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commande {self.id} - {self.client}"

class Livraison(models.Model):
    tournee = models.ForeignKey('logistics.Tournee', on_delete=models.CASCADE)
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    gps_lat = models.FloatField(null=True, blank=True)
    gps_lng = models.FloatField(null=True, blank=True)
    photo_preuve = models.ImageField(upload_to='livraisons/', null=True, blank=True)
    signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Livraison {self.id} - {self.client}"
