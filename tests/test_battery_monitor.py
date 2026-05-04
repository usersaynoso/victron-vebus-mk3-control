from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "victron_vebus_mk3"
    / "battery_monitor.py"
)
SPEC = importlib.util.spec_from_file_location("battery_monitor", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
battery_monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(battery_monitor)


class FakeParser:
    def __init__(self, value: float, scale: float = 1) -> None:
        self.value = value
        self._scale = scale
        self.raw: bytes | None = None

    def parse(self, raw: bytes) -> float:
        self.raw = raw
        return self.value


class FakeDriver:
    REQUEST_TIMEOUT_SECONDS = 0.1

    def __init__(self, response: bytes | None = None) -> None:
        self._variable_info = {}
        self._variable_id_queue = []
        self.response = response
        self.request: list[int] | None = None

    def _send_w_request(self, msg: list[int], completion) -> None:
        self.request = msg
        if self.response is not None:
            completion(None, self.response)


class FakeMK3:
    def __init__(self, driver: FakeDriver | None) -> None:
        self._driver = driver


def test_register_battery_soc_variable_appends_once() -> None:
    driver = FakeDriver()
    mk3 = FakeMK3(driver)

    battery_monitor.register_battery_soc_variable(mk3)
    battery_monitor.register_battery_soc_variable(mk3)

    assert driver._variable_id_queue == [battery_monitor.BATTERY_SOC_VARIABLE_ID]


def test_register_battery_soc_variable_skips_known_variables() -> None:
    driver = FakeDriver()
    driver._variable_info[battery_monitor.BATTERY_SOC_VARIABLE_ID] = object()

    battery_monitor.register_battery_soc_variable(FakeMK3(driver))

    assert driver._variable_id_queue == []


def test_read_battery_soc_returns_none_until_variable_info_is_available() -> None:
    value = asyncio.run(battery_monitor.read_battery_soc(FakeMK3(FakeDriver())))

    assert value is None


def test_read_battery_soc_reads_ram_variable_13() -> None:
    parser = FakeParser(78.5)
    driver = FakeDriver(bytes([0x00, 0x00, 0x85, 0x34, 0x12]))
    driver._variable_info[battery_monitor.BATTERY_SOC_VARIABLE_ID] = parser

    value = asyncio.run(battery_monitor.read_battery_soc(FakeMK3(driver)))

    assert driver.request == [0x30, battery_monitor.BATTERY_SOC_VARIABLE_ID]
    assert parser.raw == bytes([0x34, 0x12])
    assert value == 78.5


def test_read_battery_soc_converts_fractional_values_to_percentage() -> None:
    parser = FakeParser(0.99, scale=0.01)
    driver = FakeDriver(bytes([0x00, 0x00, 0x85, 0x63, 0x00]))
    driver._variable_info[battery_monitor.BATTERY_SOC_VARIABLE_ID] = parser

    value = asyncio.run(battery_monitor.read_battery_soc(FakeMK3(driver)))

    assert value == 99.0


def test_read_battery_soc_returns_none_for_unsupported_variable() -> None:
    parser = FakeParser(0)
    driver = FakeDriver(bytes([0x00, 0x00, 0x90, 0x00, 0x00]))
    driver._variable_info[battery_monitor.BATTERY_SOC_VARIABLE_ID] = parser

    value = asyncio.run(battery_monitor.read_battery_soc(FakeMK3(driver)))

    assert value is None
    assert parser.raw is None
