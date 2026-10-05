class NotificationService:
    def __init__(self, providers=None):
        self.providers = providers or []

    def send_report(self, message: str) -> None:
        for provider in self.providers:
            provider.send(message)
