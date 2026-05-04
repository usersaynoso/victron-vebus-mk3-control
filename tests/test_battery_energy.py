from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "victron_vebus_mk3"
    / "battery_energy.py"
)
SPEC = importlib.util.spec_from_file_location("battery_energy", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
battery_energy = importlib.util.module_from_spec(SPEC)
sys.modules["battery_energy"] = battery_energy
SPEC.loader.exec_module(battery_energy)


def test_into_battery_accumulator_integrates_positive_power_only() -> None:
    accumulator = battery_energy.BatteryEnergyAccumulator(
        direction=battery_energy.BatteryEnergyDirection.INTO_BATTERY
    )
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assert accumulator.advance(start, 1200.0) == 0.0
    total = accumulator.advance(start + timedelta(minutes=30), 0.0)

    assert round(total, 6) == 0.6


def test_out_of_battery_accumulator_integrates_negative_power_only() -> None:
    accumulator = battery_energy.BatteryEnergyAccumulator(
        direction=battery_energy.BatteryEnergyDirection.OUT_OF_BATTERY
    )
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assert accumulator.advance(start, -600.0) == 0.0
    total = accumulator.advance(start + timedelta(minutes=15), 0.0)

    assert round(total, 6) == 0.15


def test_accumulator_skips_gaps_larger_than_max_interval() -> None:
    accumulator = battery_energy.BatteryEnergyAccumulator(
        direction=battery_energy.BatteryEnergyDirection.INTO_BATTERY,
        max_interval_seconds=30,
    )
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    accumulator.advance(start, 1000.0)
    total = accumulator.advance(start + timedelta(minutes=2), 1000.0)

    assert total == 0.0


def test_accumulator_restore_preserves_existing_total() -> None:
    accumulator = battery_energy.BatteryEnergyAccumulator(
        direction=battery_energy.BatteryEnergyDirection.OUT_OF_BATTERY
    )
    accumulator.restore(1.25)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assert accumulator.advance(start, -500.0) == 1.25
    total = accumulator.advance(start + timedelta(hours=1), 0.0)

    assert round(total, 6) == 1.75


def test_battery_energy_power_watts_splits_charge_and_discharge() -> None:
    assert (
        battery_energy.battery_energy_power_watts(
            450.0, battery_energy.BatteryEnergyDirection.INTO_BATTERY
        )
        == 450.0
    )
    assert (
        battery_energy.battery_energy_power_watts(
            450.0, battery_energy.BatteryEnergyDirection.OUT_OF_BATTERY
        )
        == 0.0
    )
    assert (
        battery_energy.battery_energy_power_watts(
            -450.0, battery_energy.BatteryEnergyDirection.OUT_OF_BATTERY
        )
        == 450.0
    )
