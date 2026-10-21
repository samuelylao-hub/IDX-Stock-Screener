from datetime import date
from collections import defaultdict

from psycopg import sql
from backend.app.database import get_connection
from backend.app.focused_universe import FOCUSED_UNIVERSE


def main():
    universe = list(dict.fromkeys(FOCUSED_UNIVERSE))
    print("=== SIMULASI OFFLINE: FOCUSED UNIVERSE ===")
    print(f"Tanggal lokal simulasi : {date.today()}")
    print(f"Jumlah ticker unik     : {len(universe)}")
    print("Mode                   : READ ONLY; tidak ada API eksternal")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            schema = defaultdict(set)
            for table, column in cur.fetchall():
                schema[table].add(column)

            if "stocks" not in schema:
                raise RuntimeError("Tabel stocks tidak ditemukan.")
            if not {"id", "symbol"}.issubset(schema["stocks"]):
                raise RuntimeError("Kolom stocks.id/symbol tidak sesuai.")

            cur.execute("SELECT id, UPPER(symbol) FROM stocks")
            stock_ids = {symbol: stock_id for stock_id, symbol in cur.fetchall()}
            mapped = [s for s in universe if s.upper() in stock_ids]
            print(f"Ticker terdaftar DB    : {len(mapped)}/{len(universe)}")

            def find_table(candidates):
                for name in candidates:
                    cols = schema.get(name, set())
                    date_col = next(
                        (c for c in ("trade_date", "calendar_date", "date")
                         if c in cols), None
                    )
                    if "stock_id" in cols and date_col:
                        return name, date_col
                return None, None

            price_table, price_date = find_table(["stock_prices"])
            foreign_table, foreign_date = find_table(["foreign_daily_flow"])
            broker_candidates = sorted(
                name for name, cols in schema.items()
                if "broker" in name.lower()
                and "stock_id" in cols
                and any(c in cols for c in ("trade_date", "date"))
            )
            broker_table, broker_date = find_table(broker_candidates)

            def coverage(table, date_col, label):
                if not table:
                    print(f"\n{label}: TABEL TIDAK DITEMUKAN")
                    return set(), None

                query = sql.SQL("""
                    SELECT stock_id, MAX({}) AS latest_date
                    FROM {}
                    GROUP BY stock_id
                """).format(sql.Identifier(date_col), sql.Identifier(table))
                with conn.cursor() as c:
                    c.execute(query)
                    latest_by_id = dict(c.fetchall())

                covered = {
                    symbol for symbol in mapped
                    if stock_ids[symbol.upper()] in latest_by_id
                }
                dates = [
                    latest_by_id[stock_ids[s.upper()]]
                    for s in covered
                ]
                newest = max(dates) if dates else None
                on_newest = {
                    s for s in covered
                    if latest_by_id[stock_ids[s.upper()]] == newest
                } if newest else set()

                print(f"\n{label}: {table}")
                print(f"  Tanggal terbaru per saham : {newest}")
                print(f"  Saham dengan data         : {len(covered)}/{len(universe)}")
                print(f"  Saham pada tanggal terbaru: {len(on_newest)}/{len(universe)}")
                return covered, newest

            prices, price_latest = coverage(
                price_table, price_date, "DATA HARGA"
            )
            foreign, foreign_latest = coverage(
                foreign_table, foreign_date, "FOREIGN FLOW"
            )
            broker, broker_latest = coverage(
                broker_table, broker_date, "BROKER FLOW"
            )

    print("\n=== SIMULASI BATAS INDEX ALPHA: 5 UNIT ===")
    # Ini simulasi kapasitas, bukan klaim bahwa ticker tersebut telah dipanggil.
    offset = date.today().toordinal() % len(universe)
    rotated = universe[offset:] + universe[:offset]
    selected = rotated[:5]
    print("Contoh 5 ticker untuk jatah provider:")
    print(", ".join(selected))
    print("Kuota simulasi terpakai : 5/5 unit maksimum")

    print("\n=== KONDISI DATA UNTUK SCREENING ===")
    price_only = prices - foreign - broker
    with_price = prices
    with_some_flow = prices & (foreign | broker)
    with_both_flows = prices & foreign & broker

    print(f"Saham dengan data harga                    : {len(with_price)}")
    print(f"Harga + minimal satu jenis flow             : {len(with_some_flow)}")
    print(f"Harga + foreign dan broker flow             : {len(with_both_flows)}")
    print(f"Harga ada, kedua flow tidak tersedia        : {len(price_only)}")
    print("\nCatatan: cakupan data tidak sama dengan sinyal valid.")
    print("Kelayakan sinyal tetap bergantung pada freshness,")
    print("riwayat, kualitas data, dan aturan Signal Fusion.")


if __name__ == "__main__":
    main()
