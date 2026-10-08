import sys; sys.path.insert(0, "."); from backend.app.database import get_connection

groups = {
    "PRAJOGO": {
        "BRPT": "Barito Pacific Tbk",
        "TPIA": "Chandra Asri Pacific Tbk",
        "BREN": "Barito Renewables Energy Tbk",
        "CUAN": "Petrindo Jaya Kreasi Tbk",
        "PTRO": "Petrosea Tbk",
        "CDIA": "Chandra Daya Investasi Tbk",
    },
    "BAKRIE": {
        "BNBR": "Bakrie & Brothers Tbk",
        "BUMI": "Bumi Resources Tbk",
        "ENRG": "Energi Mega Persada Tbk",
        "UNSP": "Bakrie Sumatera Plantations Tbk",
        "VKTR": "VKTR Teknologi Mobilitas Tbk",
        "VIVA": "Visi Media Asia Tbk",
        "MDIA": "Intermedia Capital Tbk",
        "ALII": "Ancara Logistics Indonesia Tbk",
        "JGLE": "Graha Andrasentra Propertindo Tbk",
    },
    "HAJI_ISAM": {
        "JARR": "Jhonlin Agro Raya Tbk",
        "TEBE": "Dana Brata Luhur Tbk",
        "PACK": "Abadi Nusantara Hijau Investama Tbk",
        "BYAN": "Bayan Resources Tbk",
    },
    "HAJI_ISAM_FAMILY": {
        "PGUN": "Pradiksi Gunatama Tbk",
    },
}

conn = get_connection()
cur = conn.cursor()

for group, stocks in groups.items():
    for symbol, company_name in stocks.items():
        cur.execute(
            """
            INSERT INTO stocks
                (symbol, company_name, is_active, thematic_group, intraday_enabled)
            VALUES
                (%s, %s, TRUE, %s, TRUE)
            ON CONFLICT (symbol)
            DO UPDATE SET
                company_name = EXCLUDED.company_name,
                is_active = TRUE,
                thematic_group = EXCLUDED.thematic_group,
                intraday_enabled = TRUE,
                updated_at = NOW()
            """,
            (symbol, company_name, group),
        )

conn.commit()
cur.close()
conn.close()

print("THEMATIC UNIVERSE UPDATED")
