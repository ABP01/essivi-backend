"""
URLs pour l'authentification Appwrite
"""
from django.urls import path
from . import appwrite_views

urlpatterns = [
    # Authentication OTP/SMS
    path('send-otp/', appwrite_views.send_phone_otp, name='appwrite_send_otp'),
    path('verify-otp/', appwrite_views.verify_phone_otp, name='appwrite_verify_otp'),
    
    # User info
    path('user/', appwrite_views.get_appwrite_user, name='appwrite_get_user'),
    
    # Push notifications
    path('save-fcm-token/', appwrite_views.save_fcm_token, name='appwrite_save_fcm_token'),
    path('send-push/', appwrite_views.send_push_notification, name='appwrite_send_push'),
    
    # Health check
    path('health/', appwrite_views.health_check, name='appwrite_health'),
]
