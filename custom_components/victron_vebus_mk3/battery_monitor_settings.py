from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any


FLAGS0_SETTING_ID = 0
FLAGS1_SETTING_ID = 1
DISABLE_WAVE_CHECK_FLAG_BIT = 3
DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT = 7
DISABLE_CHARGE_FLAG_BIT = 6
DO_NOT_STOP_AFTER_EXCESSIVE_BULK_FLAG_BIT = 4
POWER_ASSIST_ENABLED_FLAG_BIT = 5
DISABLE_AES_FLAG_BIT = 8
REDUCED_FLOAT_ENABLED_FLAG_BIT = 11
DISABLE_GROUND_RELAY_FLAG_BIT = 13
WEAK_AC_INPUT_ENABLED_FLAG_BIT = 14
REMOTE_OVERRULES_AC2_FLAG_BIT = 15
ACCEPT_WIDE_INPUT_FREQUENCY_FLAG_BIT = 11
# Dynamic current limiter is Flags[28], which maps to bit 12 in Flags1.
DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT = 12
TUBULAR_PLATE_TRACTION_BATTERY_CURVE_FLAG_BIT = 13
REMOTE_OVERRULES_AC1_FLAG_BIT = 14
AES_LOW_POWER_SHUTDOWN_ENABLED_FLAG_BIT = 15

ABSORPTION_VOLTAGE_SETTING_ID = 2
FLOAT_VOLTAGE_SETTING_ID = 3
CHARGE_CURRENT_SETTING_ID = 4
INVERTER_OUTPUT_VOLTAGE_SETTING_ID = 5
AC1_INPUT_CURRENT_LIMIT_SETTING_ID = 6
REPEATED_ABSORPTION_TIME_SETTING_ID = 7
REPEATED_ABSORPTION_INTERVAL_SETTING_ID = 8
MAXIMUM_ABSORPTION_TIME_SETTING_ID = 9
BATTERY_CAPACITY_SETTING_ID = 64
BATTERY_SOC_WHEN_BULK_FINISHED_SETTING_ID = 65
BATTERY_CHARGE_EFFICIENCY_SETTING_ID = 72
DC_INPUT_LOW_SHUTDOWN_SETTING_ID = 11
# VE.Bus stores low restart as an offset above the low shut-down voltage.
DC_INPUT_LOW_RESTART_OFFSET_SETTING_ID = 12
ASSIST_CURRENT_BOOST_FACTOR_SETTING_ID = 48
AC2_INPUT_CURRENT_LIMIT_SETTING_ID = 49
AES_LOW_CURRENT_LIMIT_SETTING_ID = 50
AES_CURRENT_HYSTERESIS_SETTING_ID = 51
# VE.Bus stores low pre-alarm as an offset above the low restart voltage.
DC_INPUT_LOW_PRE_ALARM_OFFSET_SETTING_ID = 63

BATTERY_MONITOR_SETTING_IDS = (
    BATTERY_CAPACITY_SETTING_ID,
    BATTERY_SOC_WHEN_BULK_FINISHED_SETTING_ID,
    BATTERY_CHARGE_EFFICIENCY_SETTING_ID,
)
MONITORED_SETTING_IDS = BATTERY_MONITOR_SETTING_IDS + (
    ABSORPTION_VOLTAGE_SETTING_ID,
    FLOAT_VOLTAGE_SETTING_ID,
    CHARGE_CURRENT_SETTING_ID,
    INVERTER_OUTPUT_VOLTAGE_SETTING_ID,
    AC1_INPUT_CURRENT_LIMIT_SETTING_ID,
    REPEATED_ABSORPTION_TIME_SETTING_ID,
    REPEATED_ABSORPTION_INTERVAL_SETTING_ID,
    MAXIMUM_ABSORPTION_TIME_SETTING_ID,
    DC_INPUT_LOW_SHUTDOWN_SETTING_ID,
    DC_INPUT_LOW_RESTART_OFFSET_SETTING_ID,
    ASSIST_CURRENT_BOOST_FACTOR_SETTING_ID,
    AC2_INPUT_CURRENT_LIMIT_SETTING_ID,
    AES_LOW_CURRENT_LIMIT_SETTING_ID,
    AES_CURRENT_HYSTERESIS_SETTING_ID,
    DC_INPUT_LOW_PRE_ALARM_OFFSET_SETTING_ID,
    FLAGS0_SETTING_ID,
    FLAGS1_SETTING_ID,
)


