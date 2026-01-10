from rest_framework import serializers
from .models import CustomUser, AgentProfile, ClientProfile, UserPreferences

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'is_active']
        read_only_fields = ['id']

from django.contrib.auth.password_validation import validate_password
from django.core import exceptions

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'email', 'role', 'phone_number', 'first_name', 'last_name']

    def validate_password(self, value):
        try:
            validate_password(value)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def create(self, validated_data):
        # create user and set optional first/last name when provided
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            role=validated_data.get('role', 'client'),
            phone_number=validated_data.get('phone_number')
        )
        fn = validated_data.get('first_name')
        ln = validated_data.get('last_name')
        if fn:
            user.first_name = fn
        if ln:
            user.last_name = ln
        if fn or ln:
            user.save()
        # Automatically create related profile based on role
        role = validated_data.get('role', 'client')
        if role == 'client':
            # create a minimal ClientProfile so frontend can immediately access profile data
            from .models import ClientProfile
            # prefer various incoming field names for store name / owner / address
            data = self.initial_data if hasattr(self, 'initial_data') else {}
            store = data.get('storeName') or data.get('store_name') or data.get('company') or data.get('nom_point_vente') or user.username
            owner = data.get('ownerName') or data.get('owner_name') or data.get('owner') or data.get('nom_proprietaire') or ''
            addr = data.get('address') or data.get('adresse') or data.get('location') or ''
            gps_lat = data.get('gps_lat') or data.get('lat')
            gps_lng = data.get('gps_lng') or data.get('lng')

            defaults = {'nom_point_vente': store}
            if owner:
                defaults['nom_proprietaire'] = owner
            if addr:
                defaults['adresse'] = addr
            if gps_lat is not None:
                try:
                    defaults['gps_lat'] = float(gps_lat)
                except Exception:
                    pass
            if gps_lng is not None:
                try:
                    defaults['gps_lng'] = float(gps_lng)
                except Exception:
                    pass

            ClientProfile.objects.get_or_create(user=user, defaults=defaults)
        elif role == 'agent':
            from .models import AgentProfile
            # pull extra fields from initial_data when available
            data = self.initial_data if hasattr(self, 'initial_data') else {}
            ident = data.get('identificationNumber') or data.get('identification_number') or data.get('ident')
            tr_plate = data.get('tricycle_plate') or data.get('tricyclePlate') or data.get('tricycle_plate')

            defaults = {}
            if ident:
                defaults['identification_number'] = ident
            if tr_plate:
                defaults['tricycle_plate'] = tr_plate

            AgentProfile.objects.get_or_create(user=user, defaults=defaults)

        return user

class AgentProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    firstname = serializers.SerializerMethodField()
    lastname = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentProfile
        fields = ['id', 'user', 'firstname', 'lastname', 'status', 'identification_number', 'tricycle_plate', 'latitude', 'longitude', 'date_embauche', 'tricycle', 'zone_assignee']

    def get_firstname(self, obj):
        try:
            return obj.user.first_name
        except Exception:
            return ''

    def get_lastname(self, obj):
        try:
            return obj.user.last_name
        except Exception:
            return ''

    def get_status(self, obj):
        try:
            # prefer explicit agent status if present on profile, otherwise map user's active flag
            if hasattr(obj, 'status') and obj.status:
                return obj.status
            return 'active' if getattr(obj.user, 'is_active', True) else 'inactive'
        except Exception:
            return 'inactive'

    def _extract_name_from_input(self):
        """
        Helper to extract possible first/last name values from the incoming request payload.
        Accepts multiple naming variants that the frontend might send.
        """
        data = {}
        try:
            raw = self.initial_data if hasattr(self, 'initial_data') and self.initial_data else {}
            # support nested user payload
            u = raw.get('user') if isinstance(raw.get('user'), dict) else {}
            # first name variants
            first = raw.get('first_name') or raw.get('firstname') or raw.get('first') or u.get('first_name') or u.get('firstname') or None
            last = raw.get('last_name') or raw.get('lastname') or raw.get('last') or u.get('last_name') or u.get('lastname') or None
            if first:
                data['first_name'] = first
            if last:
                data['last_name'] = last
        except Exception:
            pass
        return data

    def update(self, instance, validated_data):
        # update profile fields normally
        instance = super().update(instance, validated_data)
        # propagate any provided first/last name to the related user
        try:
            names = self._extract_name_from_input()
            if names:
                user = instance.user
                updated = False
                if 'first_name' in names and names['first_name'] and user.first_name != names['first_name']:
                    user.first_name = names['first_name']
                    updated = True
                if 'last_name' in names and names['last_name'] and user.last_name != names['last_name']:
                    user.last_name = names['last_name']
                    updated = True
                if updated:
                    user.save()
        except Exception:
            pass
        return instance

    def create(self, validated_data):
        # create profile normally
        instance = super().create(validated_data)
        # propagate names if provided in payload
        try:
            names = self._extract_name_from_input()
            if names:
                user = instance.user
                if 'first_name' in names and names['first_name']:
                    user.first_name = names['first_name']
                if 'last_name' in names and names['last_name']:
                    user.last_name = names['last_name']
                user.save()
        except Exception:
            pass
        return instance

class ClientProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    storeName = serializers.SerializerMethodField()
    ownerName = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    
    class Meta:
        model = ClientProfile
        fields = ['id', 'user', 'nom_point_vente', 'storeName', 'nom_proprietaire', 'ownerName', 'adresse', 'address', 'gps_lat', 'gps_lng', 'lat', 'lng', 'solde']

    def get_storeName(self, obj):
        return obj.nom_point_vente or ''

    def get_ownerName(self, obj):
        return obj.nom_proprietaire or (obj.user.first_name + ' ' + obj.user.last_name).strip() or ''

    def get_address(self, obj):
        return obj.adresse or ''

    def get_lat(self, obj):
        return obj.gps_lat if obj.gps_lat is not None else None

    def get_lng(self, obj):
        return obj.gps_lng if obj.gps_lng is not None else None

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint"""
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value

class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user preferences"""
    class Meta:
        model = UserPreferences
        fields = ['id', 'notifications_enabled', 'email_notifications', 'sms_notifications', 'language', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


