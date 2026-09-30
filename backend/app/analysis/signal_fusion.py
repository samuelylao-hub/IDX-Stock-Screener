from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from backend.app.data.signal_fusion_repository import FlowWindow


@dataclass
class SignalFusionResult:
    symbol: str
    trade_date: date

    foreign_state: str
    broker_state: str
    price_volume_state: str

    foreign_1d_state: str
    foreign_5d_state: str
    foreign_20d_state: str

    broker_1d_state: str
    broker_5d_state: str
    broker_20d_state: str

    foreign_persistence: str
    broker_persistence: str

    alignment: str
    observation: str

    data_completeness: float

    foreign_windows: dict[int, FlowWindow] = field(default_factory=dict)
    broker_windows: dict[int, FlowWindow] = field(default_factory=dict)


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


def classify_flow_window(window: Optional[FlowWindow]) -> str:
    if window is None:
        return "INSUFFICIENT_DATA"

    if window.net_value is None:
        return "INSUFFICIENT_DATA"

    if window.available_days < window.window_days:
        return "INSUFFICIENT_DATA"

    if window.net_value > 0:
        return "ACCUMULATION"

    if window.net_value < 0:
        return "DISTRIBUTION"

    return "NEUTRAL"


def determine_flow_persistence(
    windows: dict[int, FlowWindow],
) -> str:
    available_states = []

    for window_days in (1, 5, 20):
        state = classify_flow_window(
            windows.get(window_days)
        )

        if state != "INSUFFICIENT_DATA":
            available_states.append(state)

    if not available_states:
        return "INSUFFICIENT_DATA"

    if len(available_states) == 1:
        return "SINGLE_DAY"

    if all(
        state == available_states[0]
        for state in available_states
    ):
        return "CONSISTENT"

    return "MIXED"


def determine_alignment(
    foreign_state: str,
    broker_state: str,
) -> str:
    if (
        foreign_state == "NEUTRAL"
        or broker_state == "NEUTRAL"
    ):
        return "NEUTRAL"

    if foreign_state == broker_state:
        return "ALIGNED"

    return "DIVERGENT"


def build_observation(
    foreign_state: str,
    broker_state: str,
    price_volume_state: str,
    alignment: str,
    foreign_persistence: str = "INSUFFICIENT_DATA",
    broker_persistence: str = "INSUFFICIENT_DATA",
    foreign_5d_state: str = "INSUFFICIENT_DATA",
    foreign_20d_state: str = "INSUFFICIENT_DATA",
    broker_5d_state: str = "INSUFFICIENT_DATA",
    broker_20d_state: str = "INSUFFICIENT_DATA",
) -> str:
    parts = []

    if alignment == "ALIGNED":
        if foreign_state == "ACCUMULATION":
            parts.append(
                "Foreign flow and aggregate broker flow both "
                "show accumulation."
            )
        elif foreign_state == "DISTRIBUTION":
            parts.append(
                "Foreign flow and aggregate broker flow both "
                "show distribution."
            )

    elif alignment == "DIVERGENT":
        parts.append(
            f"Foreign flow shows {foreign_state.lower()}, "
            f"while aggregate broker flow shows "
            f"{broker_state.lower()}."
        )

    else:
        parts.append(
            f"Foreign state is {foreign_state.lower()}, "
            f"broker state is {broker_state.lower()}, "
            f"and price/volume is "
            f"{price_volume_state.lower()}."
        )

    if foreign_persistence == "CONSISTENT":
        parts.append(
            "Foreign flow is consistent across the available "
            "multi-day windows."
        )
    elif foreign_persistence == "SINGLE_DAY":
        parts.append(
            "Foreign flow is currently supported only by "
            "the available one-day window."
        )
    elif foreign_persistence == "MIXED":
        parts.append(
            "Foreign flow direction differs across the "
            "available multi-day windows."
        )

    if broker_persistence == "CONSISTENT":
        parts.append(
            "Broker flow is consistent across the available "
            "multi-day windows."
        )
    elif broker_persistence == "SINGLE_DAY":
        parts.append(
            "Broker flow is currently supported only by "
            "the available one-day window."
        )
    elif broker_persistence == "MIXED":
        parts.append(
            "Broker flow direction differs across the "
            "available multi-day windows."
        )

    if foreign_5d_state == "INSUFFICIENT_DATA":
        parts.append(
            "Foreign 5D flow is insufficient for a multi-day "
            "confirmation."
        )

    if foreign_20d_state == "INSUFFICIENT_DATA":
        parts.append(
            "Foreign 20D flow is insufficient for a longer-term "
            "confirmation."
        )

    if broker_5d_state == "INSUFFICIENT_DATA":
        parts.append(
            "Broker 5D flow is insufficient for a multi-day "
            "confirmation."
        )

    if broker_20d_state == "INSUFFICIENT_DATA":
        parts.append(
            "Broker 20D flow is insufficient for a longer-term "
            "confirmation."
        )

    return " ".join(parts)


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
    foreign_windows: Optional[dict[int, FlowWindow]] = None,
    broker_windows: Optional[dict[int, FlowWindow]] = None,
) -> SignalFusionResult:
    foreign_windows = foreign_windows or {}
    broker_windows = broker_windows or {}

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

    foreign_1d_state = classify_flow_window(
        foreign_windows.get(1)
    )
    foreign_5d_state = classify_flow_window(
        foreign_windows.get(5)
    )
    foreign_20d_state = classify_flow_window(
        foreign_windows.get(20)
    )

    broker_1d_state = classify_flow_window(
        broker_windows.get(1)
    )
    broker_5d_state = classify_flow_window(
        broker_windows.get(5)
    )
    broker_20d_state = classify_flow_window(
        broker_windows.get(20)
    )

    foreign_persistence = determine_flow_persistence(
        foreign_windows
    )

    broker_persistence = determine_flow_persistence(
        broker_windows
    )

    if has_foreign_data and has_broker_data:
        alignment = determine_alignment(
            foreign_state,
            broker_state,
        )
    else:
        alignment = "INSUFFICIENT_DATA"

    observation = build_observation(
        foreign_state=foreign_state,
        broker_state=broker_state,
        price_volume_state=price_volume_state,
        alignment=alignment,
        foreign_persistence=foreign_persistence,
        broker_persistence=broker_persistence,
        foreign_5d_state=foreign_5d_state,
        foreign_20d_state=foreign_20d_state,
        broker_5d_state=broker_5d_state,
        broker_20d_state=broker_20d_state,
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
        foreign_1d_state=foreign_1d_state,
        foreign_5d_state=foreign_5d_state,
        foreign_20d_state=foreign_20d_state,
        broker_1d_state=broker_1d_state,
        broker_5d_state=broker_5d_state,
        broker_20d_state=broker_20d_state,
        foreign_persistence=foreign_persistence,
        broker_persistence=broker_persistence,
        alignment=alignment,
        observation=observation,
        data_completeness=data_completeness,
        foreign_windows=foreign_windows,
        broker_windows=broker_windows,
    )