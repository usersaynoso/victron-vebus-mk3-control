from __future__ import annotations

from dataclasses import dataclass
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from typing import Callable
from victron_vebus_mk3_protocol import InterfaceFlags, LEDState, SwitchRegister

from . import Context, Data
from .const import DOMAIN, KEY_CONTEXT
from .ram_variables import (
    MULTI_FUNCTIONAL_RELAY_STATE_VARIABLE_ID,
    VIRTUAL_SWITCH_POSITION_VARIABLE_ID,
    ram_variable_bool_enabled,
    ram_variable_bool_supported,
)


@dataclass(kw_only=True)
class VictronMK3BinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[Data], bool | None]


def led_description(
    key: str, name: str, led: LEDState
) -> VictronMK3BinarySensorEntityDescription:
    return VictronMK3BinarySensorEntityDescription(
        key=key,
        name=name,
        translation_key=key,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _led_active(data, led),
    )


ENTITY_DESCRIPTIONS: tuple[VictronMK3BinarySensorEntityDescription, ...] = (
    led_description("mains_indicator", "Mains Indicator", LEDState.MAINS),
    led_description("bulk_indicator", "Bulk Indicator", LEDState.BULK),
    led_description(
        "absorption_indicator", "Absorption Indicator", LEDState.ABSORPTION
    ),
    led_description("float_indicator", "Float Indicator", LEDState.FLOAT),
    led_description("inverter_indicator", "Inverter Indicator", LEDState.INVERTER),
    led_description("overload_indicator", "Overload Indicator", LEDState.OVERLOAD),
    led_description(
        "low_battery_indicator", "Low Battery Indicator", LEDState.LOW_BATTERY
    ),
    led_description(
        "temperature_indicator", "Temperature Indicator", LEDState.TEMPERATURE
    ),
    VictronMK3BinarySensorEntityDescription(
        key="remote_panel_detected",
        name="Remote Panel Detected",
        translation_key="remote_panel_detected",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None
        if data.config is None
        else data.config.remote_panel_detected,
    ),
    VictronMK3BinarySensorEntityDescription(
        key="current_limit_controlled_by_panel",
        name="Current Limit Controlled By Panel",
        translation_key="current_limit_controlled_by_panel",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None
        if data.config is None
        else data.config.current_limit_overridden_by_panel,
    ),
    VictronMK3BinarySensorEntityDescription(
        key="external_control_panel_dedicated",
        name="External Control Panel Dedicated",
        translation_key="external_control_panel_dedicated",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None
        if data.config is None
        else data.config.digital_multi_control_dedicated,
    ),
    VictronMK3BinarySensorEntityDescription(
        key="remote_generator_selected_state",
        name="Remote Generator Selected State",
        translation_key="remote_generator_selected_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _switch_register_active(
            data, SwitchRegister.REMOTE_GENERATOR_SELECTED
        ),
    ),
    VictronMK3BinarySensorEntityDescription(
        key="onboard_remote_inverter_switch",
        name="Onboard Remote Inverter Switch",
        translation_key="onboard_remote_inverter_switch",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _switch_register_active(
            data, SwitchRegister.ONBOARD_REMOTE_SWITCH_INVERT
        ),
    ),
    VictronMK3BinarySensorEntityDescription(
        key="interface_panel_detect",
        name="Interface Panel Detect",
        translation_key="interface_panel_detect",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _interface_flag_active(data, InterfaceFlags.PANEL_DETECT),
    ),
    VictronMK3BinarySensorEntityDescription(
        key="interface_standby",
        name="Interface Standby",
        translation_key="interface_standby",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _interface_flag_active(data, InterfaceFlags.STANDBY),
    ),
    VictronMK3BinarySensorEntityDescription(
        key="virtual_switch_position",
        name="Virtual Switch Position",
        translation_key="virtual_switch_position",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _ram_variable_bool(
            data, VIRTUAL_SWITCH_POSITION_VARIABLE_ID
        ),
    ),
    VictronMK3BinarySensorEntityDescription(
        key="multi_functional_relay_state",
        name="Multi-functional Relay State",
        translation_key="multi_functional_relay_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _ram_variable_bool(
            data, MULTI_FUNCTIONAL_RELAY_STATE_VARIABLE_ID
        ),
    ),
)


def _led_active(data: Data, led: LEDState) -> bool | None:
    if data.led is None:
        return None
    return bool((data.led.on | data.led.blink) & led)


def _switch_register_active(data: Data, flag: SwitchRegister) -> bool | None:
    if data.config is None:
        return None
    return bool(data.config.switch_register & flag)


def _interface_flag_active(data: Data, flag: InterfaceFlags) -> bool | None:
    if data.interface is None:
        return None
    return bool(data.interface.flags & flag)


def _ram_variable_bool(data: Data, variable_id: int) -> bool | None:
    info = data.ram_variable_info.get(variable_id)
    value = data.ram_variable_values.get(variable_id)
    if not ram_variable_bool_supported(info):
        return None
    return ram_variable_bool_enabled(value, info)


class VictronMK3BinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        context: Context,
        entity_description: VictronMK3BinarySensorEntityDescription,
    ) -> None:
        CoordinatorEntity.__init__(self, context.coordinator, entity_description.key)
        self.entity_description = entity_description
        self._attr_device_info = context.device_info
        self._attr_unique_id = f"{context.device_id}-{entity_description.key}"
        self._attr_available = False
        self._attr_is_on = False

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        value = None if data is None else self.entity_description.value_fn(data)
        if value is None:
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_is_on = value
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    context = hass.data[DOMAIN][entry.entry_id][KEY_CONTEXT]
    async_add_entities(
        VictronMK3BinarySensorEntity(context, description)
        for description in ENTITY_DESCRIPTIONS
    )
