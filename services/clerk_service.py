import requests
from django.conf import settings


class ClerkService:
    def __init__(self):
        self.api_url = settings.CLERK_API_URL
        self.secret_key = settings.CLERK_SECRET_KEY

    def retrieve_user(self, user_id: str) -> dict | None:
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        response = requests.get(f"{self.api_url}/v1/users/{user_id}", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
