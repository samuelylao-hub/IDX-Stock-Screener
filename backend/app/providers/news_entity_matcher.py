import re


LEGAL_SUFFIXES = {
    "pt",
    "tbk",
    "persero",
}


def normalize_entity_text(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_company_name(value: str) -> str:
    normalized = normalize_entity_text(value)

    words = [
        word
        for word in normalized.split()
        if word not in LEGAL_SUFFIXES
    ]

    return " ".join(words)


def matches_stock_entity(
    text: str,
    symbol: str,
    company_name: str,
) -> bool:
    normalized_text = normalize_entity_text(text)
    normalized_symbol = normalize_entity_text(symbol)
    normalized_company = normalize_company_name(
        company_name
    )

    symbol_pattern = (
        rf"(?<![a-z0-9]){re.escape(normalized_symbol)}"
        rf"(?![a-z0-9])"
    )

    if re.search(symbol_pattern, normalized_text):
        return True

    if (
        normalized_company
        and normalized_company in normalized_text
    ):
        return True

    return False


def find_matching_symbols(
    text: str,
    stocks,
) -> list[str]:
    matches = []

    for stock in stocks:
        symbol = stock[1]
        company_name = stock[2]

        if matches_stock_entity(
            text,
            symbol,
            company_name,
        ):
            matches.append(symbol)

    return matches
