from datetime import date
import html
import re

from curl_cffi import requests


URL = "https://www.idx.co.id/id/perusahaan-tercatat/suspensi-6-bulan/"

MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "Mei": 5, "Jun": 6, "Jul": 7, "Agu": 8,
    "Sep": 9, "Okt": 10, "Nov": 11, "Des": 12,
}


def clean_cell(value):
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_date(value):
    value = clean_cell(value)

    match = re.search(
        r"(\d{1,2})-([A-Za-z]+)-(\d{2,4})",
        value,
    )

    if not match:
        return None

    day = int(match.group(1))
    month = MONTHS.get(match.group(2).title())
    year = int(match.group(3))

    if year < 100:
        year += 2000

    if not month:
        return None

    return date(year, month, day)


def fetch_long_suspensions():
    response = requests.get(
        URL,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.idx.co.id/",
        },
        impersonate="chrome",
        timeout=30,
    )

    response.raise_for_status()

    source = html.unescape(response.text)

    source = source.replace(r"\u003C", "<")
    source = source.replace(r"\u003c", "<")
    source = source.replace(r"\u003E", ">")
    source = source.replace(r"\u003e", ">")
    source = source.replace(r"\u002F", "/")

    rows = re.findall(
        r"<tr\b[^>]*>(.*?)</tr>",
        source,
        flags=re.I | re.S,
    )

    result = {}

    for raw_row in rows:
        cells = re.findall(
            r"<td\b[^>]*>(.*?)</td>",
            raw_row,
            flags=re.I | re.S,
        )

        cells = [clean_cell(cell) for cell in cells]

        if len(cells) < 7:
            continue

        symbol = cells[1].upper()

        if not re.fullmatch(r"[A-Z0-9]{3,5}", symbol):
            continue

        suspension_date = parse_date(cells[6])

        if suspension_date is None:
            continue

        result[symbol] = {
            "symbol": symbol,
            "company_name": cells[2],
            "sector": cells[3],
            "board": cells[4],
            "suspension_date": suspension_date,
        }

    return list(result.values())


def sync():
    """Mark listed long-suspended symbols in the local stocks table.

    This deliberately updates only symbols present in a successfully parsed IDX
    response. It does not clear older SUSPENDED statuses when a symbol vanishes
    from the page, because absence alone is not sufficient proof that trading
    has resumed.
    """
    rows = fetch_long_suspensions()
    if not rows:
        raise RuntimeError(
            "IDX suspension page returned no parsed rows; refusing to change statuses."
        )

    from backend.app.database import get_connection

    updated = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for row in rows:
                reason = (
                    f"IDX suspensi 6 bulan sejak "
                    f"{row['suspension_date'].isoformat()}"
                )
                cur.execute(
                    """
                    UPDATE stocks
                    SET market_status = 'SUSPENDED',
                        risk_flags = '["SUSPENDED"]'::jsonb,
                        status_reason = %s,
                        updated_at = NOW()
                    WHERE symbol = %s
                    """,
                    (reason, row["symbol"]),
                )
                updated += cur.rowcount
        conn.commit()

    print(
        f"IDX suspension sync complete: parsed={len(rows)}, "
        f"stocks_updated={updated}"
    )
    return updated


if __name__ == "__main__":
    rows = fetch_long_suspensions()

    print(f"IDX SUSPENSION UNIQUE = {len(rows)}")

    print("SAMPLE:")
    for row in rows[:10]:
        print(
            row["symbol"],
            "|",
            row["board"],
            "|",
            row["suspension_date"],
        )
