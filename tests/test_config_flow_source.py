from __future__ import annotations

import ast
from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "victron_vebus_mk3"
    / "config_flow.py"
).read_text()


def test_user_setup_port_uses_home_assistant_2026_serial_path_field() -> None:
    assert (
        "from homeassistant.helpers.service_info.usb import UsbServiceInfo" in SOURCE
    )
    assert "SerialPortSelector" not in SOURCE
    assert "): str," in SOURCE


def test_usb_probe_abort_uses_description_placeholder_mapping() -> None:
    tree = ast.parse(SOURCE)

    abort_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "async_abort"
    ]

    assert any(
        keyword.arg == "description_placeholders"
        and isinstance(keyword.value, ast.Dict)
        for call in abort_calls
        for keyword in call.keywords
    )
    assert (
        'description_placeholders={"error_detail", probe_result.name.lower()}'
        not in SOURCE
    )


def test_config_flow_imports_bundled_protocol_module() -> None:
    tree = ast.parse(SOURCE)

    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "protocol"
        and node.level == 1
        and any(alias.name == "probe" for alias in node.names)
        for node in ast.walk(tree)
    )
    assert "from victron_vebus_mk3_protocol" not in SOURCE


def test_options_flow_exposes_poll_interval_with_minimum_and_default() -> None:
    assert "async_get_options_flow" in SOURCE
    assert "class MK3OptionsFlow(OptionsFlow)" in SOURCE
    assert "CONF_UPDATE_INTERVAL" in SOURCE
    assert "DEFAULT_UPDATE_INTERVAL" in SOURCE
    assert "MIN_UPDATE_INTERVAL" in SOURCE
    assert "vol.Range(min=MIN_UPDATE_INTERVAL)" in SOURCE
    assert "self._config_entry.options.get(" in SOURCE
