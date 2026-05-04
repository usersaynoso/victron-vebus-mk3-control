from __future__ import annotations

from dataclasses import dataclass
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfElectricPotential,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util
from typing import Callable

from . import Context, Data, UPDATE_INTERVAL
from .battery_energy import BatteryEnergyAccumulator, BatteryEnergyDirection
from .const import (
    AC_PHASES_POLLED,
    DOMAIN,
    KEY_CONTEXT,
)
from .protocol import DeviceState
from .remote_panel import Mode, enum_options, enum_value
from .ram_variables import (
    BATTERY_RIPPLE_VOLTAGE_VARIABLE_ID,
    IGNORE_AC_INPUT_VARIABLE_ID,
    SIGNED_AC_LOAD_CURRENT_VARIABLE_ID,
    ram_variable_bool_enabled,
    ram_variable_bool_supported,
)
from .vebus_state import ChargeState


@dataclass(kw_only=True)
class VictronMK3SensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[Data], StateType]


@dataclass(kw_only=True)
class VictronMK3BatteryEnergySensorEntityDescription(SensorEntityDescription):
    direction: BatteryEnergyDirection


def make_ac_phase_sensors(phase: int) -> tuple[VictronMK3SensorEntityDescription, ...]:
    index = phase - 1
    enable_default = phase == 1
    key_suffix = "" if phase == 1 else f"_l{phase}"
    name_suffix = "" if phase == 1 else f" L{phase}"
    return (
        VictronMK3SensorEntityDescription(
            key=f"ac_input_voltage{key_suffix}",
            name=f"AC Input Voltage{name_suffix}",
            translation_key=f"ac_input_voltage{key_suffix}",
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=1,
            entity_registry_enabled_default=enable_default,
            value_fn=lambda data: None
            if data.ac[index] is None
            else data.ac[index].ac_mains_voltage,
        ),
        VictronMK3SensorEntityDescription(
            key=f"ac_input_current{key_suffix}",
            name=f"AC Input Current{name_suffix}",
            translation_key=f"ac_input_current{key_suffix}",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=1,
            entity_registry_enabled_default=enable_default,
            value_fn=lambda data: None
            if data.ac[index] is None
            else data.ac[index].ac_mains_current,
        ),
        VictronMK3SensorEntityDescription(
            key=f"ac_output_voltage{key_suffix}",
            name=f"AC Output Voltage{name_suffix}",
            translation_key=f"ac_output_voltage{key_suffix}",
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=1,
            entity_registry_enabled_default=enable_default,
            value_fn=lambda data: None
            if data.ac[index] is None
            else data.ac[index].ac_inverter_voltage,
        ),
        VictronMK3SensorEntityDescription(
            key=f"ac_output_current{key_suffix}",
            name=f"AC Output Current{name_suffix}",
            translation_key=f"ac_output_current{key_suffix}",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=1,
            entity_registry_enabled_default=enable_default,
            value_fn=lambda data: None
            if data.ac[index] is None
            else data.ac[index].ac_inverter_current,
        ),
    )


