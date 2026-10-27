from datetime import date
from unittest.mock import MagicMock

import pytest

from backend.app.data.index_alpha_quota import (
    DAILY_LIMIT,
    ENDPOINT_LIMITS,
    reserve_daily_index_alpha_symbols,
)


class FakeCursor:
    def __init__(self, existing_batch=False, used=0):
        self.existing_batch = existing_batch
        self.used = used
        self.fetchone_calls = 0
        self.last_query = ""
        self.queries = []

    def execute(self, query, params=None):
        self.last_query = " ".join(query.split())
        self.queries.append(self.last_query)

    def fetchone(self):
        self.fetchone_calls += 1
        if self.fetchone_calls == 1:
            return (1,) if self.existing_batch else None
        return (self.used,)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def factory_for(cursor):
    def factory():
        return FakeConnection(cursor)
    return factory


def test_free_plan_limit_is_five_units_per_day():
    assert DAILY_LIMIT == 5


def test_endpoint_limits_do_not_exceed_daily_limit():
    assert sum(ENDPOINT_LIMITS.values()) <= DAILY_LIMIT


def test_unknown_endpoint_is_rejected_before_database_access():
    factory = MagicMock()
    with pytest.raises(ValueError, match="Endpoint kuota tidak dikenal"):
        reserve_daily_index_alpha_symbols(
            factory, [(1, "BBCA")], date(2026, 10, 14), "unknown", 1
        )
    factory.assert_not_called()


def test_empty_stock_list_does_not_access_database():
    factory = MagicMock()
    result = reserve_daily_index_alpha_symbols(
        factory, [], date(2026, 10, 14), "foreign_flow", 3
    )
    assert result == []
    factory.assert_not_called()


def test_nonpositive_limit_does_not_access_database():
    factory = MagicMock()
    result = reserve_daily_index_alpha_symbols(
        factory, [(1, "BBCA")], date(2026, 10, 14), "foreign_flow", 0
    )
    assert result == []
    factory.assert_not_called()


def test_previously_reserved_endpoint_is_not_reserved_twice():
    cursor = FakeCursor(existing_batch=True)
    result = reserve_daily_index_alpha_symbols(
        factory_for(cursor),
        [(1, "BBCA"), (2, "BBRI")],
        date(2026, 10, 14),
        "foreign_flow",
        3,
    )
    assert result == []


def test_no_batch_is_recorded_when_daily_quota_is_exhausted():
    cursor = FakeCursor(existing_batch=False, used=5)
    result = reserve_daily_index_alpha_symbols(
        factory_for(cursor),
        [(1, "BBCA"), (2, "BBRI")],
        date(2026, 10, 14),
        "foreign_flow",
        3,
        daily_limit=5,
    )

    assert result == []
    assert not any(
        "INSERT INTO index_alpha_daily_batches" in query
        for query in cursor.queries
    )


def test_reservation_respects_remaining_daily_quota():
    cursor = FakeCursor(existing_batch=False, used=4)
    stocks = [(i, f"T{i}") for i in range(10)]
    result = reserve_daily_index_alpha_symbols(
        factory_for(cursor),
        stocks,
        date(2026, 10, 14),
        "foreign_flow",
        3,
        daily_limit=5,
    )
    assert len(result) <= 1
