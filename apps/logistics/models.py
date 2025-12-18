from django.db import models

class Tricycle(models.Model):
    STATUS_CHOICES = (
        ('active', 'Actif'),
        ('maintenance', 'En Maintenance'),
        ('inactive', 'Inactif'),
    )
    immatriculation = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.immatriculation

class Tournee(models.Model):
    # Agent reference will be string to avoid circular import issues if possible, 
    # but since Agent is in Users app, we reference 'users.CustomUser' or 'users.AgentProfile'
    # The requirement says `agent` (ForeignKey). 
    agent = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='tournees')
    tricycle = models.ForeignKey(Tricycle, on_delete=models.CASCADE, related_name='tournees', null=True, blank=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    stock_initial = models.IntegerField(default=0)
    stock_retour = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Tournée {self.id} - {self.agent}"
