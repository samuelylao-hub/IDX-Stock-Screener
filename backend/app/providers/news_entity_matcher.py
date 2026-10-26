import re


LEGAL_SUFFIXES = {"pt", "tbk", "persero"}

# Terms indicating a plausible capital-market, corporate, or economic impact.
# Deliberately exclude generic social, celebrity, and lifestyle coverage.
MARKET_TERMS = {
    "saham", "emiten", "bei", "bursa", "idx", "ipo", "listing",
    "delisting", "suspensi", "dividen", "laba", "rugi", "pendapatan",
    "keuangan", "kinerja", "kuartal", "semester", "laporan", "audit",
    "akuisisi", "merger", "divestasi", "investasi", "ekspansi",
    "pabrik", "produksi", "penjualan", "kontrak", "proyek", "utang",
    "obligasi", "rights issue", "stock split", "buyback", "takeover",
    "restrukturisasi", "pailit", "default", "kredit", "ekspor", "impor",
    "suku bunga", "inflasi", "rupiah", "nilai tukar", "tarif", "pajak",
    "regulasi", "ojk", "aturan", "ekonomi", "komoditas", "harga minyak",
    "harga batu bara", "harga nikel", "harga emas", "ekonomi global",
    "forecast", "outlook", "target", "dividen", "pemegang saham",
    "aksi korporasi", "rups", "tender", "penghentian perdagangan",
}


def normalize_entity_text(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^a-z0-9\\s]", " ", value)
    value = re.sub(r"\\s+", " ", value)
    return value.strip()


def normalize_company_name(value: str) -> str:
    normalized = normalize_entity_text(value)
    return " ".join(word for word in normalized.split() if word not in LEGAL_SUFFIXES)


def has_market_relevance(text: str) -> bool:
    normalized = normalize_entity_text(text)
    return any(
        normalize_entity_text(term) in normalized
        for term in MARKET_TERMS
    )


def matches_stock_entity(text: str, symbol: str, company_name: str) -> bool:
    normalized_text = normalize_entity_text(text)
    normalized_symbol = normalize_entity_text(symbol)
    normalized_company = normalize_company_name(company_name)

    if not normalized_symbol:
        return False

    symbol_pattern = rf"(?<![a-z0-9]){re.escape(normalized_symbol)}(?![a-z0-9])"
    symbol_match = bool(re.search(symbol_pattern, normalized_text))
    company_match = bool(normalized_company and normalized_company in normalized_text)
    return (symbol_match or company_match) and has_market_relevance(normalized_text)


def find_matching_symbols(text: str, stocks) -> list[str]:
    matches = []
    for stock in stocks:
        symbol, company_name = stock[1], stock[2]
        if matches_stock_entity(text, symbol, company_name):
            matches.append(symbol)
    return matches
