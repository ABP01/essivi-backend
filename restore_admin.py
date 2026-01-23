#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.users.models import CustomUser

def restore_admin():
    username = 'admin'
    password = 'admin'
    email = 'admin@essivi.com'

    try:
        user = CustomUser.objects.get(username=username)
        user.set_password(password)
        user.save()
        print(f"✅ Password for user '{username}' has been updated to '{password}'.")
    except CustomUser.DoesNotExist:
        CustomUser.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role='admin', 
            phone_number='+228 90 00 00 00'
        )
        print(f"✅ Created new superuser '{username}' with password '{password}'.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    restore_admin()
