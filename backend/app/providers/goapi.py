import os


class GoAPIProvider:
    @property
    def name(self) -> str:
        return "goapi"

    def is_available(self) -> bool:
        return bool(os.getenv("GOAPI_API_KEY"))