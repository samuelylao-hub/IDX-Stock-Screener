class NotificationService:
    def __init__(self, providers=None):
        self.providers = providers or []

    def send_report(self, message: str) -> None:
        for provider in self.providers:
            provider.send(message)

    def send_alerts(self, alerts) -> None:
        if not alerts:
            return

        lines = ["IDX SIGNAL ALERT", ""]

        for alert in alerts:
            lines.extend([
                f"[{alert.level}] {alert.symbol}",
                alert.message,
                "",
            ])

        message = "\n".join(lines)

        for provider in self.providers:
            provider.send(message)
