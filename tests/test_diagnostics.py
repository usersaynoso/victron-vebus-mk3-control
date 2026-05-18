from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import IntFlag
import importlib
import importlib.util
from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "victron_vebus_mk3"
PACKAGE = "custom_components.victron_vebus_mk3"


def _load_component_submodule(name: str):
    parent = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    parent.__path__ = [str(ROOT / "custom_components")]

    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(COMPONENT)]
    sys.modules[PACKAGE] = package
    return importlib.import_module(f"{PACKAGE}.{name}")


def _load_path_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ExampleFlag(IntFlag):
    FIRST = 1
    SECOND = 2


@dataclass
class ExampleData:
    flag: ExampleFlag
    value: float


class ExampleResponse:
    def __init__(self) -> None:
        self.visible = ExampleFlag.FIRST | ExampleFlag.SECOND
        self._private = "hidden"


def test_json_safe_serializes_protocol_style_objects() -> None:
    diagnostics = _load_component_submodule("diagnostics")

    payload = diagnostics._json_safe(
        {
            "settings": {0: ExampleData(flag=ExampleFlag.SECOND, value=12.5)},
            "responses": [ExampleResponse()],
        }
    )

    assert payload["settings"]["0"]["flag"] == {
        "name": "SECOND",
        "value": 2,
    }
    assert payload["responses"][0]["visible"] == {
        "name": "FIRST|SECOND",
        "value": 3,
    }
    assert "_private" not in payload["responses"][0]


def test_device_info_diagnostics_redacts_identifier_values() -> None:
    diagnostics = _load_component_submodule("diagnostics")

    payload = diagnostics._device_info_diagnostics(
        {
            "identifiers": {
                (
                    "victron_vebus_mk3",
                    "/dev/serial/by-id/usb-Victron_Interface_SECRET",
                )
            },
            "connections": {("usb", "SECRET")},
        }
    )

    assert payload["identifiers"] == [["victron_vebus_mk3", "**REDACTED**"]]
    assert payload["connections"] == [["usb", "**REDACTED**"]]


def test_environment_diagnostics_reports_home_assistant_system_info(monkeypatch) -> None:
    diagnostics = _load_component_submodule("diagnostics")
    homeassistant = types.ModuleType("homeassistant")
    helpers = types.ModuleType("homeassistant.helpers")
    system_info = types.ModuleType("homeassistant.helpers.system_info")

    async def async_get_system_info(hass):
        return {
            "version": "2026.5.0",
            "installation_type": "Home Assistant OS",
            "config_dir": "/config",
        }

    system_info.async_get_system_info = async_get_system_info
    helpers.system_info = system_info
    monkeypatch.setitem(sys.modules, "homeassistant", homeassistant)
    monkeypatch.setitem(sys.modules, "homeassistant.helpers", helpers)
    monkeypatch.setitem(sys.modules, "homeassistant.helpers.system_info", system_info)

    payload = asyncio.run(diagnostics._environment_diagnostics(object()))

    assert payload == {
        "version": "2026.5.0",
        "installation_type": "Home Assistant OS",
        "config_dir": "/config",
    }


def test_controller_diagnostics_exposes_cached_protocol_context() -> None:
    diagnostics = _load_component_submodule("diagnostics")
    controller = types.SimpleNamespace(
        _fault=ExampleFlag.FIRST,
        _idle=True,
        standby=False,
        capabilities=ExampleData(flag=ExampleFlag.SECOND, value=1),
        _last_battery_capacity=220.0,
        _ram_variable_info={9: "cached-ram-info"},
        _setting_info={0: "cached-setting-info"},
        ac_entities=[
            [types.SimpleNamespace(enabled=True), types.SimpleNamespace(enabled=False)],
            [types.SimpleNamespace(enabled=True)],
            [],
            [],
        ],
    )

    payload = diagnostics._controller_diagnostics(
        types.SimpleNamespace(controller=controller)
    )

    assert payload["fault"] == {"name": "FIRST", "value": 1}
    assert payload["idle"] is True
    assert payload["standby"] is False
    assert payload["last_battery_capacity"] == 220.0
    assert payload["cached_ram_variable_info"] == {"9": "cached-ram-info"}
    assert payload["cached_setting_info"] == {"0": "cached-setting-info"}
    assert payload["ac_phase_enabled_entity_counts"] == [1, 1, 0, 0]


def test_diagnostics_event_log_keeps_recent_errors_only() -> None:
    events = _load_path_module(
        "diagnostics_events",
        COMPONENT / "diagnostics_events.py",
    )
    log = events.DiagnosticsEventLog(maxlen=2)

    log.record("first")
    log.record("second", ValueError("bad value"))
    log.record("third", "plain message", entity_id="switch.example")

    history = log.as_list()

    assert [event["operation"] for event in history] == ["second", "third"]
    assert history[0]["exception"] == {
        "type": "ValueError",
        "message": "bad value",
    }
    assert history[1]["message"] == "plain message"
    assert history[1]["details"] == {"entity_id": "switch.example"}


def test_diagnostics_source_exposes_home_assistant_config_entry_hook() -> None:
    source = (COMPONENT / "diagnostics.py").read_text()
    init_source = (COMPONENT / "__init__.py").read_text()

    assert "async_get_config_entry_diagnostics" in source
    assert "async_redact_data" in source
    assert "async_get_system_info" in source
    assert "entity_registry.async_entries_for_config_entry" in source
    assert '"environment"' in source
    assert '"entities"' in source
    assert '"controller"' in source
    assert '"mk3_device"' in source
    assert '"victron_data"' in source
    assert "TO_REDACT" in source
    assert '"serial_number"' in source
    assert '"config_dir"' in source
    assert '"port"' in source
    assert "DiagnosticsEventLog" in init_source
    assert "controller_fault" in init_source
    assert "coordinator_update" in init_source
    assert "run_control_action" in init_source


def test_control_entities_record_failed_actions_for_diagnostics() -> None:
    for filename in ("button.py", "number.py", "select.py", "switch.py"):
        source = (COMPONENT / filename).read_text()
        assert "run_control_action" in source, filename


def test_issue_template_requires_diagnostics_upload() -> None:
    template_dir = ROOT / ".github" / "ISSUE_TEMPLATE"
    config = (template_dir / "config.yml").read_text()
    problem_report = (template_dir / "victron_problem_report.yml").read_text()

    assert "blank_issues_enabled: false" in config
    assert "Download diagnostics" in problem_report
    assert "click the ... next to Victron VE.Bus MK3 Control" in problem_report
    assert "type: upload" in problem_report
    assert "id: diagnostics" in problem_report
    assert "required: true" in problem_report
    assert 'accept: ".json,.txt,.log,.zip"' in problem_report


def test_docs_explain_download_diagnostics() -> None:
    readme = (ROOT / "README.md").read_text()
    troubleshooting = (ROOT / "wiki" / "Troubleshooting.md").read_text()

    assert "Download diagnostics" in readme
    assert "GitHub issue" in readme
    assert "Download Diagnostics For A GitHub Issue" in troubleshooting
    assert "Click the **...** menu" in troubleshooting
    assert "Attach the diagnostics file" in troubleshooting
