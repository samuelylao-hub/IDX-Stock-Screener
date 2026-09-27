import os

from dotenv import load_dotenv

from backend.app.providers.index_alpha import IndexAlphaProvider


load_dotenv()


def test_index_alpha_provider_available():
    api_key = os.getenv("INDEX_ALPHA_API_KEY")

    provider = IndexAlphaProvider()

    assert bool(api_key) == provider.is_available()