from datetime import date, timezone
from unittest.mock import patch

from src.db.screener import create_screener_run


def test_create_screener_run_stores_utc_timestamp():
    with patch("src.db.screener.get_connection") as get_connection:
        conn = get_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (123,)

        result = create_screener_run(date(2026, 10, 23), 100)

        assert result == 123
        params = cursor.execute.call_args.args[1]
        started_at = params[1]
        assert started_at.tzinfo is not None
        assert started_at.utcoffset().total_seconds() == 0
        assert started_at.tzinfo == timezone.utc