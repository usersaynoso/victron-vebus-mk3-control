from __future__ import annotations

from dataclasses import dataclass, field
import importlib
from pathlib import Path
import sys
import types
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "victron_vebus_mk3"
PACKAGE = "custom_components.victron_vebus_mk3"


def _load_capabilities():
    parent = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    parent.__path__ = [str(ROOT / "custom_components")]

    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(COMPONENT)]
    sys.modules[PACKAGE] = package
    return importlib.import_module(f"{PACKAGE}.capabilities")


capabilities = _load_capabilities()


@dataclass
class FakeConfig:
    num_ac_inputs: int = 0
    maximum_current_limit: float = 0
    actual_current_limit: float = 0


@dataclass
class FakeData:
    config: FakeConfig | None = None
    device_charge_state_supported: bool | None = None
    setting_info: dict[int, Any] = field(default_factory=dict)
    setting_values: dict[int, Any] = field(default_factory=dict)


def _supported_setting(setting_id: int):
    return (
        capabilities.SettingInfo(
            setting_id=setting_id,
            supported=True,
            scale=1,
            offset=0,
            minimum_raw=0,
            maximum_raw=100,
        ),
        capabilities.SettingValue(
            setting_id=setting_id,
            supported=True,
            value=1,
            raw_value=1,
        ),
    )


def _unsupported_setting(setting_id: int):
    return (
        capabilities.SettingInfo(setting_id=setting_id, supported=False),
        capabilities.SettingValue(setting_id=setting_id, supported=False),
    )


def test_inverter_charger_capabilities_are_detected_from_supported_probes() -> None:
    data = FakeData(
        config=FakeConfig(num_ac_inputs=1, maximum_current_limit=16, actual_current_limit=8),
        device_charge_state_supported=True,
    )
    info, value = _supported_setting(capabilities.CHARGE_CURRENT_SETTING_ID)
    data.setting_info[capabilities.CHARGE_CURRENT_SETTING_ID] = info
    data.setting_values[capabilities.CHARGE_CURRENT_SETTING_ID] = value

    result = capabilities.infer_device_capabilities(data)

    assert result.has_charger is True
    assert result.has_ac_input is True
    assert capabilities.entity_supported(result, "charge_enabled")
    assert capabilities.entity_supported(result, "remote_panel_current_limit")


def test_inverter_only_capabilities_hide_charger_and_ac_input_entities() -> None:
    data = FakeData(
        config=FakeConfig(num_ac_inputs=0, maximum_current_limit=0, actual_current_limit=0),
        device_charge_state_supported=False,
    )
    for setting_id in (
        capabilities.CHARGER_SETTING_IDS | capabilities.AC_INPUT_SETTING_IDS
    ):
        info, value = _unsupported_setting(setting_id)
        data.setting_info[setting_id] = info
        data.setting_values[setting_id] = value
    data.setting_info[capabilities.FLAGS0_SETTING_ID] = capabilities.SettingInfo(
        setting_id=capabilities.FLAGS0_SETTING_ID,
        supported=True,
        maximum_raw=0,
    )
    data.setting_values[capabilities.FLAGS0_SETTING_ID] = capabilities.SettingValue(
        setting_id=capabilities.FLAGS0_SETTING_ID,
        supported=True,
        raw_value=0,
    )
    data.setting_info[capabilities.FLAGS1_SETTING_ID] = capabilities.SettingInfo(
        setting_id=capabilities.FLAGS1_SETTING_ID,
        supported=True,
        maximum_raw=0,
    )
    data.setting_values[capabilities.FLAGS1_SETTING_ID] = capabilities.SettingValue(
        setting_id=capabilities.FLAGS1_SETTING_ID,
        supported=True,
        raw_value=0,
    )

    result = capabilities.infer_device_capabilities(data)
    hidden = capabilities.unsupported_entity_keys(result)

    assert result.has_charger is False
    assert result.has_ac_input is False
    assert "charge_enabled" in hidden
    assert "force_equalise" in hidden
    assert "ac_input_current_limit" in hidden
    assert "remote_panel_current_limit" in hidden
    assert not capabilities.entity_supported(result, "charge_enabled")
    assert not capabilities.entity_supported(result, "remote_panel_current_limit")
    assert capabilities.entity_supported(result, "battery_voltage")
    assert capabilities.entity_supported(result, "inverter_output_voltage")
    assert capabilities.entity_supported(result, "remote_panel_standby")


def test_unknown_capabilities_preserve_existing_entity_behavior() -> None:
    result = capabilities.infer_device_capabilities(FakeData())

    assert result.has_charger is None
    assert result.has_ac_input is None
    assert capabilities.entity_supported(result, "charge_enabled")
    assert capabilities.entity_supported(result, "remote_panel_current_limit")


def test_explicitly_unsupported_settings_are_filtered_even_when_device_type_unknown() -> None:
    result = capabilities.DeviceCapabilities(
        setting_support={capabilities.CHARGE_CURRENT_SETTING_ID: False}
    )

    assert not capabilities.entity_supported(
        result,
        "charge_current",
        setting_id=capabilities.CHARGE_CURRENT_SETTING_ID,
    )
