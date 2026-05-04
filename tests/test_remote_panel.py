import importlib.util
from pathlib import Path
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "victron_vebus_mk3"
    / "remote_panel.py"
)
SPEC = importlib.util.spec_from_file_location("remote_panel", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
remote_panel = importlib.util.module_from_spec(SPEC)
sys.modules["remote_panel"] = remote_panel
SPEC.loader.exec_module(remote_panel)


def test_mode_with_charger_enabled_uses_pass_through_for_non_charging_inverter_mode() -> None:
    assert (
        remote_panel.mode_with_charger_enabled(remote_panel.Mode.ON, False)
        is remote_panel.Mode.PASS_THROUGH
    )
    assert (
        remote_panel.mode_with_charger_enabled(remote_panel.Mode.PASS_THROUGH, True)
        is remote_panel.Mode.ON
    )
    assert (
        remote_panel.mode_with_charger_enabled(remote_panel.Mode.CHARGER_ONLY, False)
        is remote_panel.Mode.OFF
    )


def test_pass_through_mode_maps_to_on_with_charge_disabled() -> None:
    assert (
        remote_panel.base_mode_for_remote_panel(remote_panel.Mode.PASS_THROUGH)
        is remote_panel.Mode.ON
    )
    assert remote_panel.disable_charge_for_remote_panel(remote_panel.Mode.PASS_THROUGH)
    assert not remote_panel.disable_charge_for_remote_panel(remote_panel.Mode.ON)


def test_mode_with_disable_charge_maps_on_to_pass_through() -> None:
    assert (
        remote_panel.mode_with_disable_charge(remote_panel.Mode.ON, True)
        is remote_panel.Mode.PASS_THROUGH
    )
    assert (
        remote_panel.mode_with_disable_charge(remote_panel.Mode.CHARGER_ONLY, True)
        is remote_panel.Mode.CHARGER_ONLY
    )


def test_inverter_only_mode_options_are_off_and_on() -> None:
    assert remote_panel.mode_options_for_capabilities(False) == ["off", "on"]
    assert "charger_only" in remote_panel.mode_options_for_capabilities(True)
    assert "pass_through" in remote_panel.mode_options_for_capabilities(None)


def test_inverter_only_mode_display_maps_enabled_modes_to_on() -> None:
    assert (
        remote_panel.mode_for_capabilities(remote_panel.Mode.INVERTER_ONLY, False)
        is remote_panel.Mode.ON
    )
    assert (
        remote_panel.mode_for_capabilities(remote_panel.Mode.PASS_THROUGH, False)
        is remote_panel.Mode.ON
    )
    assert (
        remote_panel.mode_for_capabilities(remote_panel.Mode.OFF, False)
        is remote_panel.Mode.OFF
    )


def test_inverter_only_mode_validation_rejects_charger_modes() -> None:
    assert remote_panel.mode_supported_by_capabilities(remote_panel.Mode.ON, False)
    assert remote_panel.mode_supported_by_capabilities(remote_panel.Mode.OFF, False)
    assert remote_panel.mode_supported_by_capabilities(
        remote_panel.Mode.INVERTER_ONLY, False
    )
    assert not remote_panel.mode_supported_by_capabilities(
        remote_panel.Mode.CHARGER_ONLY, False
    )
    assert not remote_panel.mode_supported_by_capabilities(
        remote_panel.Mode.PASS_THROUGH, False
    )
