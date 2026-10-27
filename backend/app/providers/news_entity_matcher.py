
import re

LEGAL_SUFFIXES = {"pt", "tbk", "persero"}
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
    "forecast", "outlook", "target", "pemegang saham", "bisnis",
    "aksi korporasi", "rups", "tender", "penghentian perdagangan",
}

def normalize_entity_text(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def normalize_company_name(value: str) -> str:
    normalized = normalize_entity_text(value)
    return " ".join(word for word in normalized.split() if word not in LEGAL_SUFFIXES)

def has_market_relevance(text: str) -> bool:
    normalized = f" {normalize_entity_text(text)} "
    return any(
        f" {normalize_entity_text(term)} " in normalized
        for term in MARKET_TERMS
    )

def matches_stock_entity(text: str, symbol: str, company_name: str) -> bool:
    normalized_text = normalize_entity_text(text)
    normalized_symbol = normalize_entity_text(symbol)
    normalized_company = normalize_company_name(company_name)
    if not normalized_symbol:
        return False
    symbol_match = bool(re.search(
        rf"(?<![a-z0-9]){re.escape(normalized_symbol)}(?![a-z0-9])",
        normalized_text,
    ))
    company_match = bool(normalized_company and normalized_company in normalized_text)
    return (symbol_match or company_match) and has_market_relevance(normalized_text)

def find_matching_symbols(text: str, stocks) -> list[str]:
    return [
        stock[1] for stock in stocks
        if matches_stock_entity(text, stock[1], stock[2])
    ]
