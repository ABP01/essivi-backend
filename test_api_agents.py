
import requests
import json

BASE_URL = "http://localhost:8000/api"

def get_token():
    url = f"{BASE_URL}/token/"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Error getting token: {response.text}")
        return None

def list_agents(token):
    url = f"{BASE_URL}/users/agents/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error fetching agents: {response.status_code} {response.text}")

if __name__ == "__main__":
    token = get_token()
    if token:
        list_agents(token)
