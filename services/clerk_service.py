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

    def create_new_session(self, user_id: str) -> dict | None:
        response = requests.post(
            f"{self.api_url}/v1/sessions",
            headers={
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json",
            },
            json={"user_id": user_id},
        )
        if response.status_code in [200, 201]:
            return response.json()
        return None

    def create_session_token(self, session_id: str) -> dict | None:
        response = requests.post(
            f"{self.api_url}/v1/sessions/{session_id}/tokens",
            headers={
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json",
            },
        )
        if response.status_code in [200, 201]:
            return response.json()
        return None
