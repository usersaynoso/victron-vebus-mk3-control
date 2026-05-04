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


def mode_options_for_capabilities(has_charger: bool | None) -> list[str]:
    if has_charger is False:
        return [enum_value(Mode.OFF), enum_value(Mode.ON)]
    return enum_options(Mode)


def mode_for_capabilities(mode: Mode | None, has_charger: bool | None) -> Mode | None:
    if mode is None or has_charger is not False:
        return mode
    if mode is Mode.OFF:
        return Mode.OFF
    return Mode.ON


def mode_supported_by_capabilities(mode: Mode, has_charger: bool | None) -> bool:
    if has_charger is False:
        return mode in (Mode.OFF, Mode.ON, Mode.INVERTER_ONLY)
    return True


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