@dataclass
class SettingInfo:
    setting_id: int
    supported: bool
    scale: float | None = None
    offset: int | None = None
    default_raw: int | None = None
    minimum_raw: int | None = None
    maximum_raw: int | None = None
    access_level: int | None = None

    @property
    def default(self) -> float | None:
        return None if self.default_raw is None else self.value_from_raw(self.default_raw)

    @property
    def minimum(self) -> float | None:
        return None if self.minimum_raw is None else self.value_from_raw(self.minimum_raw)

    @property
    def maximum(self) -> float | None:
        return None if self.maximum_raw is None else self.value_from_raw(self.maximum_raw)

    def value_from_raw(self, raw_value: int) -> float:
        if self.scale is None or self.offset is None:
            raise ValueError("Setting metadata is incomplete")
        return self.scale * (raw_value + self.offset)

    def raw_from_value(self, value: float) -> int:
        if self.scale is None or self.offset is None:
            raise ValueError("Setting metadata is incomplete")
        raw_value = round(value / self.scale - self.offset)
        if raw_value < 0 or raw_value > 0xFFFF:
            raise ValueError(f"Setting value {value} is out of range")
        return raw_value


@dataclass
class SettingValue:
    setting_id: int
    supported: bool
    value: float | None = None
    raw_value: int | None = None


KNOWN_SETTING_INFO: dict[int, SettingInfo] = {
    BATTERY_CAPACITY_SETTING_ID: SettingInfo(
        setting_id=BATTERY_CAPACITY_SETTING_ID,
        supported=True,
        scale=1,
        offset=0,
        default_raw=0,
        minimum_raw=0,
        maximum_raw=65330,
    ),
    BATTERY_SOC_WHEN_BULK_FINISHED_SETTING_ID: SettingInfo(
        setting_id=BATTERY_SOC_WHEN_BULK_FINISHED_SETTING_ID,
        supported=True,
        scale=0.5,
        offset=0,
        default_raw=170,
        minimum_raw=60,
        maximum_raw=200,
    ),
    BATTERY_CHARGE_EFFICIENCY_SETTING_ID: SettingInfo(
        setting_id=BATTERY_CHARGE_EFFICIENCY_SETTING_ID,
        supported=True,
        scale=1 / 256,
        offset=1,
        default_raw=255,
        minimum_raw=0,
        maximum_raw=255,
    ),
}


def battery_monitor_enabled_from_capacity(capacity: float | None) -> bool | None:
    if capacity is None:
        return None
    return capacity > 0


def setting_flag_supported(info: SettingInfo | None, flag_bit: int) -> bool:
    return (
        info is not None
        and info.supported
        and info.maximum_raw is not None
        and 0 <= flag_bit < 16
        and info.maximum_raw & (1 << flag_bit) != 0
    )


def setting_flag_enabled(value: SettingValue | None, flag_bit: int) -> bool | None:
    if (
        value is None
        or not value.supported
        or value.raw_value is None
        or flag_bit < 0
        or flag_bit >= 16
    ):
        return None

    return value.raw_value & (1 << flag_bit) != 0


def setting_flag_value(
    value: SettingValue | None, flag_bit: int, *, inverted: bool = False
) -> bool | None:
    enabled = setting_flag_enabled(value, flag_bit)
    if enabled is None:
        return None
    return not enabled if inverted else enabled


