from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "victron_vebus_mk3"
    / "ram_variables.py"
)
SPEC = importlib.util.spec_from_file_location("ram_variables", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
ram_variables = importlib.util.module_from_spec(SPEC)
sys.modules["ram_variables"] = ram_variables
SPEC.loader.exec_module(ram_variables)


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


def test_read_ram_variable_info_parses_bit_variable_metadata() -> None:
    driver = FakeDriver([bytes.fromhex("ff588e02008f0080")])

    info = asyncio.run(
        ram_variables.read_ram_variable_info(
            FakeMK3(driver), ram_variables.IGNORE_AC_INPUT_VARIABLE_ID
        )
    )

    assert driver.frames == [("A", [1, 0])]
    assert driver.requests == [[0x36, ram_variables.IGNORE_AC_INPUT_VARIABLE_ID, 0]]
    assert info is not None
    assert info.supported
    assert info.bit == 1
    assert ram_variables.ram_variable_bool_supported(info)


def test_read_ram_variable_reads_bit_backed_boolean_value() -> None:
    driver = FakeDriver([bytes.fromhex("ff59850200")])
    info = ram_variables.RamVariableInfo(
        variable_id=ram_variables.IGNORE_AC_INPUT_VARIABLE_ID,
        supported=True,
        bit=1,
    )

    value = asyncio.run(
        ram_variables.read_ram_variable(
            FakeMK3(driver), ram_variables.IGNORE_AC_INPUT_VARIABLE_ID, info
        )
    )

    assert driver.frames == [("A", [1, 0])]
    assert driver.requests == [[0x30, ram_variables.IGNORE_AC_INPUT_VARIABLE_ID]]
    assert value is not None
    assert value.supported
    assert value.raw_value == 2
    assert value.value == 1
    assert ram_variables.ram_variable_bool_enabled(value, info)


def test_read_ram_variable_reads_signed_scaled_value() -> None:
    driver = FakeDriver([bytes.fromhex("ff598585ff")])
    info = ram_variables.RamVariableInfo(
        variable_id=ram_variables.SIGNED_AC_LOAD_CURRENT_VARIABLE_ID,
        supported=True,
        signed=True,
        scale=0.1,
        offset=0,
    )

    value = asyncio.run(
        ram_variables.read_ram_variable(
            FakeMK3(driver), ram_variables.SIGNED_AC_LOAD_CURRENT_VARIABLE_ID, info
        )
    )

    assert value is not None
    assert value.supported
    assert value.raw_value == 0xFF85
    assert round(value.value, 1) == -12.3


def test_ram_variable_bool_enabled_supports_bit_and_binary_variables() -> None:
    bit_info = ram_variables.RamVariableInfo(
        variable_id=ram_variables.IGNORE_AC_INPUT_VARIABLE_ID,
        supported=True,
        bit=1,
    )
    binary_info = ram_variables.RamVariableInfo(
        variable_id=12,
        supported=True,
        scale=1,
        offset=0,
    )

    assert ram_variables.ram_variable_bool_enabled(
        ram_variables.RamVariableValue(
            variable_id=ram_variables.IGNORE_AC_INPUT_VARIABLE_ID,
            supported=True,
            raw_value=2,
        ),
        bit_info,
    )
    assert not ram_variables.ram_variable_bool_enabled(
        ram_variables.RamVariableValue(
            variable_id=ram_variables.IGNORE_AC_INPUT_VARIABLE_ID,
            supported=True,
            raw_value=0,
        ),
        bit_info,
    )
    assert ram_variables.ram_variable_bool_enabled(
        ram_variables.RamVariableValue(variable_id=12, supported=True, raw_value=1, value=1),
        binary_info,
    )
    assert not ram_variables.ram_variable_bool_enabled(
        ram_variables.RamVariableValue(variable_id=12, supported=True, raw_value=0, value=0),
        binary_info,
    )


def test_new_safe_ram_variables_are_monitored() -> None:
    assert ram_variables.BATTERY_RIPPLE_VOLTAGE_VARIABLE_ID in (
        ram_variables.MONITORED_RAM_VARIABLE_IDS
    )
    assert ram_variables.SIGNED_AC_LOAD_CURRENT_VARIABLE_ID in (
        ram_variables.MONITORED_RAM_VARIABLE_IDS
    )
    assert ram_variables.VIRTUAL_SWITCH_POSITION_VARIABLE_ID in (
        ram_variables.MONITORED_RAM_VARIABLE_IDS
    )
    assert ram_variables.MULTI_FUNCTIONAL_RELAY_STATE_VARIABLE_ID in (
        ram_variables.MONITORED_RAM_VARIABLE_IDS
    )
