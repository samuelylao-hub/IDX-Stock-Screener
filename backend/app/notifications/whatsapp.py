import requests

from backend.app.notifications.base import NotificationProvider


class WhatsAppNotificationProvider(NotificationProvider):
    def __init__(self, api_url: str, access_token: str, phone_number_id: str):
        self.api_url = api_url
        self.access_token = access_token
        self.phone_number_id = phone_number_id

    def send(self, message: str) -> None:
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": self.phone_number_id,
                "type": "text",
                "text": {
                    "body": message,
                },
            },
            timeout=15,
        )

        response.raise_for_status()