def setting_raw_with_flag(raw_value: int, flag_bit: int, enabled: bool) -> int:
    if raw_value < 0 or raw_value > 0xFFFF:
        raise ValueError(f"Setting raw value {raw_value} is out of range")
    if flag_bit < 0 or flag_bit >= 16:
        raise ValueError(f"Flag bit {flag_bit} is out of range")

    mask = 1 << flag_bit
    if enabled:
        return raw_value | mask
    return raw_value & ~mask


def ups_function_supported(info: SettingInfo | None) -> bool:
    return setting_flag_supported(
        info, DISABLE_WAVE_CHECK_FLAG_BIT
    ) and setting_flag_supported(info, DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT)


def ups_function_enabled(value: SettingValue | None) -> bool | None:
    disable_wave_check = setting_flag_enabled(value, DISABLE_WAVE_CHECK_FLAG_BIT)
    inverse_disable_wave_check = setting_flag_enabled(
        value, DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT
    )
    if disable_wave_check is None or inverse_disable_wave_check is None:
        return None
    return not disable_wave_check


def setting_raw_with_ups_function(raw_value: int, enabled: bool) -> int:
    value = setting_raw_with_flag(raw_value, DISABLE_WAVE_CHECK_FLAG_BIT, not enabled)
    return setting_raw_with_flag(
        value, DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT, enabled
    )


def numeric_setting_range(
    info: SettingInfo | None, value: SettingValue | None
) -> tuple[float, float, float, float] | None:
    if (
        info is None
        or not info.supported
        or info.minimum is None
        or info.maximum is None
        or info.scale is None
        or value is None
        or not value.supported
        or value.value is None
    ):
        return None

    return (
        info.minimum,
        info.maximum,
        abs(info.scale),
        value.value,
    )


def relative_numeric_setting_range(
    base_value: float | None,
    info: SettingInfo | None,
    value: SettingValue | None,
) -> tuple[float, float, float, float] | None:
    absolute_value = relative_setting_absolute_value(base_value, value)
    if (
        base_value is None
        or absolute_value is None
        or info is None
        or not info.supported
        or info.minimum is None
        or info.maximum is None
        or info.scale is None
    ):
        return None

    return (
        base_value + info.minimum,
        base_value + info.maximum,
        abs(info.scale),
        absolute_value,
    )


def relative_setting_absolute_value(
    base_value: float | None, value: SettingValue | None
) -> float | None:
    if (
        base_value is None
        or value is None
        or not value.supported
        or value.value is None
    ):
        return None

    return base_value + value.value


def relative_setting_offset_from_absolute(
    base_value: float, absolute_value: float
) -> float:
    return absolute_value - base_value


async def read_setting_info(mk3: Any, setting_id: int) -> SettingInfo | None:
    if setting_id in KNOWN_SETTING_INFO:
        return _clone_setting_info(KNOWN_SETTING_INFO[setting_id])

    if hasattr(mk3, "send_setting_info_request"):
        response = await mk3.send_setting_info_request(setting_id)
        return _coerce_setting_info(response, setting_id)

    driver = getattr(mk3, "_driver", None)
    if driver is None:
        return None

    completed = asyncio.Event()
    result: dict[str, SettingInfo | Exception | None] = {"value": None, "error": None}
    frames: list[bytes] = []

    def completion(_handler: Any, msg: bytes) -> None:
        try:
            frames.append(bytes(msg))
            parsed = _parse_setting_info_frames(setting_id, frames)
            if parsed is None:
                driver._w_completion = completion
                return
            result["value"] = parsed
        except Exception as err:
            result["error"] = err
        finally:
            if result["value"] is not None or result["error"] is not None:
                completed.set()

    driver._send_w_request([0x35, setting_id & 0xFF, setting_id >> 8], completion)
    await asyncio.wait_for(completed.wait(), _request_timeout(driver))

    error = result["error"]
    if error is not None:
        raise error
    return result["value"]


