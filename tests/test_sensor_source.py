from pathlib import Path


def test_sensor_source_exposes_battery_energy_entities_for_energy_dashboard() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "victron_vebus_mk3"
        / "sensor.py"
    ).read_text()

    assert 'key="battery_energy_into"' in source
    assert 'key="battery_energy_out_of"' in source
    assert 'key="ignore_ac_input_state"' in source
    assert 'name="Ignore AC Input State"' in source
    assert "SensorDeviceClass.ENERGY" in source
    assert "SensorDeviceClass.ENUM" in source
    assert "SensorStateClass.TOTAL_INCREASING" in source
    assert "UnitOfEnergy.KILO_WATT_HOUR" in source


def test_sensor_source_exposes_signed_battery_power_entity() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "victron_vebus_mk3"
        / "sensor.py"
    ).read_text()

    assert 'key="battery_charge_discharge_power"' in source
    assert 'name="Battery Charge Discharge Power"' in source
    assert "else -data.power.dc_power" in source
