from __future__ import annotations

import ast
from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "victron_vebus_mk3"
    / "config_flow.py"
).read_text()


def test_user_setup_port_uses_serial_port_selector() -> None:
    tree = ast.parse(SOURCE)

    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "homeassistant.helpers.selector"
        and any(alias.name == "SerialPortSelector" for alias in node.names)
        for node in ast.walk(tree)
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "SerialPortSelector"
        for node in ast.walk(tree)
    )
    assert "vol.Required(CONF_PORT, default=user_input[CONF_PORT]): str" not in SOURCE


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
