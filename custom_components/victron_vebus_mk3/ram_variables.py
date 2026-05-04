from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any


BATTERY_RIPPLE_VOLTAGE_VARIABLE_ID = 6
SIGNED_AC_LOAD_CURRENT_VARIABLE_ID = 9
VIRTUAL_SWITCH_POSITION_VARIABLE_ID = 10
IGNORE_AC_INPUT_VARIABLE_ID = 11
MULTI_FUNCTIONAL_RELAY_STATE_VARIABLE_ID = 12

MONITORED_RAM_VARIABLE_IDS = (
    BATTERY_RIPPLE_VOLTAGE_VARIABLE_ID,
    SIGNED_AC_LOAD_CURRENT_VARIABLE_ID,
    VIRTUAL_SWITCH_POSITION_VARIABLE_ID,
    IGNORE_AC_INPUT_VARIABLE_ID,
    MULTI_FUNCTIONAL_RELAY_STATE_VARIABLE_ID,
)


@dataclass
class RamVariableInfo:
    variable_id: int
    supported: bool
    signed: bool | None = None
    scale: float | None = None
    offset: int | None = None
    bit: int | None = None


@dataclass
class RamVariableValue:
    variable_id: int
    supported: bool
    value: float | None = None
    raw_value: int | None = None


def ram_variable_bool_supported(info: RamVariableInfo | None) -> bool:
    return (
        info is not None
        and info.supported
        and (
            info.bit is not None
            or (info.scale is not None and info.offset is not None)
        )
    )


def ram_variable_bool_enabled(
    value: RamVariableValue | None, info: RamVariableInfo | None
) -> bool | None:
    if value is None or not value.supported or value.raw_value is None:
        return None

    if info is not None and info.bit is not None:
        return value.raw_value & (1 << info.bit) != 0

    if value.raw_value in (0, 1):
        return value.raw_value == 1
    if value.value in (0, 1):
        return value.value == 1
    return None


async def read_ram_variable_info(mk3: Any, variable_id: int) -> RamVariableInfo | None:
    driver = getattr(mk3, "_driver", None)
    if driver is None:
        return None

    completed = asyncio.Event()
    result: dict[str, RamVariableInfo | Exception | None] = {"value": None, "error": None}

    def completion(_handler: Any, msg: bytes) -> None:
        try:
            result["value"] = _parse_ram_variable_info_frame(variable_id, msg)
        except Exception as err:
            result["error"] = err
        finally:
            completed.set()

    _select_ram_variable_address(driver)
    driver._send_w_request([0x36, variable_id & 0xFF, variable_id >> 8], completion)
    await asyncio.wait_for(completed.wait(), _request_timeout(driver))

    error = result["error"]
    if error is not None:
        raise error
    return result["value"]


async def read_ram_variable(
    mk3: Any, variable_id: int, info: RamVariableInfo | None = None
) -> RamVariableValue | None:
    driver = getattr(mk3, "_driver", None)
    if driver is None:
        return None

    if info is None:
        info = await read_ram_variable_info(mk3, variable_id)
    if info is not None and not info.supported:
        return RamVariableValue(variable_id=variable_id, supported=False)

    completed = asyncio.Event()
    result: dict[str, RamVariableValue | Exception | None] = {"value": None, "error": None}

    def completion(_handler: Any, msg: bytes) -> None:
        try:
            result["value"] = _parse_ram_variable_value_frame(variable_id, msg, info)
        except Exception as err:
            result["error"] = err
        finally:
            completed.set()

    _select_ram_variable_address(driver)
    driver._send_w_request([0x30, variable_id & 0xFF], completion)
    await asyncio.wait_for(completed.wait(), _request_timeout(driver))

    error = result["error"]
    if error is not None:
        raise error
    return result["value"]


def _request_timeout(driver: Any) -> float:
    return getattr(type(driver), "REQUEST_TIMEOUT_SECONDS", 0.5)


def _select_ram_variable_address(driver: Any) -> None:
    send_frame = getattr(driver, "_send_frame", None)
    if send_frame is not None:
        send_frame("A", [1, 0])


def _parse_ram_variable_info_frame(
    variable_id: int, frame: bytes
) -> RamVariableInfo:
    if len(frame) < 5:
        raise ValueError(f"Unexpected RAM variable info response length: {len(frame)}")
    if frame[2] != 0x8E:
        raise ValueError(f"Unexpected RAM variable info response code: {frame[2]:#x}")

    sc_raw = frame[3] | frame[4] << 8
    if sc_raw == 0:
        return RamVariableInfo(variable_id=variable_id, supported=False)

    if len(frame) < 8 or frame[5] != 0x8F:
        raise ValueError("Incomplete RAM variable info response")

    offset_raw = frame[6] | frame[7] << 8
    if offset_raw == 0x8000:
        return RamVariableInfo(
            variable_id=variable_id,
            supported=True,
            signed=False,
            offset=-0x8000,
            bit=abs(_signed_16bit(frame[3:5])) - 1,
        )

    sc = _signed_16bit(frame[3:5])
    scale = abs(sc)
    if scale >= 0x4000:
        scale = 1 / (0x8000 - scale)

    return RamVariableInfo(
        variable_id=variable_id,
        supported=True,
        signed=sc < 0,
        scale=scale,
        offset=_signed_16bit(frame[6:8]),
    )


def _parse_ram_variable_value_frame(
    variable_id: int, frame: bytes, info: RamVariableInfo | None
) -> RamVariableValue:
    if len(frame) < 5:
        raise ValueError(f"Unexpected RAM variable response length: {len(frame)}")

    code = frame[2]
    if code == 0x90:
        return RamVariableValue(variable_id=variable_id, supported=False)
    if code != 0x85:
        raise ValueError(f"Unexpected RAM variable response code: {code:#x}")

    raw_value = frame[3] | frame[4] << 8
    return RamVariableValue(
        variable_id=variable_id,
        supported=True,
        value=_ram_variable_value_from_raw(raw_value, info),
        raw_value=raw_value,
    )


def _ram_variable_value_from_raw(
    raw_value: int, info: RamVariableInfo | None
) -> float | None:
    if info is None:
        return raw_value
    if info.bit is not None:
        return 1 if raw_value & (1 << info.bit) != 0 else 0
    if info.scale is None or info.offset is None:
        return None

    value = raw_value
    if info.signed and value >= 0x8000:
        value -= 0x10000
    return info.scale * (value + info.offset)


def _signed_16bit(raw: bytes) -> int:
    value = raw[0] | raw[1] << 8
    if value >= 0x8000:
        value -= 0x10000
    return value
