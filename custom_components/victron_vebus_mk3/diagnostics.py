"""Diagnostics support for the Victron VE.Bus MK3 integration."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .const import CONF_SERIAL_NUMBER, DOMAIN, KEY_CONTEXT

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


TO_REDACT = {
    CONF_SERIAL_NUMBER,
    "config_dir",
    "config_path",
    "serial",
    "serial_number",
    "device",
    "external_url",
    "internal_url",
    "latitude",
    "location_name",
    "longitude",
    "port",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    from homeassistant.components.diagnostics import async_redact_data

    payload = _diagnostics_payload(hass, entry)
    payload["environment"] = await _environment_diagnostics(hass)
    payload = _json_safe(payload)
    return async_redact_data(payload, TO_REDACT)


def _diagnostics_payload(hass: Any, entry: Any) -> dict[str, Any]:
    context = _context_for_entry(hass, entry)

    return {
        "integration": _manifest_diagnostics(),
        "config_entry": _config_entry_diagnostics(entry),
        "coordinator": _coordinator_diagnostics(context),
        "controller": _controller_diagnostics(context),
        "mk3_device": _device_diagnostics(context),
        "victron_data": _victron_data_diagnostics(context),
        "entities": _entity_diagnostics(hass, entry),
        "recent_events": []
        if context is None
        else context.diagnostics_events.as_list(),
    }


def _context_for_entry(hass: Any, entry: Any) -> Any | None:
    return (
        getattr(hass, "data", {})
        .get(DOMAIN, {})
        .get(getattr(entry, "entry_id", None), {})
        .get(KEY_CONTEXT)
    )


def _manifest_diagnostics() -> dict[str, Any]:
    try:
        manifest = json.loads(Path(__file__).with_name("manifest.json").read_text())
    except Exception as err:
        return {"error": _exception_diagnostics(err)}

    return {
        "domain": manifest.get("domain"),
        "name": manifest.get("name"),
        "version": manifest.get("version"),
        "iot_class": manifest.get("iot_class"),
        "integration_type": manifest.get("integration_type"),
        "requirements": manifest.get("requirements"),
    }


def _config_entry_diagnostics(entry: Any) -> dict[str, Any]:
    return {
        "entry_id": getattr(entry, "entry_id", None),
        "domain": getattr(entry, "domain", DOMAIN),
        "title": getattr(entry, "title", None),
        "source": getattr(entry, "source", None),
        "version": getattr(entry, "version", None),
        "minor_version": getattr(entry, "minor_version", None),
        "data": getattr(entry, "data", {}),
        "options": getattr(entry, "options", {}),
    }


async def _environment_diagnostics(hass: Any) -> dict[str, Any]:
    try:
        from homeassistant.helpers import system_info

        return await system_info.async_get_system_info(hass)
    except Exception as err:
        return {"error": _exception_diagnostics(err)}


def _coordinator_diagnostics(context: Any | None) -> dict[str, Any] | None:
    if context is None:
        return None

    coordinator = context.coordinator
    last_exception = getattr(coordinator, "last_exception", None)
    return {
        "data_available": getattr(coordinator, "data", None) is not None,
        "last_update_success": getattr(coordinator, "last_update_success", None),
        "last_exception": _exception_diagnostics(last_exception),
        "last_update_success_time": getattr(
            coordinator, "last_update_success_time", None
        ),
        "last_update_failure_time": getattr(
            coordinator, "last_update_failure_time", None
        ),
        "update_interval_seconds": context.update_interval.total_seconds(),
    }


def _controller_diagnostics(context: Any | None) -> dict[str, Any] | None:
    if context is None:
        return None

    controller = context.controller
    ac_entities = getattr(controller, "ac_entities", [])
    return {
        "fault": _json_safe(getattr(controller, "_fault", None)),
        "idle": getattr(controller, "_idle", None),
        "standby": getattr(controller, "standby", None),
        "capabilities": _json_safe(getattr(controller, "capabilities", None)),
        "last_battery_capacity": getattr(controller, "_last_battery_capacity", None),
        "cached_ram_variable_info": _json_safe(
            getattr(controller, "_ram_variable_info", {})
        ),
        "cached_setting_info": _json_safe(getattr(controller, "_setting_info", {})),
        "ac_phase_enabled_entity_counts": [
            sum(1 for entity in phase if getattr(entity, "enabled", False))
            for phase in ac_entities
        ],
    }


def _device_diagnostics(context: Any | None) -> dict[str, Any] | None:
    if context is None:
        return None

    return {
        "device_id": context.device_id,
        "device_info": _device_info_diagnostics(context.device_info),
        "controller_capabilities": context.controller.capabilities,
        "standby": context.controller.standby,
    }


def _device_info_diagnostics(device_info: Any) -> Any:
    info = _json_safe(device_info)
    if not isinstance(info, dict):
        return info

    for key in ("connections", "identifiers"):
        if isinstance(info.get(key), list):
            info[key] = [_redact_identifier_value(item) for item in info[key]]
    return info


def _redact_identifier_value(item: Any) -> Any:
    if isinstance(item, list) and len(item) >= 2:
        return [item[0], "**REDACTED**", *item[2:]]
    return item


def _victron_data_diagnostics(context: Any | None) -> dict[str, Any] | None:
    data = None if context is None else getattr(context.coordinator, "data", None)
    if data is None:
        return None

    return {
        **vars(data),
        "derived": {
            "front_panel_mode": _safe_derived_value(data, "front_panel_mode"),
            "remote_panel_mode": _safe_derived_value(data, "remote_panel_mode"),
            "actual_mode": _safe_derived_value(data, "actual_mode"),
        },
    }


def _safe_derived_value(data: Any, method_name: str) -> Any:
    try:
        return getattr(data, method_name)()
    except Exception as err:
        return {"error": _exception_diagnostics(err)}


def _entity_diagnostics(hass: Any, entry: Any) -> list[dict[str, Any]]:
    from homeassistant.helpers import entity_registry

    registry = entity_registry.async_get(hass)
    entries = entity_registry.async_entries_for_config_entry(
        registry,
        getattr(entry, "entry_id", None),
    )
    return [_entity_entry_diagnostics(hass, entity_entry) for entity_entry in entries]


def _entity_entry_diagnostics(hass: Any, entity_entry: Any) -> dict[str, Any]:
    state = hass.states.get(entity_entry.entity_id)
    return {
        "entity_id": getattr(entity_entry, "entity_id", None),
        "unique_id": getattr(entity_entry, "unique_id", None),
        "platform": getattr(entity_entry, "platform", None),
        "device_id": getattr(entity_entry, "device_id", None),
        "area_id": getattr(entity_entry, "area_id", None),
        "name": getattr(entity_entry, "name", None),
        "original_name": getattr(entity_entry, "original_name", None),
        "translation_key": getattr(entity_entry, "translation_key", None),
        "icon": getattr(entity_entry, "icon", None),
        "original_icon": getattr(entity_entry, "original_icon", None),
        "device_class": getattr(entity_entry, "device_class", None),
        "original_device_class": getattr(entity_entry, "original_device_class", None),
        "entity_category": getattr(entity_entry, "entity_category", None),
        "disabled_by": getattr(entity_entry, "disabled_by", None),
        "hidden_by": getattr(entity_entry, "hidden_by", None),
        "has_entity_name": getattr(entity_entry, "has_entity_name", None),
        "state": _state_diagnostics(state),
    }


def _state_diagnostics(state: Any | None) -> dict[str, Any] | None:
    if state is None:
        return None

    return {
        "state": getattr(state, "state", None),
        "attributes": getattr(state, "attributes", {}),
        "last_changed": getattr(state, "last_changed", None),
        "last_reported": getattr(state, "last_reported", None),
        "last_updated": getattr(state, "last_updated", None),
    }


def _exception_diagnostics(err: BaseException | None) -> dict[str, str] | None:
    if err is None:
        return None
    return {
        "type": type(err).__name__,
        "message": str(err),
    }


def _json_safe(value: Any) -> Any:
    """Convert values from Home Assistant and protocol objects into JSON-safe data."""
    if isinstance(value, Enum):
        return {
            "name": value.name,
            "value": _json_safe(value.value),
        }
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, BaseException):
        return _exception_diagnostics(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_safe(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {_json_safe_key(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if hasattr(value, "__dict__"):
        return {
            key: _json_safe(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


def _json_safe_key(value: Any) -> str:
    if isinstance(value, Enum):
        return value.name
    return str(value)
