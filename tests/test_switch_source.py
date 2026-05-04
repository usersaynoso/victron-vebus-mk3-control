from pathlib import Path


def test_switch_source_exposes_setting_flag_switches() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "victron_vebus_mk3"
        / "switch.py"
    ).read_text()

    assert 'key="charge_enabled"' in source
    assert 'name="Charge Enabled"' in source
    assert 'key="power_assist"' in source
    assert 'name="PowerAssist"' in source
    assert 'key="ups_function"' in source
    assert 'name="UPS Function"' in source
    assert 'key="dynamic_current_limiter"' in source
    assert 'name="Dynamic Current Limiter"' in source
    assert 'key="weak_ac_input"' in source
    assert 'name="Weak AC Input"' in source
    assert "DISABLE_WAVE_CHECK_FLAG_BIT" in source
    assert "DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT" in source
    assert "POWER_ASSIST_ENABLED_FLAG_BIT" in source
    assert "DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT" in source
    assert "WEAK_AC_INPUT_ENABLED_FLAG_BIT" in source
    assert "mode_with_charger_enabled" in source
    assert "VictronMK3ChargeEnabledSwitchEntity(context)" in source
    assert "VictronMK3UpsFunctionSwitchEntity(context)" in source
    assert "VictronMK3SettingFlagSwitchEntity(context, description)" in source
