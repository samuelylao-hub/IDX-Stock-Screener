from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class SignalFusionResult:
    symbol: str
    trade_date: date

    foreign_state: str
    broker_state: str
    price_volume_state: str

    alignment: str
    observation: str

    data_completeness: float


def determine_foreign_state(net_foreign: float) -> str:
    if net_foreign > 0:
        return "ACCUMULATION"

    if net_foreign < 0:
        return "DISTRIBUTION"

    return "NEUTRAL"


def determine_broker_state(total_net: float) -> str:
    if total_net > 0:
        return "ACCUMULATION"

    if total_net < 0:
        return "DISTRIBUTION"

    return "NEUTRAL"


def determine_price_volume_state(
    first_close: float,
    last_close: float,
) -> str:
    if last_close > first_close:
        return "UPTREND"

    if last_close < first_close:
        return "DOWNTREND"

    return "SIDEWAYS"


def determine_alignment(
    foreign_state: str,
    broker_state: str,
) -> str:
    if foreign_state == "NEUTRAL" or broker_state == "NEUTRAL":
        return "NEUTRAL"

    if foreign_state == broker_state:
        return "ALIGNED"

    return "DIVERGENT"


def build_observation(
    foreign_state: str,
    broker_state: str,
    price_volume_state: str,
    alignment: str,
) -> str:
    if alignment == "ALIGNED":
        if foreign_state == "ACCUMULATION":
            return (
                "Foreign flow and aggregate broker flow both show "
                "accumulation."
            )

        if foreign_state == "DISTRIBUTION":
            return (
                "Foreign flow and aggregate broker flow both show "
                "distribution."
            )

    if alignment == "DIVERGENT":
        return (
            f"Foreign flow shows {foreign_state.lower()}, while aggregate "
            f"broker flow shows {broker_state.lower()}."
        )

    return (
        f"Foreign state is {foreign_state.lower()}, broker state is "
        f"{broker_state.lower()}, and price/volume is "
        f"{price_volume_state.lower()}."
    )


def calculate_data_completeness(
    has_price_data: bool,
    has_foreign_data: bool,
    has_broker_data: bool,
) -> float:
    available = sum(
        [
            has_price_data,
            has_foreign_data,
            has_broker_data,
        ]
    )

    return available / 3


def build_signal_fusion_result(
    symbol: str,
    trade_date: date,
    net_foreign: Optional[float],
    broker_net: Optional[float],
    first_close: Optional[float],
    last_close: Optional[float],
) -> SignalFusionResult:
    has_foreign_data = net_foreign is not None
    has_broker_data = broker_net is not None
    has_price_data = (
        first_close is not None
        and last_close is not None
    )

    foreign_state = (
        determine_foreign_state(net_foreign)
        if has_foreign_data
        else "UNKNOWN"
    )

    broker_state = (
        determine_broker_state(broker_net)
        if has_broker_data
        else "UNKNOWN"
    )

    price_volume_state = (
        determine_price_volume_state(
            first_close,
            last_close,
        )
        if has_price_data
        else "UNKNOWN"
    )

    if has_foreign_data and has_broker_data:
        alignment = determine_alignment(
            foreign_state,
            broker_state,
        )
    else:
        alignment = "INSUFFICIENT_DATA"

    observation = build_observation(
        foreign_state,
        broker_state,
        price_volume_state,
        alignment,
    )

    data_completeness = calculate_data_completeness(
        has_price_data,
        has_foreign_data,
        has_broker_data,
    )

    return SignalFusionResult(
        symbol=symbol,
        trade_date=trade_date,
        foreign_state=foreign_state,
        broker_state=broker_state,
        price_volume_state=price_volume_state,
        alignment=alignment,
        observation=observation,
        data_completeness=data_completeness,
    )