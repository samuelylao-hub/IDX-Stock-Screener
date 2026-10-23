from datetime import date
from unittest.mock import patch

from backend.app.data.foreign_flow import update_foreign_flow_batch
from backend.app.data.broker_flow import update_broker_summary_batch


TRADE_DATE = date(2026, 10, 8)


def test_foreign_flow_batch_saves_matching_symbols():
    stocks = [(1, "BBCA"), (2, "BBRI")]
    response = {
        "BBCA": {
            "foreign_buy": 1000,
            "foreign_sell": 400,
            "net_foreign": 600,
        },
        "BBRI": {
            "foreign_buy": 2000,
            "foreign_sell": 500,
            "net_foreign": 1500,
        },
    }

    with (
        patch("backend.app.data.foreign_flow.IndexAlphaProvider") as provider_class,
        patch("backend.app.data.foreign_flow.save_foreign_flow") as save_flow,
    ):
        provider_class.return_value.get_foreign_flow_batch.return_value = response
        saved = update_foreign_flow_batch(stocks, TRADE_DATE)

    assert saved == 2
    assert save_flow.call_count == 2
    provider_class.return_value.get_foreign_flow_batch.assert_called_once()


def test_foreign_flow_batch_skips_symbols_missing_from_response():
    stocks = [(1, "BBCA"), (2, "BBRI")]

    with (
        patch("backend.app.data.foreign_flow.IndexAlphaProvider") as provider_class,
        patch("backend.app.data.foreign_flow.save_foreign_flow") as save_flow,
    ):
        provider_class.return_value.get_foreign_flow_batch.return_value = {
            "BBCA": {
                "foreign_buy": 1000,
                "foreign_sell": 400,
                "net_foreign": 600,
            }
        }
        saved = update_foreign_flow_batch(stocks, TRADE_DATE)

    assert saved == 1
    save_flow.assert_called_once()


def test_broker_batch_counts_save_function_return_values():
    stocks = [(1, "BBCA"), (2, "BBRI")]
    response = {
        "BBCA": [
            {
                "code": "YP",
                "buy_freq": 10,
                "buy_volume": 100,
                "buy_value": 1000,
                "sell_freq": 5,
                "sell_volume": 40,
                "sell_value": 400,
                "buy_avg": 100,
                "sell_avg": 100,
            }
        ],
        "BBRI": [],
    }

    def fake_save(summaries, stock_id, investor_type="all", market_segment="RG"):
        return len(summaries)

    with (
        patch("backend.app.data.broker_flow.IndexAlphaProvider") as provider_class,
        patch(
            "backend.app.data.broker_flow.save_broker_summary",
            side_effect=fake_save,
        ) as save_summary,
    ):
        provider_class.return_value.get_broker_summary_batch.return_value = response
        saved = update_broker_summary_batch(stocks, TRADE_DATE)

    assert saved == 1
    assert save_summary.call_count == 2
    assert save_summary.call_args_list[0].kwargs["stock_id"] == 1
    assert save_summary.call_args_list[1].kwargs["stock_id"] == 2
    assert save_summary.call_args_list[1].kwargs["summaries"] == []


def test_batch_functions_return_zero_for_empty_universe():
    with (
        patch("backend.app.data.foreign_flow.IndexAlphaProvider") as foreign_provider,
        patch("backend.app.data.broker_flow.IndexAlphaProvider") as broker_provider,
    ):
        assert update_foreign_flow_batch([], TRADE_DATE) == 0
        assert update_broker_summary_batch([], TRADE_DATE) == 0

    # Provider objects are constructed, but no API methods should be called.
    foreign_provider.return_value.get_foreign_flow_batch.assert_not_called()
    broker_provider.return_value.get_broker_summary_batch.assert_not_called()

def test_broker_batch_reports_symbols_missing_from_response(capsys):
    stocks = [(1, "BBCA"), (2, "BBRI")]
    response = {
        "BBCA": [{
            "code": "YP",
            "buy_freq": 1,
            "buy_volume": 10,
            "buy_value": 100,
            "sell_freq": 1,
            "sell_volume": 5,
            "sell_value": 50,
            "buy_avg": 10,
            "sell_avg": 10,
        }]
    }

    with (
        patch("backend.app.data.broker_flow.IndexAlphaProvider") as provider_class,
        patch("backend.app.data.broker_flow.save_broker_summary", side_effect=lambda summaries, **kwargs: len(summaries)),
    ):
        provider_class.return_value.get_broker_summary_batch.return_value = response
        saved = update_broker_summary_batch(stocks, TRADE_DATE)

    assert saved == 1
    assert "BBRI" in capsys.readouterr().out



def test_broker_batch_treats_null_symbol_payload_as_empty(capsys):
    stocks = [(1, "BBCA"), (2, "BBRI")]
    response = {"BBCA": [], "BBRI": None}

    with (
        patch("backend.app.data.broker_flow.IndexAlphaProvider") as provider_class,
        patch(
            "backend.app.data.broker_flow.save_broker_summary",
            side_effect=lambda summaries, **kwargs: len(summaries),
        ) as save_summary,
    ):
        provider_class.return_value.get_broker_summary_batch.return_value = response
        saved = update_broker_summary_batch(stocks, TRADE_DATE)

    assert saved == 0
    assert save_summary.call_count == 2
    assert "EMPTY_ROWS" in capsys.readouterr().out
