import os

import requests
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("INDEX_ALPHA_API_KEY")

if not api_key:
    raise RuntimeError("INDEX_ALPHA_API_KEY tidak ditemukan.")


response = requests.get(
    "https://api.indexalpha.id/usage",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    },
    timeout=15,
)

print("HTTP STATUS:", response.status_code)
print("RESPONSE:", response.text)