from __future__ import annotations

from enum import Enum


class Mode(Enum):
    OFF = 0
    ON = 1
    CHARGER_ONLY = 2
    INVERTER_ONLY = 3
    PASS_THROUGH = 4


def enum_options(enum_class: type[Enum]) -> list[str]:
    return [x.lower() for x in enum_class._member_names_]


def enum_value(value: Enum | None) -> str | None:
    return None if value is None else str(value) if value.name is None else value.name.lower()


def mode_from_value(value: str) -> Mode:
    return Mode[value.upper()]


def charger_enabled_in_mode(mode: Mode) -> bool:
    return mode in (Mode.ON, Mode.CHARGER_ONLY)


def inverter_enabled_in_mode(mode: Mode) -> bool:
    return mode in (Mode.ON, Mode.INVERTER_ONLY, Mode.PASS_THROUGH)


def mode_from_enabled_states(charger_enabled: bool, inverter_enabled: bool) -> Mode:
    if charger_enabled and inverter_enabled:
        return Mode.ON
    if charger_enabled:
        return Mode.CHARGER_ONLY
    if inverter_enabled:
        return Mode.PASS_THROUGH
    return Mode.OFF


def mode_with_charger_enabled(mode: Mode, enabled: bool) -> Mode:
    return mode_from_enabled_states(
        charger_enabled=enabled,
        inverter_enabled=inverter_enabled_in_mode(mode),
    )


def mode_with_disable_charge(base_mode: Mode, disable_charge: bool) -> Mode:
    if disable_charge and base_mode is Mode.ON:
        return Mode.PASS_THROUGH
    return base_mode


def base_mode_for_remote_panel(mode: Mode) -> Mode:
    if mode is Mode.PASS_THROUGH:
        return Mode.ON
    return mode


def disable_charge_for_remote_panel(mode: Mode) -> bool:
    return mode is Mode.PASS_THROUGH
