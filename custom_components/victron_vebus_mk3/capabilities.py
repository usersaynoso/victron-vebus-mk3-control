from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .battery_monitor_settings import (
    ABSORPTION_VOLTAGE_SETTING_ID,
    ACCEPT_WIDE_INPUT_FREQUENCY_FLAG_BIT,
    AC1_INPUT_CURRENT_LIMIT_SETTING_ID,
    AC2_INPUT_CURRENT_LIMIT_SETTING_ID,
    AES_CURRENT_HYSTERESIS_SETTING_ID,
    AES_LOW_POWER_SHUTDOWN_ENABLED_FLAG_BIT,
    AES_LOW_CURRENT_LIMIT_SETTING_ID,
    ASSIST_CURRENT_BOOST_FACTOR_SETTING_ID,
    BATTERY_CHARGE_EFFICIENCY_SETTING_ID,
    BATTERY_CAPACITY_SETTING_ID,
    BATTERY_SOC_WHEN_BULK_FINISHED_SETTING_ID,
    CHARGE_CURRENT_SETTING_ID,
    DC_INPUT_LOW_PRE_ALARM_OFFSET_SETTING_ID,
    DC_INPUT_LOW_RESTART_OFFSET_SETTING_ID,
    DC_INPUT_LOW_SHUTDOWN_SETTING_ID,
    DISABLE_CHARGE_FLAG_BIT,
    DISABLE_AES_FLAG_BIT,
    DISABLE_GROUND_RELAY_FLAG_BIT,
    DISABLE_WAVE_CHECK_FLAG_BIT,
    DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT,
    DO_NOT_STOP_AFTER_EXCESSIVE_BULK_FLAG_BIT,
    DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT,
    FLAGS0_SETTING_ID,
    FLAGS1_SETTING_ID,
    FLOAT_VOLTAGE_SETTING_ID,
    INVERTER_OUTPUT_VOLTAGE_SETTING_ID,
    MAXIMUM_ABSORPTION_TIME_SETTING_ID,
    POWER_ASSIST_ENABLED_FLAG_BIT,
    REDUCED_FLOAT_ENABLED_FLAG_BIT,
    REMOTE_OVERRULES_AC1_FLAG_BIT,
    REMOTE_OVERRULES_AC2_FLAG_BIT,
    REPEATED_ABSORPTION_INTERVAL_SETTING_ID,
    REPEATED_ABSORPTION_TIME_SETTING_ID,
    SettingInfo,
    SettingValue,
    TUBULAR_PLATE_TRACTION_BATTERY_CURVE_FLAG_BIT,
    WEAK_AC_INPUT_ENABLED_FLAG_BIT,
    setting_flag_supported,
)
from .const import AC_PHASES_POLLED


SettingFlag = tuple[int, int]


def _ac_phase_input_entity_keys() -> set[str]:
    keys: set[str] = set()
    for phase in range(1, AC_PHASES_POLLED + 1):
        suffix = "" if phase == 1 else f"_l{phase}"
        keys.update({f"ac_input_voltage{suffix}", f"ac_input_current{suffix}"})
    return keys


CHARGER_SETTING_IDS = frozenset(
    {
        ABSORPTION_VOLTAGE_SETTING_ID,
        FLOAT_VOLTAGE_SETTING_ID,
        CHARGE_CURRENT_SETTING_ID,
        REPEATED_ABSORPTION_TIME_SETTING_ID,
        REPEATED_ABSORPTION_INTERVAL_SETTING_ID,
        MAXIMUM_ABSORPTION_TIME_SETTING_ID,
    }
)

AC_INPUT_SETTING_IDS = frozenset(
    {
        AC1_INPUT_CURRENT_LIMIT_SETTING_ID,
        AC2_INPUT_CURRENT_LIMIT_SETTING_ID,
        ASSIST_CURRENT_BOOST_FACTOR_SETTING_ID,
    }
)

CHARGER_SETTING_FLAGS = frozenset(
    {
        (FLAGS0_SETTING_ID, DISABLE_CHARGE_FLAG_BIT),
        (FLAGS0_SETTING_ID, DO_NOT_STOP_AFTER_EXCESSIVE_BULK_FLAG_BIT),
        (FLAGS0_SETTING_ID, REDUCED_FLOAT_ENABLED_FLAG_BIT),
        (FLAGS1_SETTING_ID, TUBULAR_PLATE_TRACTION_BATTERY_CURVE_FLAG_BIT),
    }
)

