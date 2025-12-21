import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rest_framework.test import APIClient

c = APIClient()
r = c.post('/api/token/', {'username':'admin','password':'password'}, format='json')
print('token_response', r.status_code, getattr(r, 'data', r.content))
if r.status_code == 200:
    access = r.data.get('access')
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    s = c.get('/api/dashboard/stats/')
    print('stats', s.status_code, getattr(s, 'data', s.content))
else:
    print('failed to get token')
