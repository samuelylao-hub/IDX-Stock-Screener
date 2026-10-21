"""Seed kalender BEI 2027 berdasarkan pengumuman September 2026.

Referensi: Peng-00169/BEI.POP/09-2026.
Jalankan dari root repository dengan:
python scripts/seed_market_calendar_2027.py

Perbarui jika BEI menerbitkan revisi kalender.
"""
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.database import get_connection


HOLIDAYS = {
    date(2027, 1, 1): "Tahun Baru Masehi",
    date(2027, 1, 5): "Isra Mikraj Nabi Muhammad SAW",
    date(2027, 2, 5): "Cuti Bersama Tahun Baru Imlek",
    date(2027, 3, 8): "Hari Suci Nyepi",
    date(2027, 3, 9): "Cuti Bersama Idul Fitri",
    date(2027, 3, 10): "Hari Raya Idul Fitri",
    date(2027, 3, 11): "Hari Raya Idul Fitri",
    date(2027, 3, 12): "Cuti Bersama Idul Fitri",
    date(2027, 3, 15): "Cuti Bersama Idul Fitri",
    date(2027, 3, 25): "Cuti Bersama Wafat Yesus Kristus",
    date(2027, 3, 26): "Wafat Yesus Kristus",
    date(2027, 5, 6): "Kenaikan Yesus Kristus",
    date(2027, 5, 17): "Idul Adha",
    date(2027, 5, 18): "Cuti Bersama Idul Adha",
    date(2027, 5, 19): "Cuti Bersama Waisak",
    date(2027, 5, 20): "Hari Raya Waisak",
    date(2027, 6, 1): "Hari Lahir Pancasila",
    date(2027, 8, 17): "Hari Kemerdekaan Republik Indonesia",
    date(2027, 12, 24): "Cuti Bersama Natal",
    date(2027, 12, 31): "Libur Bursa akhir tahun",
}


def main():
    start = date(2027, 1, 1)
    end = date(2027, 12, 31)

    rows = []
    day = start
    while day <= end:
        trading = day.weekday() < 5 and day not in HOLIDAYS
        rows.append((day, trading, HOLIDAYS.get(day)))
        day += timedelta(days=1)

    assert len(rows) == 365, f"Jumlah tanggal salah: {len(rows)}"
    assert len(HOLIDAYS) == 20, f"Jumlah libur salah: {len(HOLIDAYS)}"
    assert sum(1 for _, trading, _ in rows if trading) == 241

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO market_calendar
                    (calendar_date, is_trading_day, holiday_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (calendar_date) DO UPDATE SET
                    is_trading_day = EXCLUDED.is_trading_day,
                    holiday_name = EXCLUDED.holiday_name
                """,
                rows,
            )

            cursor.execute(
                """
                SELECT
                    COUNT(*),
                    COUNT(*) FILTER (WHERE is_trading_day = TRUE),
                    COUNT(*) FILTER (WHERE is_trading_day = FALSE),
                    COUNT(*) FILTER (WHERE holiday_name IS NOT NULL)
                FROM market_calendar
                WHERE calendar_date BETWEEN %s AND %s
                """,
                (start, end),
            )
            result = cursor.fetchone()

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    total, trading, closed, named_holidays = result

    print("===== VERIFIKASI KALENDER BEI 2027 =====")
    print(f"Total tanggal          : {total}")
    print(f"Hari bursa             : {trading}")
    print(f"Hari non-bursa         : {closed}")
    print(f"Libur dengan nama      : {named_holidays}")

    if (total, trading, closed, named_holidays) != (365, 241, 124, 20):
        raise SystemExit("GAGAL: hasil database tidak sesuai target.")

    print("SEED BERHASIL.")


if __name__ == "__main__":
    main()
