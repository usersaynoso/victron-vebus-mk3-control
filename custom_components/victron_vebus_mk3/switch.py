from __future__ import annotations

from dataclasses import dataclass
from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from typing import Awaitable, Callable

from . import Context
from .battery_monitor_settings import (
    ACCEPT_WIDE_INPUT_FREQUENCY_FLAG_BIT,
    AES_LOW_POWER_SHUTDOWN_ENABLED_FLAG_BIT,
    BATTERY_CAPACITY_SETTING_ID,
    DISABLE_CHARGE_FLAG_BIT,
    DISABLE_WAVE_CHECK_FLAG_BIT,
    DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT,
    DISABLE_AES_FLAG_BIT,
    DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT,
    DO_NOT_STOP_AFTER_EXCESSIVE_BULK_FLAG_BIT,
    FLAGS0_SETTING_ID,
    FLAGS1_SETTING_ID,
    DISABLE_GROUND_RELAY_FLAG_BIT,
    POWER_ASSIST_ENABLED_FLAG_BIT,
    REDUCED_FLOAT_ENABLED_FLAG_BIT,
    REMOTE_OVERRULES_AC1_FLAG_BIT,
    REMOTE_OVERRULES_AC2_FLAG_BIT,
    setting_flag_enabled,
    setting_flag_supported,
    setting_flag_value,
    TUBULAR_PLATE_TRACTION_BATTERY_CURVE_FLAG_BIT,
    ups_function_enabled,
    ups_function_supported,
    WEAK_AC_INPUT_ENABLED_FLAG_BIT,
)
from .capabilities import entity_supported
from .const import (
    DOMAIN,
    KEY_CONTEXT,
)
from .remote_panel import charger_enabled_in_mode, mode_with_charger_enabled


class VictronMK3StandbySwitchEntity(RestoreEntity, SwitchEntity):
    _attr_has_entity_name = True

    entity_description = SwitchEntityDescription(
        key="remote_panel_standby",
        name="Remote Panel Standby",
        translation_key="remote_panel_standby",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
    )

    def __init__(self, context: Context):
        self.context = context
        self._attr_device_info = context.device_info
        self._attr_unique_id = f"{context.device_id}-{VictronMK3StandbySwitchEntity.entity_description.key}"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        self._attr_is_on = state.state == STATE_ON if state is not None else True
        await self._notify_controller("switch.remote_panel_standby.restore")

    async def async_turn_on(self) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()
        await self._notify_controller("switch.remote_panel_standby.turn_on")

    async def async_turn_off(self) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
        await self._notify_controller("switch.remote_panel_standby.turn_off")

    async def _notify_controller(self, operation: str) -> None:
        self.context.controller.standby = self._attr_is_on
        await self.context.run_control_action(
            operation,
            self.context.coordinator.async_request_refresh(),
        )


