from pathlib import Path


def test_battery_monitor_number_entities_avoid_unsupported_precision_keyword() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "victron_vebus_mk3"
        / "number.py"
    ).read_text()

    assert "battery_capacity" in source
    assert "battery_soc_when_bulk_finished" in source
    assert "battery_charge_efficiency" in source
    assert "dc_input_low_shutdown" in source
    assert "DC Input Low Shut-down" in source
    assert "dc_input_low_restart" in source
    assert "DC Input Low Restart" in source
    assert "suggested_display_precision" not in source