ENTITY_DESCRIPTIONS: tuple[VictronMK3SensorEntityDescription, ...] = (
    VictronMK3SensorEntityDescription(
        key="ac_input_current_limit",
        name="AC Input Current Limit",
        translation_key="ac_input_current_limit",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None
        if data.config is None
        else data.config.actual_current_limit,
    ),
    VictronMK3SensorEntityDescription(
        key="ac_input_current_limit_maximum",
        name="AC Input Current Limit Maximum",
        translation_key="ac_input_current_limit_maximum",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None
        if data.config is None
        else data.config.maximum_current_limit,
    ),
    VictronMK3SensorEntityDescription(
        key="ac_input_current_limit_minimum",
        name="AC Input Current Limit Minimum",
        translation_key="ac_input_current_limit_minimum",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None
        if data.config is None
        else data.config.minimum_current_limit,
    ),
    VictronMK3SensorEntityDescription(
        key="last_active_ac_input",
        name="Last Active AC Input",
        translation_key="last_active_ac_input",
        device_class=SensorDeviceClass.ENUM,
        options=("ac_input_1", "ac_input_2", "ac_input_3", "ac_input_4", "unknown"),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _last_active_ac_input(data),
    ),
    VictronMK3SensorEntityDescription(
        key="number_of_ac_inputs",
        name="Number Of AC Inputs",
        translation_key="number_of_ac_inputs",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None if data.config is None else data.config.num_ac_inputs,
    ),
    VictronMK3SensorEntityDescription(
        key="reported_ac_number_of_phases",
        name="Reported AC Number Of Phases",
        translation_key="reported_ac_number_of_phases",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _reported_ac_number_of_phases(data),
    ),
    VictronMK3SensorEntityDescription(
        key="interface_flags",
        name="Interface Flags",
        translation_key="interface_flags",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: None
        if data.interface is None
        else int(data.interface.flags),
    ),
    VictronMK3SensorEntityDescription(
        key="ac_input_power",
        name="AC Input Power",
        translation_key="ac_input_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda data: None if data.power is None else data.power.ac_mains_power,
    ),
    VictronMK3SensorEntityDescription(
        key="ac_input_frequency",
        name="AC Input Frequency",
        translation_key="ac_input_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=1,
        value_fn=lambda data: None
        if data.ac[0] is None
        else data.ac[0].ac_mains_frequency,
    ),
    VictronMK3SensorEntityDescription(
        key="ac_output_power",
        name="AC Output Power",
        translation_key="ac_output_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda data: None
        if data.power is None
        else data.power.ac_inverter_power,
    ),
    VictronMK3SensorEntityDescription(
        key="ac_output_frequency",
        name="AC Output Frequency",
        translation_key="ac_output_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=1,
        value_fn=lambda data: None
        if data.dc is None
        else data.dc.ac_inverter_frequency,
    ),
    VictronMK3SensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        value_fn=lambda data: None if data.dc is None else data.dc.dc_voltage,
    ),
    VictronMK3SensorEntityDescription(
        key="battery_ripple_voltage",
        name="Battery Ripple Voltage",
        translation_key="battery_ripple_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _ram_variable_value(
            data, BATTERY_RIPPLE_VOLTAGE_VARIABLE_ID
        ),
    ),
    VictronMK3SensorEntityDescription(
        key="battery_power",
        name="Battery Power",
        translation_key="battery_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda data: None if data.power is None else data.power.dc_power,
    ),
    VictronMK3SensorEntityDescription(
        key="battery_charge_discharge_power",
        name="Battery Charge Discharge Power",
        translation_key="battery_charge_discharge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda data: None if data.power is None else -data.power.dc_power,
    ),
    VictronMK3SensorEntityDescription(
        key="battery_state_of_charge",
        name="Battery State of Charge",
        translation_key="battery_state_of_charge",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=lambda data: data.battery_soc,
    ),
    VictronMK3SensorEntityDescription(
        key="battery_charger_current",
        name="Battery Charger Current",
        translation_key="battery_charger_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        value_fn=lambda data: None
        if data.dc is None
        else data.dc.dc_current_from_charger,
    ),
    VictronMK3SensorEntityDescription(
        key="battery_inverter_current",
        name="Battery Inverter Current",
        translation_key="battery_inverter_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        value_fn=lambda data: None
        if data.dc is None
        else data.dc.dc_current_to_inverter,
    ),
    VictronMK3SensorEntityDescription(
        key="signed_ac_load_current",
        name="Signed AC Load Current",
        translation_key="signed_ac_load_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _ram_variable_value(
            data, SIGNED_AC_LOAD_CURRENT_VARIABLE_ID
        ),
    ),
    VictronMK3SensorEntityDescription(
        key="device_state",
        name="Device State",
        translation_key="device_state",
        device_class=SensorDeviceClass.ENUM,
        options=enum_options(DeviceState),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None
        if data.ac[0] is None
        else enum_value(data.ac[0].device_state),
    ),
    VictronMK3SensorEntityDescription(
        key="vebus_charge_state",
        name="Detailed Charge State",
        translation_key="vebus_charge_state",
        device_class=SensorDeviceClass.ENUM,
        options=("not_charging", *enum_options(ChargeState)),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _vebus_charge_state(data),
    ),
    VictronMK3SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        translation_key="firmware_version",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None if data.version is None else data.version.version,
    ),
    VictronMK3SensorEntityDescription(
        key="lit_indicators",
        name="Lit Indicators",
        translation_key="lit_indicators",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None if data.led is None else enum_value(data.led.on),
    ),
    VictronMK3SensorEntityDescription(
        key="blinking_indicators",
        name="Blinking Indicators",
        translation_key="blinking_indicators",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: None if data.led is None else enum_value(data.led.blink),
    ),
    VictronMK3SensorEntityDescription(
        key="front_panel_mode",
        name="Front Panel Mode",
        translation_key="front_panel_mode",
        device_class=SensorDeviceClass.ENUM,
        options=("off", "on", "charger_only"),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: enum_value(data.front_panel_mode()),
    ),
    VictronMK3SensorEntityDescription(
        key="ignore_ac_input_state",
        name="Ignore AC Input State",
        translation_key="ignore_ac_input_state",
        device_class=SensorDeviceClass.ENUM,
        options=("off", "on"),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _ignore_ac_input_state(data),
    ),
    VictronMK3SensorEntityDescription(
        key="actual_mode",
        name="Actual Mode",
        translation_key="actual_mode",
        device_class=SensorDeviceClass.ENUM,
        options=enum_options(Mode),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: enum_value(data.actual_mode()),
    ),
)


