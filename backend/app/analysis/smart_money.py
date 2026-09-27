from dataclasses import dataclass

from backend.app.providers.index_alpha import (
    BrokerSummary,
    ForeignFlow,
)


@dataclass
class SmartMoneySnapshot:
    symbol: str
    trade_date: object

    foreign_buy: int
    foreign_sell: int
    net_foreign: int

    total_broker_buy_value: int
    total_broker_sell_value: int
    total_broker_net_value: int

    top_accumulating_brokers: list[BrokerSummary]
    top_distributing_brokers: list[BrokerSummary]


def build_smart_money_snapshot(
    flow: ForeignFlow,
    broker_summaries: list[BrokerSummary],
    top_n: int = 5,
) -> SmartMoneySnapshot:
    total_broker_buy_value = sum(
        broker.buy_value
        for broker in broker_summaries
    )

    total_broker_sell_value = sum(
        broker.sell_value
        for broker in broker_summaries
    )

    total_broker_net_value = (
        total_broker_buy_value
        - total_broker_sell_value
    )

    sorted_brokers = sorted(
        broker_summaries,
        key=lambda broker: broker.net_value,
        reverse=True,
    )

    top_accumulating_brokers = sorted_brokers[:top_n]

    top_distributing_brokers = sorted(
        broker_summaries,
        key=lambda broker: broker.net_value,
    )[:top_n]

    return SmartMoneySnapshot(
        symbol=flow.symbol,
        trade_date=flow.trade_date,
        foreign_buy=flow.foreign_buy,
        foreign_sell=flow.foreign_sell,
        net_foreign=flow.net_foreign,
        total_broker_buy_value=total_broker_buy_value,
        total_broker_sell_value=total_broker_sell_value,
        total_broker_net_value=total_broker_net_value,
        top_accumulating_brokers=top_accumulating_brokers,
        top_distributing_brokers=top_distributing_brokers,
    )