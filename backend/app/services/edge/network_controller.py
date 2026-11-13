import datetime
from enum import Enum
from typing import Optional
from app.core.logging import logger

class NetworkState(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"

class NetworkStateController:
    """
    Manages and monitors operational edge network connectivity.
    Supports manual state simulation (for drills, disconnected edge tests)
    and automated connectivity probing.
    """
    _state: NetworkState = NetworkState.ONLINE
    _last_state_change: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    _offline_reason: Optional[str] = None

    @classmethod
    def get_state(cls) -> NetworkState:
        return cls._state

    @classmethod
    def is_online(cls) -> bool:
        return cls._state == NetworkState.ONLINE

    @classmethod
    def is_offline(cls) -> bool:
        return cls._state == NetworkState.OFFLINE

    @classmethod
    def set_state(cls, state: NetworkState, reason: Optional[str] = None) -> None:
        prev = cls._state
        cls._state = state
        cls._last_state_change = datetime.datetime.now(datetime.timezone.utc)
        cls._offline_reason = reason if state != NetworkState.ONLINE else None
        logger.info(f"NetworkStateController: Transitioned from {prev} to {state}. Reason: {reason or 'N/A'}")

    @classmethod
    def get_last_state_change(cls) -> datetime.datetime:
        return cls._last_state_change

    @classmethod
    def get_offline_reason(cls) -> Optional[str]:
        return cls._offline_reason

    @classmethod
    def reset(cls) -> None:
        """Resets to default ONLINE state."""
        cls._state = NetworkState.ONLINE
        cls._last_state_change = datetime.datetime.now(datetime.timezone.utc)
        cls._offline_reason = None
