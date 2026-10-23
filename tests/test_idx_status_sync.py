from datetime import date
from unittest.mock import patch

import pytest

from backend.app.providers import idx_status


def test_sync_updates_only_symbols_returned_by_idx():
    rows = [{
        "symbol": "BBCA",
        "company_name": "Bank Central Asia",
        "sector": "Finance",
        "board": "Main",
        "suspension_date": date(2026, 1, 2),
    }]

    with (
        patch.object(idx_status, "fetch_long_suspensions", return_value=rows),
        patch("backend.app.database.get_connection") as get_connection,
    ):
        conn = get_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1

        updated = idx_status.sync()

    assert updated == 1
    conn.cursor.return_value.__enter__.return_value.execute.assert_called_once()
    query, params = cursor.execute.call_args.args
    assert "market_status = 'SUSPENDED'" in query
    assert params == ("IDX suspensi 6 bulan sejak 2026-01-02", "BBCA")
    conn.commit.assert_called_once()


def test_sync_refuses_to_update_when_idx_response_is_empty():
    with (
        patch.object(idx_status, "fetch_long_suspensions", return_value=[]),
        patch("backend.app.database.get_connection") as get_connection,
        pytest.raises(RuntimeError, match="refusing to change statuses"),
    ):
        idx_status.sync()

    get_connection.assert_not_called()
