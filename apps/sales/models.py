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
    montant = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
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
    preuve_validee = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Livraison {self.id} - {self.client}"

class Notification(models.Model):
    """User notifications for orders, deliveries, and system messages"""
    TYPE_CHOICES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )
    
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class BottleReturn(models.Model):
    """Track bottle return requests from clients"""
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('completed', 'Complété'),
        ('rejected', 'Rejeté'),
    )
    
    client = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='bottle_returns')
    bottle_count = models.IntegerField()
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bottle Return {self.id} - {self.client.username} ({self.bottle_count} bottles)"
    
    def save(self, *args, **kwargs):
        # Calculate credit amount based on bottle count (100 FCFA per bottle)
        if not self.credit_amount:
            self.credit_amount = self.bottle_count * 100
        super().save(*args, **kwargs)

class Subscription(models.Model):
    """Manage recurring subscriptions for clients"""
    PLAN_CHOICES = (
        ('hebdomadaire', 'Hebdomadaire'),
        ('bi_mensuel', 'Bi-mensuel'),
        ('mensuel', 'Mensuel'),
    )
    
    BOTTLE_SIZE_CHOICES = (
        ('5L', '5 Litres'),
        ('10L', '10 Litres'),
        ('20L', '20 Litres'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Actif'),
        ('paused', 'En pause'),
        ('cancelled', 'Annulé'),
    )
    
    client = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='mensuel')
    bottle_size = models.CharField(max_length=5, choices=BOTTLE_SIZE_CHOICES, default='20L')
    quantity = models.IntegerField(default=4)
    preferred_day = models.CharField(max_length=20, default='Lundi')
    time_slot = models.CharField(max_length=50, default='09:00 - 12:00')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    next_delivery = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Subscription {self.id} - {self.client.username} ({self.plan})"

class FAQ(models.Model):
    """Frequently Asked Questions for help center"""
    CATEGORY_CHOICES = (
        ('orders', 'Commandes'),
        ('delivery', 'Livraison'),
        ('payment', 'Paiement'),
        ('account', 'Compte'),
        ('other', 'Autre'),
    )
    
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
    
    def __str__(self):
        return self.question


