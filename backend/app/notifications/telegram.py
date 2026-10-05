import requests

from backend.app.notifications.base import NotificationProvider


class TelegramNotificationProvider(NotificationProvider):
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        response = requests.post(
            url,
            json={
                "chat_id": self.chat_id,
                "text": message,
            },
            timeout=15,
        )

        response.raise_for_status()
