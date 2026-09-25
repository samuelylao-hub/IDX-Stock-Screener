from backend.app.data.market_data import update_all_stocks


def run_market_data_update():
    print("Starting market data update...")

    update_all_stocks("5d")

    print("Market data update finished.")