AC_INPUT_SETTING_FLAGS = frozenset(
    {
        (FLAGS0_SETTING_ID, POWER_ASSIST_ENABLED_FLAG_BIT),
        (FLAGS0_SETTING_ID, WEAK_AC_INPUT_ENABLED_FLAG_BIT),
        (FLAGS0_SETTING_ID, REMOTE_OVERRULES_AC2_FLAG_BIT),
        (FLAGS1_SETTING_ID, DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT),
        (FLAGS1_SETTING_ID, ACCEPT_WIDE_INPUT_FREQUENCY_FLAG_BIT),
        (FLAGS1_SETTING_ID, REMOTE_OVERRULES_AC1_FLAG_BIT),
    }
)

SETTING_FLAGS = frozenset(
    {
        *CHARGER_SETTING_FLAGS,
        *AC_INPUT_SETTING_FLAGS,
        (FLAGS0_SETTING_ID, DISABLE_AES_FLAG_BIT),
        (FLAGS0_SETTING_ID, DISABLE_GROUND_RELAY_FLAG_BIT),
        (FLAGS0_SETTING_ID, DISABLE_WAVE_CHECK_FLAG_BIT),
        (FLAGS0_SETTING_ID, DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT),
        (FLAGS1_SETTING_ID, AES_LOW_POWER_SHUTDOWN_ENABLED_FLAG_BIT),
    }
)

CHARGER_ENTITY_KEYS = frozenset(
    {
        "absorption_indicator",
        "absorption_voltage",
        "battery_charger_current",
        "charge_current",
        "charge_enabled",
        "bulk_indicator",
        "float_indicator",
        "float_voltage",
        "force_absorption",
        "force_equalise",
        "force_float",
        "maximum_absorption_time",
        "repeated_absorption_interval",
        "repeated_absorption_time",
        "stop_after_excessive_bulk",
        "storage_mode",
        "tubular_plate_traction_battery_curve",
        "vebus_charge_state",
    }
)

AC_INPUT_ENTITY_KEYS = frozenset(
    {
        *_ac_phase_input_entity_keys(),
        "ac_input_current_limit",
        "ac_input_current_limit_maximum",
        "ac_input_current_limit_minimum",
        "ac_input_frequency",
        "ac_input_power",
        "accept_wide_frequency_range",
        "ac1_input_current_limit",
        "ac2_input_current_limit",
        "assist_current_boost_factor",
        "current_limit_controlled_by_panel",
        "dynamic_current_limiter",
        "last_active_ac_input",
        "mains_indicator",
        "number_of_ac_inputs",
        "power_assist",
        "remote_generator_selected_state",
        "remote_overrules_ac1",
        "remote_overrules_ac2",
        "remote_panel_current_limit",
        "reported_ac_number_of_phases",
        "ups_function",
        "weak_ac_input",
    }
)

SETTING_ENTITY_KEYS = {
    ABSORPTION_VOLTAGE_SETTING_ID: frozenset({"absorption_voltage"}),
    AC1_INPUT_CURRENT_LIMIT_SETTING_ID: frozenset({"ac1_input_current_limit"}),
    AC2_INPUT_CURRENT_LIMIT_SETTING_ID: frozenset({"ac2_input_current_limit"}),
    AES_LOW_CURRENT_LIMIT_SETTING_ID: frozenset({"aes_low_current_limit"}),
    ASSIST_CURRENT_BOOST_FACTOR_SETTING_ID: frozenset({"assist_current_boost_factor"}),
    BATTERY_CAPACITY_SETTING_ID: frozenset({"battery_capacity", "battery_monitor"}),
    BATTERY_SOC_WHEN_BULK_FINISHED_SETTING_ID: frozenset(
        {"battery_soc_when_bulk_finished"}
    ),
    BATTERY_CHARGE_EFFICIENCY_SETTING_ID: frozenset({"battery_charge_efficiency"}),
    CHARGE_CURRENT_SETTING_ID: frozenset({"charge_current"}),
    DC_INPUT_LOW_PRE_ALARM_OFFSET_SETTING_ID: frozenset({"dc_input_low_pre_alarm"}),
    DC_INPUT_LOW_RESTART_OFFSET_SETTING_ID: frozenset({"dc_input_low_restart"}),
    DC_INPUT_LOW_SHUTDOWN_SETTING_ID: frozenset({"dc_input_low_shutdown"}),
    FLOAT_VOLTAGE_SETTING_ID: frozenset({"float_voltage"}),
    INVERTER_OUTPUT_VOLTAGE_SETTING_ID: frozenset({"inverter_output_voltage"}),
    MAXIMUM_ABSORPTION_TIME_SETTING_ID: frozenset({"maximum_absorption_time"}),
    REPEATED_ABSORPTION_INTERVAL_SETTING_ID: frozenset(
        {"repeated_absorption_interval"}
    ),
    REPEATED_ABSORPTION_TIME_SETTING_ID: frozenset({"repeated_absorption_time"}),
    AES_LOW_CURRENT_LIMIT_SETTING_ID: frozenset({"aes_low_current_limit"}),
    AES_CURRENT_HYSTERESIS_SETTING_ID: frozenset({"aes_current_hysteresis"}),
}

