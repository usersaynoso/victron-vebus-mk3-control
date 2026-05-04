from pathlib import Path


def test_setup_entry_refreshes_without_blocking_on_first_update() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "victron_vebus_mk3"
        / "__init__.py"
    ).read_text()

    assert "await coordinator.async_refresh()" in source
    assert "async_config_entry_first_refresh" not in source
    assert "debug_scan_settings" not in source
    assert "DEBUG_SCAN_MARKER" not in source


def test_setup_entry_loads_new_entity_platforms() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "victron_vebus_mk3"
        / "__init__.py"
    ).read_text()

    assert "Platform.BINARY_SENSOR" in source
    assert "Platform.BUTTON" in source
    assert "read_device_charge_state" in source
    assert "send_interface_request" in source


def test_controller_rejects_charger_modes_for_inverter_only_devices() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "victron_vebus_mk3"
        / "__init__.py"
    ).read_text()

    assert "mode_supported_by_capabilities" in source
    assert "not available on inverter-only devices" in source
    assert "SwitchState.INVERTER_ONLY" in source
