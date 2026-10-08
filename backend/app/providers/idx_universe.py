from curl_cffi import requests


class IDXUniverseProvider:
    URL = "https://www.idx.co.id/primary/ListedCompany/GetCompanyProfiles"

    def fetch(self):
        response = requests.get(
            self.URL,
            params={
                "start": 0,
                "length": 9999,
            },
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan/",
            },
            impersonate="chrome",
            timeout=30,
        )
        response.raise_for_status()

        payload = response.json()
        rows = payload.get("data", [])

        result = []

        for row in rows:
            symbol = (row.get("KodeEmiten") or "").strip().upper()
            name = (row.get("NamaEmiten") or "").strip()

            if not symbol or not name:
                continue

            result.append(
                {
                    "symbol": symbol,
                    "company_name": name,
                    "sector": row.get("Sektor"),
                    "subsector": row.get("SubSektor"),
                }
            )

        return result