SETTING_FLAG_ENTITY_KEYS = {
    (FLAGS0_SETTING_ID, DISABLE_CHARGE_FLAG_BIT): frozenset({"charge_enabled"}),
    (FLAGS0_SETTING_ID, DISABLE_AES_FLAG_BIT): frozenset({"aes"}),
    (FLAGS0_SETTING_ID, DISABLE_GROUND_RELAY_FLAG_BIT): frozenset({"ground_relay"}),
    (FLAGS0_SETTING_ID, DO_NOT_STOP_AFTER_EXCESSIVE_BULK_FLAG_BIT): frozenset(
        {"stop_after_excessive_bulk"}
    ),
    (FLAGS0_SETTING_ID, DISABLE_WAVE_CHECK_FLAG_BIT): frozenset({"ups_function"}),
    (FLAGS0_SETTING_ID, DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT): frozenset(
        {"ups_function"}
    ),
    (FLAGS0_SETTING_ID, POWER_ASSIST_ENABLED_FLAG_BIT): frozenset({"power_assist"}),
    (FLAGS0_SETTING_ID, REDUCED_FLOAT_ENABLED_FLAG_BIT): frozenset({"storage_mode"}),
    (FLAGS0_SETTING_ID, REMOTE_OVERRULES_AC2_FLAG_BIT): frozenset(
        {"remote_overrules_ac2"}
    ),
    (FLAGS0_SETTING_ID, WEAK_AC_INPUT_ENABLED_FLAG_BIT): frozenset({"weak_ac_input"}),
    (FLAGS1_SETTING_ID, ACCEPT_WIDE_INPUT_FREQUENCY_FLAG_BIT): frozenset(
        {"accept_wide_frequency_range"}
    ),
    (FLAGS1_SETTING_ID, DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT): frozenset(
        {"dynamic_current_limiter"}
    ),
    (FLAGS1_SETTING_ID, REMOTE_OVERRULES_AC1_FLAG_BIT): frozenset(
        {"remote_overrules_ac1"}
    ),
    (FLAGS1_SETTING_ID, TUBULAR_PLATE_TRACTION_BATTERY_CURVE_FLAG_BIT): frozenset(
        {"tubular_plate_traction_battery_curve"}
    ),
    (FLAGS1_SETTING_ID, AES_LOW_POWER_SHUTDOWN_ENABLED_FLAG_BIT): frozenset(
        {"aes_low_power_shutdown"}
    ),
}


@dataclass
class DeviceCapabilities:
    has_charger: bool | None = None
    has_ac_input: bool | None = None
    setting_support: dict[int, bool] = field(default_factory=dict)
    setting_flag_support: dict[SettingFlag, bool] = field(default_factory=dict)

    def supports_setting(self, setting_id: int) -> bool:
        return self.setting_support.get(setting_id) is not False

    def supports_setting_flag(self, setting_id: int, flag_bit: int) -> bool:
        return self.setting_flag_support.get((setting_id, flag_bit)) is not False


def infer_device_capabilities(data: Any) -> DeviceCapabilities:
    setting_support = _setting_support(data)
    setting_flag_support = _setting_flag_support(data)

    return DeviceCapabilities(
        has_charger=_infer_has_charger(data, setting_support, setting_flag_support),
        has_ac_input=_infer_has_ac_input(data, setting_support, setting_flag_support),
        setting_support=setting_support,
        setting_flag_support=setting_flag_support,
    )


