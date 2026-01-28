from django.contrib import admin
from .models import Product, OrderItem, Commande, Livraison, Notification, BottleReturn, Subscription, FAQ, AgentRating

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit', 'quantity_per_unit', 'price', 'is_active']
    list_filter = ['category', 'unit', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'category', 'description', 'image')
        }),
        ('Configuration', {
            'fields': ('unit', 'quantity_per_unit', 'price', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['commande', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['product__category']
    search_fields = ['commande__id', 'product__name']
    readonly_fields = ['total_price']

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'agent', 'statut', 'montant', 'date_souhaitee', 'created_at']
    list_filter = ['statut', 'date_souhaitee', 'created_at']
    search_fields = ['id', 'client__username', 'agent__username']
    readonly_fields = ['created_at', 'updated_at', 'montant']
    inlines = [OrderItemInline]

    fieldsets = (
        ('Informations générales', {
            'fields': ('client', 'agent', 'statut')
        }),
        ('Détails', {
            'fields': ('montant', 'date_souhaitee')
        }),
        ('Localisation', {
            'fields': ('delivery_latitude', 'delivery_longitude'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Livraison)
class LivraisonAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'tournee', 'statut_livraison', 'timestamp']
    list_filter = ['statut_livraison', 'timestamp']
    search_fields = ['id', 'client__username', 'tournee__agent__username']
    readonly_fields = ['timestamp']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'type', 'read', 'created_at']
    list_filter = ['type', 'read', 'created_at']
    search_fields = ['user__username', 'title', 'message']

@admin.register(BottleReturn)
class BottleReturnAdmin(admin.ModelAdmin):
    list_display = ['client', 'bottle_count', 'credit_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['client__username']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['client', 'plan', 'bottle_size', 'quantity', 'status', 'next_delivery']
    list_filter = ['plan', 'bottle_size', 'status']
    search_fields = ['client__username']

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    ordering = ['order']

@admin.register(AgentRating)
class AgentRatingAdmin(admin.ModelAdmin):
    list_display = ['client', 'agent', 'commande', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['client__username', 'agent__username']