class VictronMK3BatteryMonitorSwitchEntity(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    entity_description = SwitchEntityDescription(
        key="battery_monitor",
        name="Battery Monitor",
        translation_key="battery_monitor",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
    )

    def __init__(self, context: Context):
        CoordinatorEntity.__init__(
            self,
            context.coordinator,
            VictronMK3BatteryMonitorSwitchEntity.entity_description.key,
        )
        self.context = context
        self._attr_device_info = context.device_info
        self._attr_unique_id = (
            f"{context.device_id}-"
            f"{VictronMK3BatteryMonitorSwitchEntity.entity_description.key}"
        )
        self._attr_available = False
        self._attr_is_on = False

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        value = None if data is None else data.battery_monitor_enabled
        if value is None:
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_is_on = value
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self.context.run_control_action(
            "switch.battery_monitor.turn_on",
            _set_battery_monitor_enabled(self.context, True),
        )

    async def async_turn_off(self) -> None:
        await self.context.run_control_action(
            "switch.battery_monitor.turn_off",
            _set_battery_monitor_enabled(self.context, False),
        )


async def _set_battery_monitor_enabled(context: Context, enabled: bool) -> None:
    await context.controller.set_battery_monitor_enabled(enabled)
    await context.coordinator.async_request_refresh()


async def set_charge_enabled(context: Context, enabled: bool) -> None:
    data = context.coordinator.data
    if data is None or data.config is None:
        raise HomeAssistantError("Device is not available")

    mode = data.remote_panel_mode()
    if mode is None:
        raise HomeAssistantError("Device is not available")

    await context.controller.set_remote_panel_state(
        mode_with_charger_enabled(mode, enabled),
        data.config.actual_current_limit,
    )
    await context.coordinator.async_request_refresh()


async def set_power_assist_enabled(context: Context, enabled: bool) -> None:
    await context.controller.set_power_assist_enabled(enabled)
    await context.coordinator.async_request_refresh()


async def set_ups_function_enabled(context: Context, enabled: bool) -> None:
    await context.controller.set_ups_function_enabled(enabled)
    await context.coordinator.async_request_refresh()


async def set_dynamic_current_limiter_enabled(context: Context, enabled: bool) -> None:
    await context.controller.set_dynamic_current_limiter_enabled(enabled)
    await context.coordinator.async_request_refresh()


async def set_weak_ac_input_enabled(context: Context, enabled: bool) -> None:
    await context.controller.set_weak_ac_input_enabled(enabled)
    await context.coordinator.async_request_refresh()


async def set_generic_setting_flag(
    context: Context,
    setting_id: int,
    flag_bit: int,
    enabled: bool,
    name: str,
    *,
    inverted: bool = False,
) -> None:
    await context.controller.set_setting_flag(
        setting_id,
        flag_bit,
        enabled,
        name,
        inverted=inverted,
    )
    await context.coordinator.async_request_refresh()


@dataclass(kw_only=True)
class VictronMK3SettingFlagSwitchEntityDescription(SwitchEntityDescription):
    setting_id: int
    flag_bit: int
    set_fn: Callable[[Context, bool], Awaitable[None]]
    inverted: bool = False


class VictronMK3ChargeEnabledSwitchEntity(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    entity_description = SwitchEntityDescription(
        key="charge_enabled",
        name="Charge Enabled",
        translation_key="charge_enabled",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
    )

    def __init__(self, context: Context):
        CoordinatorEntity.__init__(
            self,
            context.coordinator,
            VictronMK3ChargeEnabledSwitchEntity.entity_description.key,
        )
        self.context = context
        self._attr_device_info = context.device_info
        self._attr_unique_id = (
            f"{context.device_id}-"
            f"{VictronMK3ChargeEnabledSwitchEntity.entity_description.key}"
        )
        self._attr_available = False
        self._attr_is_on = False

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        mode = None if data is None else data.remote_panel_mode()
        if mode is None:
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_is_on = charger_enabled_in_mode(mode)
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self.context.run_control_action(
            "switch.charge_enabled.turn_on",
            set_charge_enabled(self.context, True),
        )

    async def async_turn_off(self) -> None:
        await self.context.run_control_action(
            "switch.charge_enabled.turn_off",
            set_charge_enabled(self.context, False),
        )


class VictronMK3UpsFunctionSwitchEntity(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    entity_description = SwitchEntityDescription(
        key="ups_function",
        name="UPS Function",
        translation_key="ups_function",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
    )

    def __init__(self, context: Context):
        CoordinatorEntity.__init__(
            self,
            context.coordinator,
            VictronMK3UpsFunctionSwitchEntity.entity_description.key,
        )
        self.context = context
        self._attr_device_info = context.device_info
        self._attr_unique_id = (
            f"{context.device_id}-"
            f"{VictronMK3UpsFunctionSwitchEntity.entity_description.key}"
        )
        self._attr_available = False
        self._attr_is_on = False

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        info = None if data is None else data.setting_info.get(FLAGS0_SETTING_ID)
        value = None if data is None else data.setting_values.get(FLAGS0_SETTING_ID)
        is_on = ups_function_enabled(value)
        if not ups_function_supported(info) or is_on is None:
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_is_on = is_on
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self.context.run_control_action(
            "switch.ups_function.turn_on",
            set_ups_function_enabled(self.context, True),
        )

    async def async_turn_off(self) -> None:
        await self.context.run_control_action(
            "switch.ups_function.turn_off",
            set_ups_function_enabled(self.context, False),
        )


SETTING_FLAG_ENTITY_DESCRIPTIONS: tuple[VictronMK3SettingFlagSwitchEntityDescription, ...] = (
    VictronMK3SettingFlagSwitchEntityDescription(
        key="power_assist",
        name="PowerAssist",
        translation_key="power_assist",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS0_SETTING_ID,
        flag_bit=POWER_ASSIST_ENABLED_FLAG_BIT,
        set_fn=set_power_assist_enabled,
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="dynamic_current_limiter",
        name="Dynamic Current Limiter",
        translation_key="dynamic_current_limiter",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS1_SETTING_ID,
        flag_bit=DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT,
        set_fn=set_dynamic_current_limiter_enabled,
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="weak_ac_input",
        name="Weak AC Input",
        translation_key="weak_ac_input",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS0_SETTING_ID,
        flag_bit=WEAK_AC_INPUT_ENABLED_FLAG_BIT,
        set_fn=set_weak_ac_input_enabled,
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="aes",
        name="AES",
        translation_key="aes",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS0_SETTING_ID,
        flag_bit=DISABLE_AES_FLAG_BIT,
        inverted=True,
        set_fn=lambda context, enabled: set_generic_setting_flag(
            context,
            FLAGS0_SETTING_ID,
            DISABLE_AES_FLAG_BIT,
            enabled,
            "AES",
            inverted=True,
        ),
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="stop_after_excessive_bulk",
        name="Stop After Excessive Bulk",
        translation_key="stop_after_excessive_bulk",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS0_SETTING_ID,
        flag_bit=DO_NOT_STOP_AFTER_EXCESSIVE_BULK_FLAG_BIT,
        inverted=True,
        set_fn=lambda context, enabled: set_generic_setting_flag(
            context,
            FLAGS0_SETTING_ID,
            DO_NOT_STOP_AFTER_EXCESSIVE_BULK_FLAG_BIT,
            enabled,
            "Stop After Excessive Bulk",
            inverted=True,
        ),
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="storage_mode",
        name="Storage Mode",
        translation_key="storage_mode",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS0_SETTING_ID,
        flag_bit=REDUCED_FLOAT_ENABLED_FLAG_BIT,
        set_fn=lambda context, enabled: set_generic_setting_flag(
            context,
            FLAGS0_SETTING_ID,
            REDUCED_FLOAT_ENABLED_FLAG_BIT,
            enabled,
            "Storage Mode",
        ),
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="ground_relay",
        name="Ground Relay",
        translation_key="ground_relay",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS0_SETTING_ID,
        flag_bit=DISABLE_GROUND_RELAY_FLAG_BIT,
        inverted=True,
        set_fn=lambda context, enabled: set_generic_setting_flag(
            context,
            FLAGS0_SETTING_ID,
            DISABLE_GROUND_RELAY_FLAG_BIT,
            enabled,
            "Ground Relay",
            inverted=True,
        ),
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="accept_wide_frequency_range",
        name="Accept Wide Frequency Range",
        translation_key="accept_wide_frequency_range",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS1_SETTING_ID,
        flag_bit=ACCEPT_WIDE_INPUT_FREQUENCY_FLAG_BIT,
        set_fn=lambda context, enabled: set_generic_setting_flag(
            context,
            FLAGS1_SETTING_ID,
            ACCEPT_WIDE_INPUT_FREQUENCY_FLAG_BIT,
            enabled,
            "Accept Wide Frequency Range",
        ),
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="remote_overrules_ac1",
        name="Remote Overrules AC1",
        translation_key="remote_overrules_ac1",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS1_SETTING_ID,
        flag_bit=REMOTE_OVERRULES_AC1_FLAG_BIT,
        set_fn=lambda context, enabled: set_generic_setting_flag(
            context,
            FLAGS1_SETTING_ID,
            REMOTE_OVERRULES_AC1_FLAG_BIT,
            enabled,
            "Remote Overrules AC1",
        ),
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="remote_overrules_ac2",
        name="Remote Overrules AC2",
        translation_key="remote_overrules_ac2",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS0_SETTING_ID,
        flag_bit=REMOTE_OVERRULES_AC2_FLAG_BIT,
        set_fn=lambda context, enabled: set_generic_setting_flag(
            context,
            FLAGS0_SETTING_ID,
            REMOTE_OVERRULES_AC2_FLAG_BIT,
            enabled,
            "Remote Overrules AC2",
        ),
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="tubular_plate_traction_battery_curve",
        name="Tubular Plate Traction Battery Curve",
        translation_key="tubular_plate_traction_battery_curve",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS1_SETTING_ID,
        flag_bit=TUBULAR_PLATE_TRACTION_BATTERY_CURVE_FLAG_BIT,
        set_fn=lambda context, enabled: set_generic_setting_flag(
            context,
            FLAGS1_SETTING_ID,
            TUBULAR_PLATE_TRACTION_BATTERY_CURVE_FLAG_BIT,
            enabled,
            "Tubular Plate Traction Battery Curve",
        ),
    ),
    VictronMK3SettingFlagSwitchEntityDescription(
        key="aes_low_power_shutdown",
        name="AES Low Power Shutdown",
        translation_key="aes_low_power_shutdown",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        setting_id=FLAGS1_SETTING_ID,
        flag_bit=AES_LOW_POWER_SHUTDOWN_ENABLED_FLAG_BIT,
        set_fn=lambda context, enabled: set_generic_setting_flag(
            context,
            FLAGS1_SETTING_ID,
            AES_LOW_POWER_SHUTDOWN_ENABLED_FLAG_BIT,
            enabled,
            "AES Low Power Shutdown",
        ),
    ),
)


class VictronMK3SettingFlagSwitchEntity(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        context: Context,
        entity_description: VictronMK3SettingFlagSwitchEntityDescription,
    ):
        CoordinatorEntity.__init__(
            self,
            context.coordinator,
            entity_description.key,
        )
        self.context = context
        self.entity_description = entity_description
        self._attr_device_info = context.device_info
        self._attr_unique_id = f"{context.device_id}-{entity_description.key}"
        self._attr_available = False
        self._attr_is_on = False

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        info = (
            None
            if data is None
            else data.setting_info.get(self.entity_description.setting_id)
        )
        value = (
            None
            if data is None
            else data.setting_values.get(self.entity_description.setting_id)
        )
        is_on = setting_flag_value(
            value,
            self.entity_description.flag_bit,
            inverted=self.entity_description.inverted,
        )
        if (
            not setting_flag_supported(info, self.entity_description.flag_bit)
            or is_on is None
        ):
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_is_on = is_on
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self.context.run_control_action(
            f"switch.{self.entity_description.key}.turn_on",
            self.entity_description.set_fn(self.context, True),
        )

    async def async_turn_off(self) -> None:
        await self.context.run_control_action(
            f"switch.{self.entity_description.key}.turn_off",
            self.entity_description.set_fn(self.context, False),
        )


def _ups_function_entity_supported(context: Context) -> bool:
    capabilities = context.capabilities
    return (
        entity_supported(capabilities, "ups_function")
        and capabilities.supports_setting_flag(
            FLAGS0_SETTING_ID, DISABLE_WAVE_CHECK_FLAG_BIT
        )
        and capabilities.supports_setting_flag(
            FLAGS0_SETTING_ID, DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    context = hass.data[DOMAIN][entry.entry_id][KEY_CONTEXT]
    entities = [VictronMK3StandbySwitchEntity(context)]
    if entity_supported(
        context.capabilities,
        VictronMK3BatteryMonitorSwitchEntity.entity_description.key,
        setting_id=BATTERY_CAPACITY_SETTING_ID,
    ):
        entities.append(VictronMK3BatteryMonitorSwitchEntity(context))
    if entity_supported(
        context.capabilities,
        VictronMK3ChargeEnabledSwitchEntity.entity_description.key,
        setting_flag=(FLAGS0_SETTING_ID, DISABLE_CHARGE_FLAG_BIT),
    ):
        entities.append(VictronMK3ChargeEnabledSwitchEntity(context))
    if _ups_function_entity_supported(context):
        entities.append(VictronMK3UpsFunctionSwitchEntity(context))
    entities.extend(
        VictronMK3SettingFlagSwitchEntity(context, description)
        for description in SETTING_FLAG_ENTITY_DESCRIPTIONS
        if entity_supported(
            context.capabilities,
            description.key,
            setting_flag=(description.setting_id, description.flag_bit),
        )
    )
    async_add_entities(entities)