async def read_setting(
    mk3: Any, setting_id: int, info: SettingInfo | None = None
) -> SettingValue | None:
    if hasattr(mk3, "send_setting_request"):
        response = await mk3.send_setting_request(setting_id)
        return _coerce_setting_value(response, setting_id)

    driver = getattr(mk3, "_driver", None)
    if driver is None:
        return None

    if info is None:
        info = await read_setting_info(mk3, setting_id)
    if info is not None and not info.supported:
        return SettingValue(setting_id=setting_id, supported=False)

    completed = asyncio.Event()
    result: dict[str, SettingValue | Exception | None] = {"value": None, "error": None}

    def completion(_handler: Any, msg: bytes) -> None:
        try:
            result["value"] = _parse_setting_value_frame(setting_id, msg, info)
        except Exception as err:
            result["error"] = err
        finally:
            completed.set()

    driver._send_w_request([0x31, setting_id & 0xFF, setting_id >> 8], completion)
    await asyncio.wait_for(completed.wait(), _request_timeout(driver))

    error = result["error"]
    if error is not None:
        raise error
    return result["value"]


async def write_setting(
    mk3: Any, setting_id: int, value: float, info: SettingInfo | None = None
) -> SettingValue | None:
    if hasattr(mk3, "send_setting_write_request"):
        response = await mk3.send_setting_write_request(setting_id, value)
        return _coerce_setting_value(response, setting_id)

    driver = getattr(mk3, "_driver", None)
    if driver is None:
        return None

    if info is None:
        info = await read_setting_info(mk3, setting_id)
    if info is None:
        return None
    if not info.supported:
        return SettingValue(setting_id=setting_id, supported=False)

    raw_value = info.raw_from_value(value)
    completed = asyncio.Event()
    result: dict[str, SettingValue | Exception | None] = {"value": None, "error": None}

    def completion(_handler: Any, msg: bytes) -> None:
        try:
            result["value"] = _parse_setting_write_frame(setting_id, msg, info, raw_value)
        except Exception as err:
            result["error"] = err
        finally:
            completed.set()

    driver._send_frame("X", [0x33, setting_id & 0xFF, setting_id >> 8])
    driver._send_w_request([0x34, raw_value & 0xFF, raw_value >> 8], completion)
    await asyncio.wait_for(completed.wait(), _request_timeout(driver))

    error = result["error"]
    if error is not None:
        raise error
    return result["value"]


async def write_setting_raw(
    mk3: Any, setting_id: int, raw_value: int, info: SettingInfo | None = None
) -> SettingValue | None:
    if raw_value < 0 or raw_value > 0xFFFF:
        raise ValueError(f"Setting raw value {raw_value} is out of range")

    driver = getattr(mk3, "_driver", None)
    if driver is None:
        return None

    if info is None:
        info = await read_setting_info(mk3, setting_id)
    if info is None:
        return None
    if not info.supported:
        return SettingValue(setting_id=setting_id, supported=False)

    completed = asyncio.Event()
    result: dict[str, SettingValue | Exception | None] = {"value": None, "error": None}

    def completion(_handler: Any, msg: bytes) -> None:
        try:
            result["value"] = _parse_setting_write_frame(setting_id, msg, info, raw_value)
        except Exception as err:
            result["error"] = err
        finally:
            completed.set()

    driver._send_frame("X", [0x33, setting_id & 0xFF, setting_id >> 8])
    driver._send_w_request([0x34, raw_value & 0xFF, raw_value >> 8], completion)
    await asyncio.wait_for(completed.wait(), _request_timeout(driver))

    error = result["error"]
    if error is not None:
        raise error
    return result["value"]


def _request_timeout(driver: Any) -> float:
    return getattr(type(driver), "REQUEST_TIMEOUT_SECONDS", 0.5)


