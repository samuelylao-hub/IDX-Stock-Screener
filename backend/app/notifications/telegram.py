import requests

from backend.app.notifications.base import NotificationProvider


class TelegramNotificationProvider(NotificationProvider):
    MAX_MESSAGE_LENGTH = 4000

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def _send(self, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        response = requests.post(
            url,
            json={
                "chat_id": self.chat_id,
                "text": message,
            },
            timeout=20,
        )
        response.raise_for_status()

    def send(self, message: str) -> None:
        if not message:
            return

        chunks = []
        current = ""

        for line in message.splitlines(keepends=True):
            if len(current) + len(line) > self.MAX_MESSAGE_LENGTH:
                if current:
                    chunks.append(current)
                    current = ""

                while len(line) > self.MAX_MESSAGE_LENGTH:
                    chunks.append(line[:self.MAX_MESSAGE_LENGTH])
                    line = line[self.MAX_MESSAGE_LENGTH:]

            current += line

        if current:
            chunks.append(current)

        for chunk in chunks:
            self._send(chunk)
