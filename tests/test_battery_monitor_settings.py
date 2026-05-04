from __future__ import annotations

import asyncio
import importlib.util
import math
from pathlib import Path
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "victron_vebus_mk3"
    / "battery_monitor_settings.py"
)
SPEC = importlib.util.spec_from_file_location("battery_monitor_settings", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
battery_monitor_settings = importlib.util.module_from_spec(SPEC)
sys.modules["battery_monitor_settings"] = battery_monitor_settings
SPEC.loader.exec_module(battery_monitor_settings)


class FakeDriver:
    REQUEST_TIMEOUT_SECONDS = 0.1

    def __init__(self, responses: list[bytes] | None = None) -> None:
        self.responses = responses or []
        self.requests: list[list[int]] = []
        self.frames: list[tuple[str, list[int]]] = []
        self._w_completion = None

    def _send_w_request(self, msg: list[int], completion) -> None:
        self.requests.append(msg)
        self._w_completion = completion
        for response in self.responses:
            completion(None, response)

    def _send_frame(self, command: str, data: list[int]) -> None:
        self.frames.append((command, data))


class FakeMK3:
    def __init__(self, driver: FakeDriver | None = None) -> None:
        self._driver = driver


class PublicInfoResponse:
    supported = True
    scale = 1
    offset = 0
    default_raw = 0
    minimum_raw = 0
    maximum_raw = 65330
    access_level = None


class PublicValueResponse:
    supported = True
    raw_value = 242
    value = 0.94921875


class PublicMK3:
    async def send_setting_info_request(self, setting_id: int):
        return PublicInfoResponse()

    async def send_setting_request(self, setting_id: int):
        return PublicValueResponse()

    async def send_setting_write_request(self, setting_id: int, value: float):
        return PublicValueResponse()


def test_battery_monitor_enabled_is_based_on_capacity() -> None:
    assert battery_monitor_settings.battery_monitor_enabled_from_capacity(None) is None
    assert not battery_monitor_settings.battery_monitor_enabled_from_capacity(0)
    assert battery_monitor_settings.battery_monitor_enabled_from_capacity(522)


def test_read_setting_info_uses_known_metadata_for_battery_monitor_settings() -> None:
    info = asyncio.run(
        battery_monitor_settings.read_setting_info(FakeMK3(FakeDriver()), 72)
    )

    assert info is not None
    assert info.supported
    assert info.scale == 1 / 256
    assert info.offset == 1
    assert info.minimum == 1 / 256
    assert info.maximum == 1


def test_read_setting_info_parses_short_mode_multi_frame_response() -> None:
    driver = FakeDriver(
        [
            bytes.fromhex("ff588901008a00008b00008c0000"),
            bytes.fromhex("ff588d32ff"),
        ]
    )

    info = asyncio.run(
        battery_monitor_settings.read_setting_info(FakeMK3(driver), 200)
    )

    assert driver.requests == [[0x35, 200, 0]]
    assert info is not None
    assert info.supported
    assert info.maximum_raw == 65330
    assert info.value_from_raw(522) == 522


def test_read_setting_reads_scaled_charge_efficiency() -> None:
    driver = FakeDriver([bytes.fromhex("ff5986f200")])
    info = battery_monitor_settings.SettingInfo(
        setting_id=72,
        supported=True,
        scale=1 / 256,
        offset=1,
        default_raw=255,
        minimum_raw=0,
        maximum_raw=255,
    )

    value = asyncio.run(
        battery_monitor_settings.read_setting(FakeMK3(driver), 72, info)
    )

    assert driver.requests == [[0x31, 72, 0]]
    assert value is not None
    assert value.supported
    assert value.raw_value == 242
    assert value.value == 0.94921875


def test_write_setting_sends_write_setting_then_write_data() -> None:
    driver = FakeDriver([bytes.fromhex("ff59880000")])
    info = battery_monitor_settings.SettingInfo(
        setting_id=65,
        supported=True,
        scale=0.5,
        offset=0,
        default_raw=170,
        minimum_raw=60,
        maximum_raw=200,
    )

    value = asyncio.run(
        battery_monitor_settings.write_setting(FakeMK3(driver), 65, 90, info)
    )

    assert driver.frames == [("X", [0x33, 65, 0])]
    assert driver.requests == [[0x34, 180, 0]]
    assert value is not None
    assert value.supported
    assert value.raw_value == 180
    assert value.value == 90


def test_write_setting_raw_sends_raw_setting_value() -> None:
    driver = FakeDriver([bytes.fromhex("ff59880000")])
    info = battery_monitor_settings.SettingInfo(
        setting_id=0,
        supported=True,
        scale=1,
        offset=0,
        default_raw=0,
        minimum_raw=0,
        maximum_raw=0xFFFF,
    )

    value = asyncio.run(
        battery_monitor_settings.write_setting_raw(FakeMK3(driver), 0, 0x24, info)
    )

    assert driver.frames == [("X", [0x33, 0, 0])]
    assert driver.requests == [[0x34, 0x24, 0]]
    assert value is not None
    assert value.supported
    assert value.raw_value == 0x24
    assert value.value == 0x24


def test_setting_flag_helpers_use_raw_bit_masks() -> None:
    info = battery_monitor_settings.SettingInfo(
        setting_id=0,
        supported=True,
        scale=1,
        offset=0,
        maximum_raw=(
            (1 << battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT)
            | (1 << battery_monitor_settings.DISABLE_WAVE_CHECK_FLAG_BIT)
            | (1 << battery_monitor_settings.DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT)
        ),
    )
    value = battery_monitor_settings.SettingValue(
        setting_id=0,
        supported=True,
        raw_value=(
            (1 << battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT)
            | (1 << battery_monitor_settings.DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT)
        ),
    )

    assert battery_monitor_settings.setting_flag_supported(
        info,
        battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT,
    )
    assert not battery_monitor_settings.setting_flag_supported(info, 4)
    assert battery_monitor_settings.setting_flag_enabled(
        value,
        battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT,
    )
    assert (
        battery_monitor_settings.setting_raw_with_flag(
            0,
            battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT,
            True,
        )
        == 1 << battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT
    )
    assert (
        battery_monitor_settings.setting_raw_with_flag(
            0xFFFF,
            battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT,
            False,
        )
        == 0xFFFF & ~(1 << battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT)
    )
    assert battery_monitor_settings.ups_function_supported(info)
    assert battery_monitor_settings.ups_function_enabled(value)
    assert (
        battery_monitor_settings.setting_raw_with_ups_function(0, True)
        == 1 << battery_monitor_settings.DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT
    )
    assert (
        battery_monitor_settings.setting_raw_with_ups_function(0xFFFF, False)
        == 0xFFFF
        & ~(1 << battery_monitor_settings.DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT)
    )
    assert battery_monitor_settings.DISABLE_WAVE_CHECK_FLAG_BIT == 3
    assert battery_monitor_settings.DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT == 7
    assert battery_monitor_settings.FLAGS1_SETTING_ID == 1
    assert battery_monitor_settings.DISABLE_CHARGE_FLAG_BIT == 6
    assert battery_monitor_settings.WEAK_AC_INPUT_ENABLED_FLAG_BIT == 14
    assert battery_monitor_settings.DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT == 12
    assert battery_monitor_settings.setting_flag_value(
        value,
        battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT,
    )
    assert not battery_monitor_settings.setting_flag_value(
        value,
        battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT,
        inverted=True,
    )


def test_numeric_setting_range_helpers_cover_absolute_and_relative_values() -> None:
    info = battery_monitor_settings.SettingInfo(
        setting_id=battery_monitor_settings.DC_INPUT_LOW_SHUTDOWN_SETTING_ID,
        supported=True,
        scale=0.01,
        offset=0,
        minimum_raw=930,
        maximum_raw=1300,
    )
    value = battery_monitor_settings.SettingValue(
        setting_id=battery_monitor_settings.DC_INPUT_LOW_SHUTDOWN_SETTING_ID,
        supported=True,
        raw_value=1150,
        value=11.5,
    )
    relative_info = battery_monitor_settings.SettingInfo(
        setting_id=battery_monitor_settings.DC_INPUT_LOW_RESTART_OFFSET_SETTING_ID,
        supported=True,
        scale=0.01,
        offset=0,
        minimum_raw=25,
        maximum_raw=600,
    )
    relative_value = battery_monitor_settings.SettingValue(
        setting_id=battery_monitor_settings.DC_INPUT_LOW_RESTART_OFFSET_SETTING_ID,
        supported=True,
        raw_value=160,
        value=1.6,
    )

    assert battery_monitor_settings.numeric_setting_range(info, value) == (
        9.3,
        13.0,
        0.01,
        11.5,
    )
    assert battery_monitor_settings.relative_setting_absolute_value(11.5, relative_value) == 13.1
    assert battery_monitor_settings.relative_numeric_setting_range(
        11.5,
        relative_info,
        relative_value,
    ) == (
        11.75,
        17.5,
        0.01,
        13.1,
    )
    assert math.isclose(
        battery_monitor_settings.relative_setting_offset_from_absolute(11.5, 13.1),
        1.6,
    )


def test_new_safe_setting_ids_are_monitored() -> None:
    assert battery_monitor_settings.ABSORPTION_VOLTAGE_SETTING_ID in (
        battery_monitor_settings.MONITORED_SETTING_IDS
    )
    assert battery_monitor_settings.FLOAT_VOLTAGE_SETTING_ID in (
        battery_monitor_settings.MONITORED_SETTING_IDS
    )
    assert battery_monitor_settings.CHARGE_CURRENT_SETTING_ID in (
        battery_monitor_settings.MONITORED_SETTING_IDS
    )
    assert battery_monitor_settings.INVERTER_OUTPUT_VOLTAGE_SETTING_ID in (
        battery_monitor_settings.MONITORED_SETTING_IDS
    )
    assert battery_monitor_settings.AC1_INPUT_CURRENT_LIMIT_SETTING_ID in (
        battery_monitor_settings.MONITORED_SETTING_IDS
    )
    assert battery_monitor_settings.AC2_INPUT_CURRENT_LIMIT_SETTING_ID in (
        battery_monitor_settings.MONITORED_SETTING_IDS
    )
    assert battery_monitor_settings.DC_INPUT_LOW_PRE_ALARM_OFFSET_SETTING_ID in (
        battery_monitor_settings.MONITORED_SETTING_IDS
    )


def test_unsupported_setting_helpers_return_unavailable_values() -> None:
    unsupported_info = battery_monitor_settings.SettingInfo(
        setting_id=0,
        supported=False,
        scale=1,
        offset=0,
        minimum_raw=0,
        maximum_raw=100,
    )
    unsupported_value = battery_monitor_settings.SettingValue(
        setting_id=0,
        supported=False,
        raw_value=1,
        value=1,
    )

    assert not battery_monitor_settings.setting_flag_supported(
        unsupported_info,
        battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT,
    )
    assert (
        battery_monitor_settings.setting_flag_value(
            unsupported_value,
            battery_monitor_settings.POWER_ASSIST_ENABLED_FLAG_BIT,
        )
        is None
    )
    assert (
        battery_monitor_settings.numeric_setting_range(
            unsupported_info, unsupported_value
        )
        is None
    )


def test_public_setting_api_is_coerced() -> None:
    info = asyncio.run(battery_monitor_settings.read_setting_info(PublicMK3(), 64))
    value = asyncio.run(battery_monitor_settings.read_setting(PublicMK3(), 72))
    written = asyncio.run(battery_monitor_settings.write_setting(PublicMK3(), 72, 0.95))

    assert info is not None
    assert info.supported
    assert info.maximum_raw == 65330
    assert value is not None and value.value == 0.94921875
    assert written is not None and written.raw_value == 242