def entity_supported(
    capabilities: DeviceCapabilities,
    key: str,
    *,
    setting_id: int | None = None,
    setting_flag: SettingFlag | None = None,
) -> bool:
    if key in CHARGER_ENTITY_KEYS and capabilities.has_charger is False:
        return False
    if key in AC_INPUT_ENTITY_KEYS and capabilities.has_ac_input is False:
        return False
    if setting_id is not None and not capabilities.supports_setting(setting_id):
        return False
    if setting_flag is not None and not capabilities.supports_setting_flag(
        setting_flag[0], setting_flag[1]
    ):
        return False
    return True


def unsupported_entity_keys(capabilities: DeviceCapabilities) -> set[str]:
    keys: set[str] = set()
    if capabilities.has_charger is False:
        keys.update(CHARGER_ENTITY_KEYS)
    if capabilities.has_ac_input is False:
        keys.update(AC_INPUT_ENTITY_KEYS)
    for setting_id, supported in capabilities.setting_support.items():
        if not supported:
            keys.update(SETTING_ENTITY_KEYS.get(setting_id, ()))
    for setting_flag, supported in capabilities.setting_flag_support.items():
        if not supported:
            keys.update(SETTING_FLAG_ENTITY_KEYS.get(setting_flag, ()))
    return keys


def _setting_support(data: Any) -> dict[int, bool]:
    setting_info: dict[int, SettingInfo] = getattr(data, "setting_info", {})
    setting_values: dict[int, SettingValue] = getattr(data, "setting_values", {})
    setting_ids = set(setting_info) | set(setting_values)
    support: dict[int, bool] = {}

    for setting_id in setting_ids:
        info = setting_info.get(setting_id)
        value = setting_values.get(setting_id)
        if value is not None:
            support[setting_id] = bool(
                value.supported and (info is None or info.supported)
            )
        elif info is not None and not info.supported:
            support[setting_id] = False

    return support


def _setting_flag_support(data: Any) -> dict[SettingFlag, bool]:
    setting_info: dict[int, SettingInfo] = getattr(data, "setting_info", {})
    setting_values: dict[int, SettingValue] = getattr(data, "setting_values", {})
    support: dict[SettingFlag, bool] = {}

    for setting_flag in SETTING_FLAGS:
        setting_id, flag_bit = setting_flag
        info = setting_info.get(setting_id)
        value = setting_values.get(setting_id)

        if info is not None:
            support[setting_flag] = setting_flag_supported(info, flag_bit)
        if value is not None and not value.supported:
            support[setting_flag] = False

    return support


def _infer_has_charger(
    data: Any,
    setting_support: dict[int, bool],
    setting_flag_support: dict[SettingFlag, bool],
) -> bool | None:
    probes = [getattr(data, "device_charge_state_supported", None)]
    probes.extend(setting_support.get(setting_id) for setting_id in CHARGER_SETTING_IDS)
    probes.extend(
        setting_flag_support.get(setting_flag) for setting_flag in CHARGER_SETTING_FLAGS
    )
    return _capability_from_probes(probes)


def _infer_has_ac_input(
    data: Any,
    setting_support: dict[int, bool],
    setting_flag_support: dict[SettingFlag, bool],
) -> bool | None:
    probes = [_config_has_ac_input(getattr(data, "config", None))]
    probes.extend(setting_support.get(setting_id) for setting_id in AC_INPUT_SETTING_IDS)
    probes.extend(
        setting_flag_support.get(setting_flag) for setting_flag in AC_INPUT_SETTING_FLAGS
    )
    return _capability_from_probes(probes)


def _config_has_ac_input(config: Any) -> bool | None:
    if config is None:
        return None
    if getattr(config, "num_ac_inputs", 0) > 0:
        return True
    if getattr(config, "maximum_current_limit", 0) > 0:
        return True
    if getattr(config, "actual_current_limit", 0) > 0:
        return True
    return False


def _capability_from_probes(probes: list[bool | None]) -> bool | None:
    known = [probe for probe in probes if probe is not None]
    if any(known):
        return True
    if known and len(known) == len(probes):
        return False
    return None
