"""
Appwrite Phone Authentication Backend Integration pour Django
Gère l'authentification par téléphone (OTP) avec Appwrite
"""
import os
import requests
from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.services.account import Account
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging

# Initialiser le client Appwrite
def get_appwrite_client():
    """Retourne un client Appwrite configuré"""
    client = Client()
    client.set_endpoint(os.getenv('APPWRITE_ENDPOINT', 'https://cloud.appwrite.io/v1'))
    client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
    client.set_key(os.getenv('APPWRITE_API_KEY'))
    return client

# Initialiser Firebase Admin SDK
def initialize_firebase():
    """Initialise Firebase Admin SDK si pas déjà fait"""
    if not firebase_admin._apps:
        # Utiliser les credentials par défaut (service account)
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_phone_otp(request):
    """
    Envoie un code OTP au numéro de téléphone fourni
    POST /api/auth/appwrite/send-otp/
    Body: {"phone": "+22890123456"}
    """
    phone = request.data.get('phone')
    
    if not phone:
        return Response(
            {'error': 'Le numéro de téléphone est requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        client = get_appwrite_client()
        users_service = Users(client)
        
        # Créer un token de téléphone (envoie l'OTP)
        # Appwrite gère l'envoi automatique du SMS
        result = users_service.create_phone_token(
            user_id='unique()',
            phone=phone
        )
        
        return Response({
            'success': True,
            'message': 'Code OTP envoyé avec succès',
            'user_id': result['userId']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'envoi de l\'OTP: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_phone_otp(request):
    """
    Vérifie le code OTP et crée une session
    POST /api/auth/appwrite/verify-otp/
    Body: {"user_id": "...", "otp": "123456"}
    """
    user_id = request.data.get('user_id')
    otp = request.data.get('otp')
    
    if not user_id or not otp:
        return Response(
            {'error': 'user_id et otp sont requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Vérifier l'OTP avec Appwrite
        client = get_appwrite_client()
        client.set_jwt(request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', ''))
        
        account = Account(client)
        session = account.update_phone_session(
            user_id=user_id,
            secret=otp
        )
        
        return Response({
            'success': True,
            'message': 'Code OTP vérifié avec succès',
            'session': session
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Code OTP invalide: {str(e)}'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_appwrite_user(request):
    """
    Récupère les informations de l'utilisateur Appwrite
    GET /api/auth/appwrite/user/
    Header: Authorization: Bearer <appwrite_jwt>
    """
    try:
        # Récupérer le JWT Appwrite de l'en-tête
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        jwt_token = auth_header.replace('Bearer ', '')
        
        if not jwt_token:
            return Response(
                {'error': 'Token JWT requis'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Créer un client avec le JWT de l'utilisateur
        client = Client()
        client.set_endpoint(os.getenv('APPWRITE_ENDPOINT'))
        client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
        client.set_jwt(jwt_token)
        
        account = Account(client)
        user = account.get()
        
        return Response({
            'success': True,
            'user': user
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur récupération utilisateur: {str(e)}'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_fcm_token(request):
    """
    Sauvegarde le token FCM pour les notifications push
    POST /api/auth/appwrite/save-fcm-token/
    Body: {"fcm_token": "..."}
    """
    fcm_token = request.data.get('fcm_token')
    
    if not fcm_token:
        return Response(
            {'error': 'fcm_token est requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Sauvegarder le token dans les préférences utilisateur Appwrite
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        jwt_token = auth_header.replace('Bearer ', '')
        
        client = Client()
        client.set_endpoint(os.getenv('APPWRITE_ENDPOINT'))
        client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
        client.set_jwt(jwt_token)
        
        account = Account(client)
        account.update_prefs(prefs={
            'fcm_token': fcm_token,
            'push_enabled': True
        })
        
        return Response({
            'success': True,
            'message': 'Token FCM sauvegardé avec succès'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur sauvegarde token: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_push_notification(request):
    """
    Envoie une notification push via Firebase Cloud Messaging V1
    POST /api/auth/appwrite/send-push/
    Body: {
        "fcm_token": "device_token",
        "title": "Titre de la notification",
        "message": "Message",
        "data": {"key": "value"}
    }
    """
    fcm_token = request.data.get('fcm_token')
    title = request.data.get('title')
    message = request.data.get('message')
    data = request.data.get('data', {})
    
    if not all([fcm_token, title, message]):
        return Response(
            {'error': 'fcm_token, title et message sont requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Initialiser Firebase
        initialize_firebase()
        
        # Créer le message FCM
        fcm_message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            data=data,
            token=fcm_token,
        )
        
        # Envoyer la notification
        response = messaging.send(fcm_message)
        
        return Response({
            'success': True,
            'message': 'Notification envoyée avec succès',
            'message_id': response
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur envoi notification: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Vérifie que la connexion Appwrite fonctionne
    GET /api/auth/appwrite/health/
    """
    try:
        client = get_appwrite_client()
        # Test de connexion
        return Response({
            'success': True,
            'message': 'Connexion Appwrite OK',
            'endpoint': os.getenv('APPWRITE_ENDPOINT'),
            'project_id': os.getenv('APPWRITE_PROJECT_ID')
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur connexion Appwrite: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
