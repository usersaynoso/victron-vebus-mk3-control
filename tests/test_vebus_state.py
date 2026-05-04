from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "victron_vebus_mk3"
    / "vebus_state.py"
)
SPEC = importlib.util.spec_from_file_location("vebus_state", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
vebus_state = importlib.util.module_from_spec(SPEC)
sys.modules["vebus_state"] = vebus_state
SPEC.loader.exec_module(vebus_state)


class FakeDriver:
    REQUEST_TIMEOUT_SECONDS = 0.1

    def __init__(self, responses: list[bytes]) -> None:
        self.responses = responses
        self.requests: list[list[int]] = []
        self._w_completion = None

    def _send_w_request(self, msg: list[int], completion) -> None:
        self.requests.append(msg)
        self._w_completion = completion
        for response in self.responses:
            completion(None, response)


class FakeMK3:
    def __init__(self, driver: FakeDriver | None = None) -> None:
        self._driver = driver


def test_read_device_charge_state_parses_charge_sub_state() -> None:
    driver = FakeDriver([bytes.fromhex("ff59940902")])

    result = asyncio.run(vebus_state.read_device_charge_state(FakeMK3(driver)))

    assert driver.requests == [[0x0E, 0, 0]]
    assert result is not None
    assert result.state == 9
    assert result.charge_state == vebus_state.ChargeState.ABSORPTION


def test_force_charge_state_uses_action_code() -> None:
    driver = FakeDriver([bytes.fromhex("ff59940903")])

    result = asyncio.run(
        vebus_state.read_device_charge_state(
            FakeMK3(driver), vebus_state.ChargeStateAction.FORCE_FLOAT
        )
    )

    assert driver.requests == [[0x0E, 3, 0]]
    assert result is not None
    assert result.charge_state == vebus_state.ChargeState.FLOAT


def test_read_device_charge_state_returns_none_when_not_supported() -> None:
    driver = FakeDriver([bytes.fromhex("ff59800000")])

    result = asyncio.run(vebus_state.read_device_charge_state(FakeMK3(driver)))

    assert result is None