BATTERY_ENERGY_ENTITY_DESCRIPTIONS: tuple[
    VictronMK3BatteryEnergySensorEntityDescription, ...
] = (
    VictronMK3BatteryEnergySensorEntityDescription(
        key="battery_energy_into",
        name="Battery Energy Into",
        translation_key="battery_energy_into",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        direction=BatteryEnergyDirection.INTO_BATTERY,
    ),
    VictronMK3BatteryEnergySensorEntityDescription(
        key="battery_energy_out_of",
        name="Battery Energy Out Of",
        translation_key="battery_energy_out_of",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        direction=BatteryEnergyDirection.OUT_OF_BATTERY,
    ),
)


class VictronMK3SensorEntity(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, context: Context, entity_description: VictronMK3SensorEntityDescription
    ):
        CoordinatorEntity.__init__(self, context.coordinator, entity_description.key)
        self.entity_description = entity_description
        self._attr_device_info = context.device_info
        self._attr_unique_id = f"{context.device_id}-{entity_description.key}"
        self._attr_available = False
        self._attr_native_value = None

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        value = None if data is None else self.entity_description.value_fn(data)
        if value is None:
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_native_value = value
        self.async_write_ha_state()


class VictronMK3BatteryEnergySensorEntity(RestoreEntity, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        context: Context,
        entity_description: VictronMK3BatteryEnergySensorEntityDescription,
    ):
        CoordinatorEntity.__init__(self, context.coordinator, entity_description.key)
        self.entity_description = entity_description
        self._attr_device_info = context.device_info
        self._attr_unique_id = f"{context.device_id}-{entity_description.key}"
        self._attr_available = False
        self._attr_native_value = None
        self._accumulator = BatteryEnergyAccumulator(
            direction=entity_description.direction,
            max_interval_seconds=UPDATE_INTERVAL.total_seconds() * 3,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is not None:
            restored_value = _parse_float(last_state.state)
            if restored_value is not None:
                self._accumulator.restore(restored_value)
                self._attr_native_value = round(self._accumulator.total_kwh, 6)
                self._attr_available = True

        if self.coordinator.data is not None:
            self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        power_watts = None if data is None or data.power is None else data.power.dc_power

        total_kwh = self._accumulator.advance(dt_util.utcnow(), power_watts)
        if power_watts is None:
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_native_value = round(total_kwh, 6)
        self.async_write_ha_state()


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ignore_ac_input_state(data: Data) -> str | None:
    info = data.ram_variable_info.get(IGNORE_AC_INPUT_VARIABLE_ID)
    value = data.ram_variable_values.get(IGNORE_AC_INPUT_VARIABLE_ID)
    if not ram_variable_bool_supported(info):
        return None

    enabled = ram_variable_bool_enabled(value, info)
    if enabled is None:
        return None
    return "on" if enabled else "off"


def _ram_variable_value(data: Data, variable_id: int) -> StateType:
    value = data.ram_variable_values.get(variable_id)
    if value is None or not value.supported:
        return None
    return value.value


def _last_active_ac_input(data: Data) -> str | None:
    if data.config is None:
        return None
    if 0 <= data.config.last_active_ac_input < 4:
        return f"ac_input_{data.config.last_active_ac_input + 1}"
    return "unknown"


def _reported_ac_number_of_phases(data: Data) -> int | None:
    if data.ac[0] is None:
        return None
    return data.ac[0].ac_num_phases


def _vebus_charge_state(data: Data) -> str | None:
    if data.device_charge_state is None:
        return None
    if data.device_charge_state.charge_state is None:
        return "not_charging"
    return enum_value(data.device_charge_state.charge_state)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    context = hass.data[DOMAIN][entry.entry_id][KEY_CONTEXT]
    entities = [
        VictronMK3SensorEntity(context, description)
        for description in ENTITY_DESCRIPTIONS
    ]
    entities += [
        VictronMK3BatteryEnergySensorEntity(context, description)
        for description in BATTERY_ENERGY_ENTITY_DESCRIPTIONS
    ]
    for phase in range(1, AC_PHASES_POLLED + 1):
        ac_sensors = [
            VictronMK3SensorEntity(context, description)
            for description in make_ac_phase_sensors(phase)
        ]
        context.controller.ac_entities[phase - 1] += ac_sensors
        entities += ac_sensors
    async_add_entities(entities)
