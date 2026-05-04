from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class ChargeState(IntEnum):
    INITIALIZING = 0
    BULK = 1
    ABSORPTION = 2
    FLOAT = 3
    STORAGE = 4
    REPEATED_ABSORPTION = 5
    FORCED_ABSORPTION = 6
    EQUALISE = 7
    BULK_STOPPED = 8
    UNKNOWN = 9


class ChargeStateAction(IntEnum):
    INQUIRE = 0
    FORCE_EQUALISE = 1
    FORCE_ABSORPTION = 2
    FORCE_FLOAT = 3


@dataclass
class DeviceChargeState:
    state: int
    charge_state: ChargeState | None


async def read_device_charge_state(
    mk3: Any, action: ChargeStateAction = ChargeStateAction.INQUIRE
) -> DeviceChargeState | None:
    driver = getattr(mk3, "_driver", None)
    if driver is None:
        return None

    completed = asyncio.Event()
    result: dict[str, DeviceChargeState | Exception | None] = {
        "value": None,
        "error": None,
    }

    def completion(_handler: Any, msg: bytes) -> None:
        try:
            result["value"] = _parse_device_charge_state_frame(msg)
        except Exception as err:
            result["error"] = err
        finally:
            completed.set()

    driver._send_w_request([0x0E, int(action), 0], completion)
    await asyncio.wait_for(completed.wait(), _request_timeout(driver))

    error = result["error"]
    if error is not None:
        raise error
    return result["value"]


def _request_timeout(driver: Any) -> float:
    return getattr(type(driver), "REQUEST_TIMEOUT_SECONDS", 0.5)


def _parse_device_charge_state_frame(frame: bytes) -> DeviceChargeState | None:
    if len(frame) < 5:
        raise ValueError(f"Unexpected device state response length: {len(frame)}")
    if frame[2] == 0x80:
        return None
    if frame[2] != 0x94:
        raise ValueError(f"Unexpected device state response code: {frame[2]:#x}")

    state = frame[3]
    sub_state = frame[4]
    charge_state = None
    if state == 9:
        try:
            charge_state = ChargeState(sub_state)
        except ValueError:
            charge_state = ChargeState.UNKNOWN

    return DeviceChargeState(state=state, charge_state=charge_state)
