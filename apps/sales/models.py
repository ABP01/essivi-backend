from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Product(models.Model):
    CATEGORY_CHOICES = (
        ('water', 'Eau'),
        ('drink', 'Boisson'),
        ('other', 'Autre'),
    )

    UNIT_CHOICES = (
        ('sachet', 'Sachet'),
        ('bottle', 'Bouteille'),
        ('pack', 'Pack'),
        ('case', 'Caisse'),
    )

    name = models.CharField(max_length=100, unique=True, help_text="Nom du produit")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='water')
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='sachet')
    quantity_per_unit = models.IntegerField(default=1, help_text="Quantité par unité (ex: 12 pour un pack de 12)")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Prix en FCFA")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'

    def __str__(self):
        return f"{self.name} ({self.quantity_per_unit} x {self.unit}) - {self.price} FCFA"

    def save(self, *args, **kwargs):
        if self.image and not self.image.name.endswith('.webp'):
            self.image = compress_image(self.image)
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    commande = models.ForeignKey('Commande', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Article de commande'
        verbose_name_plural = 'Articles de commande'

    def __str__(self):
        return f"{self.quantity} x {self.product.name} - {self.total_price} FCFA"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

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
    date_souhaitee = models.DateTimeField(default=timezone.now, help_text="Date souhaitée pour la livraison")
    delivery_latitude = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text="Latitude du lieu de livraison souhaité"
    )
    delivery_longitude = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text="Longitude du lieu de livraison souhaité"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commande {self.id} - {self.client}"

    @property
    def total_amount(self):
        """Calculate total from order items"""
        return sum(item.total_price for item in self.items.all())

    def update_total_amount(self):
        """Update the montant field based on order items"""
        self.montant = self.total_amount
        self.save(update_fields=['montant'])

from core.utils.images import compress_image

class Livraison(models.Model):
    tournee = models.ForeignKey('logistics.Tournee', on_delete=models.CASCADE)
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    
    # Delivery status
    statut_livraison = models.CharField(
        max_length=20,
        choices=[
            ('assigned', 'Assignée'),
            ('en_route', 'En route'),
            ('arriving', 'Arrive bientôt'),
            ('delivered', 'Livrée'),
        ],
        default='assigned',
        help_text="Statut de progression de la livraison"
    )
    
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
    photo_preuve = models.ImageField(upload_to='livraisons/', null=True, blank=True)
    signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    preuve_validee = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.photo_preuve and not self.photo_preuve.name.endswith('.webp'):
            self.photo_preuve = compress_image(self.photo_preuve)
        if self.signature and not self.signature.name.endswith('.webp'):
            self.signature = compress_image(self.signature)
        super().save(*args, **kwargs)

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

class AgentRating(models.Model):
    """Client ratings and feedback for delivery agents"""
    client = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='agent_ratings')
    agent = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='received_ratings')
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='agent_ratings')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['client', 'commande']  # One rating per client per order
    
    def __str__(self):
        return f"Rating {self.rating}/5 by {self.client} for {self.agent}"


