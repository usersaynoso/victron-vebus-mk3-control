from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BatteryEnergyDirection(str, Enum):
    INTO_BATTERY = "into_battery"
    OUT_OF_BATTERY = "out_of_battery"


def battery_energy_power_watts(
    dc_power_watts: float | None, direction: BatteryEnergyDirection
) -> float | None:
    if dc_power_watts is None:
        return None

    if direction is BatteryEnergyDirection.INTO_BATTERY:
        return max(dc_power_watts, 0.0)

    return max(-dc_power_watts, 0.0)


@dataclass
class BatteryEnergyAccumulator:
    direction: BatteryEnergyDirection
    max_interval_seconds: float | None = None
    total_kwh: float = 0.0
    _last_power_watts: float | None = None
    _last_sample_at: datetime | None = None

    def restore(self, total_kwh: float | None) -> None:
        if total_kwh is None:
            return

        self.total_kwh = max(total_kwh, 0.0)

    def advance(self, sampled_at: datetime, dc_power_watts: float | None) -> float:
        power_watts = battery_energy_power_watts(dc_power_watts, self.direction)

        if (
            power_watts is not None
            and self._last_power_watts is not None
            and self._last_sample_at is not None
        ):
            elapsed_seconds = (sampled_at - self._last_sample_at).total_seconds()
            if elapsed_seconds > 0 and (
                self.max_interval_seconds is None
                or elapsed_seconds <= self.max_interval_seconds
            ):
                self.total_kwh += self._last_power_watts * elapsed_seconds / 3_600_000

        if power_watts is None:
            self._last_power_watts = None
            self._last_sample_at = None
        else:
            self._last_power_watts = power_watts
            self._last_sample_at = sampled_at

        return self.total_kwh
