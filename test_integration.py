import requests
import unittest

class APITests(unittest.TestCase):
    BASE_URL = 'http://localhost:8000/api'

    def test_users_endpoint(self):
        response = requests.get(f'{self.BASE_URL}/users/users/')
        # Should return 401 unauthorized without auth
        self.assertEqual(response.status_code, 401)

    def test_login_endpoint(self):
        # Test with invalid credentials
        data = {'username': 'invalid', 'password': 'invalid'}
        response = requests.post(f'{self.BASE_URL}/users/auth/login/', json=data)
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()