def _clone_setting_info(info: SettingInfo) -> SettingInfo:
    return SettingInfo(
        setting_id=info.setting_id,
        supported=info.supported,
        scale=info.scale,
        offset=info.offset,
        default_raw=info.default_raw,
        minimum_raw=info.minimum_raw,
        maximum_raw=info.maximum_raw,
        access_level=info.access_level,
    )


def _coerce_setting_info(response: Any, setting_id: int) -> SettingInfo | None:
    if response is None:
        return None
    return SettingInfo(
        setting_id=setting_id,
        supported=getattr(response, "supported", False),
        scale=getattr(response, "scale", None),
        offset=getattr(response, "offset", None),
        default_raw=getattr(response, "default_raw", None),
        minimum_raw=getattr(response, "minimum_raw", None),
        maximum_raw=getattr(response, "maximum_raw", None),
        access_level=getattr(response, "access_level", None),
    )


def _coerce_setting_value(response: Any, setting_id: int) -> SettingValue | None:
    if response is None:
        return None
    return SettingValue(
        setting_id=setting_id,
        supported=getattr(response, "supported", False),
        value=getattr(response, "value", None),
        raw_value=getattr(response, "raw_value", None),
    )


def _parse_setting_info_frames(
    setting_id: int, frames: list[bytes]
) -> SettingInfo | None:
    for frame in frames:
        if len(frame) >= 5 and frame[2] == 0x89 and frame[3] == 0 and frame[4] == 0:
            return SettingInfo(setting_id=setting_id, supported=False)
        if len(frame) >= 3 and frame[2] == 0x86:
            return SettingInfo(setting_id=setting_id, supported=False)

    for frame in frames:
        if (
            len(frame) >= 14
            and frame[2] == 0x89
            and frame[5] == 0x8A
            and frame[8] == 0x8B
            and frame[11] == 0x8C
        ):
            maximum = next(
                (item for item in frames if len(item) >= 5 and item[2] == 0x8D),
                None,
            )
            if maximum is None:
                return None
            return SettingInfo(
                setting_id=setting_id,
                supported=True,
                scale=_setting_scale(frame[3:5]),
                offset=_signed_16bit(frame[6:8]),
                default_raw=frame[9] | frame[10] << 8,
                minimum_raw=frame[12] | frame[13] << 8,
                maximum_raw=maximum[3] | maximum[4] << 8,
            )
    return None


def _parse_setting_value_frame(
    setting_id: int, frame: bytes, info: SettingInfo | None
) -> SettingValue:
    if len(frame) < 5:
        raise ValueError(f"Unexpected setting response length: {len(frame)}")
    if frame[2] == 0x91:
        return SettingValue(setting_id=setting_id, supported=False)
    if frame[2] != 0x86:
        raise ValueError(f"Unexpected setting response code: {frame[2]:#x}")

    raw_value = frame[3] | frame[4] << 8
    value = raw_value if info is None else info.value_from_raw(raw_value)
    return SettingValue(
        setting_id=setting_id,
        supported=True,
        value=value,
        raw_value=raw_value,
    )


def _parse_setting_write_frame(
    setting_id: int, frame: bytes, info: SettingInfo, raw_value: int
) -> SettingValue:
    if len(frame) < 3:
        raise ValueError(f"Unexpected write response length: {len(frame)}")
    if frame[2] in (0x80, 0x9B):
        return SettingValue(setting_id=setting_id, supported=False)
    if frame[2] != 0x88:
        raise ValueError(f"Unexpected write response code: {frame[2]:#x}")

    return SettingValue(
        setting_id=setting_id,
        supported=True,
        value=info.value_from_raw(raw_value),
        raw_value=raw_value,
    )


def _setting_scale(raw: bytes) -> float:
    scale = _signed_16bit(raw)
    if scale == 0:
        raise ValueError("Unsupported setting scale")
    return scale if scale > 0 else 1 / (-scale)


def _signed_16bit(raw: bytes) -> int:
    value = raw[0] | raw[1] << 8
    if value >= 0x8000:
        value -= 0x10000
    return value
