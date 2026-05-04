"""The victron_vebus_mk3 integration."""

from __future__ import annotations

from datetime import timedelta
from homeassistant.components.device_automation.exceptions import DeviceNotFound
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
    CONF_DEVICE_ID,
    CONF_MODE,
    CONF_MODEL,
    CONF_PORT,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
import logging
from typing import List
from victron_vebus_mk3_protocol import (
    ACResponse,
    ConfigResponse,
    DCResponse,
    Fault,
    Handler,
    InterfaceFlags,
    InterfaceResponse,
    LEDResponse,
    PowerResponse,
    Response,
    SwitchRegister,
    SwitchState,
    VersionResponse,
    VictronMK3,
    logger,
)
import voluptuous as vol

from .battery_monitor import read_battery_soc, register_battery_soc_variable
from .battery_monitor_settings import (
    DISABLE_CHARGE_FLAG_BIT,
    DISABLE_WAVE_CHECK_FLAG_BIT,
    DISABLE_WAVE_CHECK_INVERTED_FLAG_BIT,
    FLAGS0_SETTING_ID,
    FLAGS1_SETTING_ID,
    MONITORED_SETTING_IDS,
    DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT,
    POWER_ASSIST_ENABLED_FLAG_BIT,
    BATTERY_CAPACITY_SETTING_ID,
    SettingInfo,
    SettingValue,
    battery_monitor_enabled_from_capacity,
    read_setting,
    read_setting_info,
    setting_flag_enabled,
    setting_flag_supported,
    setting_raw_with_flag,
    setting_raw_with_ups_function,
    ups_function_supported,
    WEAK_AC_INPUT_ENABLED_FLAG_BIT,
    write_setting,
    write_setting_raw,
)
from .const import (
    AC_PHASES_POLLED,
    CONF_CURRENT_LIMIT,
    CONF_SERIAL_NUMBER,
    DOMAIN,
    KEY_CONTEXT,
)
from .remote_panel import (
    Mode,
    base_mode_for_remote_panel,
    disable_charge_for_remote_panel,
    enum_options,
    mode_from_value,
    mode_with_disable_charge,
)
from .ram_variables import (
    IGNORE_AC_INPUT_VARIABLE_ID,
    MONITORED_RAM_VARIABLE_IDS,
    RamVariableInfo,
    RamVariableValue,
    ram_variable_bool_supported,
    read_ram_variable,
    read_ram_variable_info,
)
from .vebus_state import (
    ChargeStateAction,
    DeviceChargeState,
    read_device_charge_state,
)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]
UPDATE_INTERVAL = timedelta(seconds=2)


MODE_TO_SWITCH_STATE = {
    Mode.OFF: SwitchState.OFF,
    Mode.ON: SwitchState.ON,
    Mode.CHARGER_ONLY: SwitchState.CHARGER_ONLY,
    Mode.INVERTER_ONLY: SwitchState.INVERTER_ONLY,
}


SERVICE_NAME = "set_remote_panel_state"

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_MODE): vol.In(enum_options(Mode)),
        vol.Optional(CONF_CURRENT_LIMIT): vol.Coerce(float),
    }
)


class Data:
    def __init__(self) -> None:
        self.ac: List[ACResponse | None] = [None] * AC_PHASES_POLLED
        self.battery_monitor_enabled: bool | None = None
        self.battery_soc: float | None = None
        self.config: ConfigResponse | None = None
        self.dc: DCResponse | None = None
        self.device_charge_state: DeviceChargeState | None = None
        self.interface: InterfaceResponse | None = None
        self.led: LEDResponse | None = None
        self.power: PowerResponse | None = None
        self.ram_variable_info: dict[int, RamVariableInfo] = {}
        self.ram_variable_values: dict[int, RamVariableValue] = {}
        self.setting_info: dict[int, SettingInfo] = {}
        self.setting_values: dict[int, SettingValue] = {}
        self.version: VersionResponse | None = None

    def front_panel_mode(self) -> Mode | None:
        if self.config is None:
            return None
        reg = self.config.switch_register
        if reg & SwitchRegister.FRONT_SWITCH_UP != 0:
            return Mode.ON
        if reg & SwitchRegister.FRONT_SWITCH_DOWN != 0:
            return Mode.CHARGER_ONLY
        return Mode.OFF

    def remote_panel_mode(self) -> Mode | None:
        if self.config is None:
            return None
        reg = self.config.switch_register
        charge_disabled = setting_flag_enabled(
            self.setting_values.get(FLAGS0_SETTING_ID),
            DISABLE_CHARGE_FLAG_BIT,
        )
        if reg & SwitchRegister.DIRECT_REMOTE_SWITCH_CHARGE != 0:
            if reg & SwitchRegister.DIRECT_REMOTE_SWITCH_INVERT != 0:
                return mode_with_disable_charge(Mode.ON, charge_disabled is True)
            else:
                return Mode.CHARGER_ONLY
        else:
            if reg & SwitchRegister.DIRECT_REMOTE_SWITCH_INVERT != 0:
                return Mode.INVERTER_ONLY
            else:
                return Mode.OFF

    def actual_mode(self) -> Mode | None:
        if self.config is None:
            return None
        reg = self.config.switch_register
        charge_disabled = setting_flag_enabled(
            self.setting_values.get(FLAGS0_SETTING_ID),
            DISABLE_CHARGE_FLAG_BIT,
        )
        if reg & SwitchRegister.SWITCH_CHARGE != 0:
            if reg & SwitchRegister.SWITCH_INVERT != 0:
                return mode_with_disable_charge(Mode.ON, charge_disabled is True)
            else:
                return Mode.CHARGER_ONLY
        else:
            if reg & SwitchRegister.SWITCH_INVERT != 0:
                return Mode.INVERTER_ONLY
            else:
                return Mode.OFF


class Controller(Handler):
    def __init__(self, port: str) -> None:
        self._mk3 = VictronMK3(port)
        self._fault: Fault | None = None
        self._idle = False
        self._ram_variable_info: dict[int, RamVariableInfo] = {}
        self._setting_info: dict[int, SettingInfo] = {}
        self._last_battery_capacity: float | None = None
        self._version: VersionResponse | None = None
        self.standby: bool | None = None
        self.ac_entities = [[] for _ in range(0, AC_PHASES_POLLED)]

    async def start(self) -> None:
        await self._mk3.start(self)
        register_battery_soc_variable(self._mk3)

    async def stop(self) -> None:
        await self._mk3.stop()

    def on_response(self, response: Response) -> None:
        response.log(logger, logging.DEBUG)
        self._idle = False
        # We don't need to query the version because the interface delivers it every second.
        if isinstance(response, VersionResponse):
            self._version = response

    def on_idle(self) -> None:
        logger.debug("Idle")
        self._idle = True

    def on_fault(self, fault: Fault) -> None:
        if fault == Fault.EXCEPTION:
            logger.exception("Unhandled exception in handler")
        else:
            logger.error(f"Communication fault: {fault}")
        self._fault = fault

    async def update(self) -> Data:
        if self._fault is not None:
            raise UpdateFailed(f"Communication fault: {self._fault}")
        if self._idle:
            raise UpdateFailed("Device is asleep")

        register_battery_soc_variable(self._mk3)

        if self.standby is not None:
            flags = InterfaceFlags.PANEL_DETECT
            if self.standby:
                flags |= InterfaceFlags.STANDBY
            data_interface = await self._mk3.send_interface_request(flags)
        else:
            data_interface = await self._mk3.send_interface_request()

        data = Data()
        data.interface = data_interface
        data.version = self._version
        data.led = await self._mk3.send_led_request()
        data.dc = await self._mk3.send_dc_request()
        for phase in range(1, AC_PHASES_POLLED + 1):
            # It might be nice to optimize the polling based on AC_Response.ac_num_phases
            # but it seems to report an incorrect number of phases on some devices so instead
            # we only poll phases that are associated with enabled entities.
            index = phase - 1
            data.ac[index] = (
                await self._mk3.send_ac_request(phase)
                if any(x.enabled for x in self.ac_entities[index])
                else None
            )
        data.power = await self._mk3.send_power_request()
        await self._update_settings(data)
        await self._update_ram_variables(data)
        try:
            data.device_charge_state = await read_device_charge_state(self._mk3)
        except Exception:
            logger.debug("Failed to read detailed charge state", exc_info=True)
        try:
            if data.battery_monitor_enabled:
                data.battery_soc = await read_battery_soc(self._mk3)
        except Exception:
            logger.debug("Failed to read battery state of charge", exc_info=True)
        data.config = await self._mk3.send_config_request()
        return data

    async def set_remote_panel_state(
        self, mode: Mode, current_limit: float | None
    ) -> None:
        await self._set_setting_flag(
            FLAGS0_SETTING_ID,
            DISABLE_CHARGE_FLAG_BIT,
            disable_charge_for_remote_panel(mode),
            "Charge Enabled",
            inverted=False,
        )
        await self._mk3.send_state_request(
            MODE_TO_SWITCH_STATE[base_mode_for_remote_panel(mode)],
            current_limit,
        )

    async def set_battery_monitor_enabled(self, enabled: bool) -> None:
        target_capacity = 0 if not enabled else self._last_battery_capacity
        if enabled and (target_capacity is None or target_capacity <= 0):
            raise HomeAssistantError(
                "Set Battery Capacity to a value greater than 0 before enabling Battery Monitor"
            )

        await self.set_battery_monitor_setting(
            BATTERY_CAPACITY_SETTING_ID,
            float(target_capacity),
        )

    async def set_setting(self, setting_id: int, value: float) -> None:
        info = await self._get_setting_info(setting_id)
        result = await write_setting(self._mk3, setting_id, value, info)
        if result is None or not result.supported:
            raise HomeAssistantError(f"Setting {setting_id} is not available")

        if (
            setting_id == BATTERY_CAPACITY_SETTING_ID
            and result.value is not None
            and result.value > 0
        ):
            self._last_battery_capacity = result.value

    async def set_battery_monitor_setting(self, setting_id: int, value: float) -> None:
        await self.set_setting(setting_id, value)

    async def set_power_assist_enabled(self, enabled: bool) -> None:
        await self._set_setting_flag(
            FLAGS0_SETTING_ID,
            POWER_ASSIST_ENABLED_FLAG_BIT,
            enabled,
            "PowerAssist",
        )

    async def set_ups_function_enabled(self, enabled: bool) -> None:
        info = await self._get_setting_info(FLAGS0_SETTING_ID)
        if not ups_function_supported(info):
            raise HomeAssistantError("UPS Function is not available")

        value = await read_setting(self._mk3, FLAGS0_SETTING_ID, info)
        if value is None or not value.supported or value.raw_value is None:
            raise HomeAssistantError("UPS Function is not available")

        result = await write_setting_raw(
            self._mk3,
            FLAGS0_SETTING_ID,
            setting_raw_with_ups_function(value.raw_value, enabled),
            info,
        )
        if result is None or not result.supported:
            raise HomeAssistantError("UPS Function is not available")

    async def set_dynamic_current_limiter_enabled(self, enabled: bool) -> None:
        await self._set_setting_flag(
            FLAGS1_SETTING_ID,
            DYNAMIC_CURRENT_LIMITER_ENABLED_FLAG_BIT,
            enabled,
            "Dynamic Current Limiter",
        )

    async def set_weak_ac_input_enabled(self, enabled: bool) -> None:
        await self._set_setting_flag(
            FLAGS0_SETTING_ID,
            WEAK_AC_INPUT_ENABLED_FLAG_BIT,
            enabled,
            "Weak AC Input",
        )

    async def set_setting_flag(
        self,
        setting_id: int,
        flag_bit: int,
        enabled: bool,
        name: str,
        *,
        inverted: bool = False,
    ) -> None:
        await self._set_setting_flag(
            setting_id,
            flag_bit,
            enabled,
            name,
            inverted=inverted,
        )

    async def force_charge_state(self, action: ChargeStateAction, name: str) -> None:
        result = await read_device_charge_state(self._mk3, action)
        if result is None:
            raise HomeAssistantError(f"{name} is not available")

    async def set_ignore_ac_input_enabled(self, enabled: bool) -> None:
        raise HomeAssistantError(
            "Ignore AC Input is reported as state only on this device"
        )

    async def _set_setting_flag(
        self,
        setting_id: int,
        flag_bit: int,
        enabled: bool,
        name: str,
        *,
        inverted: bool = False,
    ) -> None:
        info = await self._get_setting_info(setting_id)
        if not setting_flag_supported(info, flag_bit):
            raise HomeAssistantError(f"{name} is not available")

        value = await read_setting(self._mk3, setting_id, info)
        if value is None or not value.supported or value.raw_value is None:
            raise HomeAssistantError(f"{name} is not available")

        result = await write_setting_raw(
            self._mk3,
            setting_id,
            setting_raw_with_flag(
                value.raw_value,
                flag_bit,
                not enabled if inverted else enabled,
            ),
            info,
        )
        if result is None or not result.supported:
            raise HomeAssistantError(f"{name} is not available")

    async def _get_ram_variable_info(self, variable_id: int) -> RamVariableInfo | None:
        info = self._ram_variable_info.get(variable_id)
        if info is None:
            info = await read_ram_variable_info(self._mk3, variable_id)
            if info is not None:
                self._ram_variable_info[variable_id] = info
        return info

    async def _get_setting_info(self, setting_id: int) -> SettingInfo | None:
        info = self._setting_info.get(setting_id)
        if info is None:
            info = await read_setting_info(self._mk3, setting_id)
            if info is not None:
                self._setting_info[setting_id] = info
        return info

    async def _update_settings(self, data: Data) -> None:
        for setting_id in MONITORED_SETTING_IDS:
            try:
                info = await self._get_setting_info(setting_id)
                if info is None:
                    continue
                data.setting_info[setting_id] = info

                value = await read_setting(self._mk3, setting_id, info)
                if value is None:
                    continue
                data.setting_values[setting_id] = value

                if (
                    setting_id == BATTERY_CAPACITY_SETTING_ID
                    and value.supported
                    and value.value is not None
                    and value.value > 0
                ):
                    self._last_battery_capacity = value.value
            except Exception:
                logger.debug(
                    "Failed to read setting %s",
                    setting_id,
                    exc_info=True,
                )

        capacity = data.setting_values.get(BATTERY_CAPACITY_SETTING_ID)
        data.battery_monitor_enabled = (
            None
            if capacity is None or not capacity.supported
            else battery_monitor_enabled_from_capacity(capacity.value)
        )

    async def _update_ram_variables(self, data: Data) -> None:
        for variable_id in MONITORED_RAM_VARIABLE_IDS:
            try:
                info = await self._get_ram_variable_info(variable_id)
                if info is None:
                    continue
                data.ram_variable_info[variable_id] = info

                value = await read_ram_variable(self._mk3, variable_id, info)
                if value is None:
                    continue
                data.ram_variable_values[variable_id] = value
            except Exception:
                logger.debug(
                    "Failed to read RAM variable %s",
                    variable_id,
                    exc_info=True,
                )


class Context:
    def __init__(
        self,
        controller: Controller,
        coordinator: DataUpdateCoordinator[Data],
        device_id: str,
        device_info: DeviceInfo,
    ) -> None:
        self.controller = controller
        self.coordinator = coordinator
        self.device_id = device_id
        self.device_info = device_info


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    port = entry.data[CONF_PORT]
    controller = Controller(port)

    coordinator = DataUpdateCoordinator[Data](
        hass,
        logger,
        name=DOMAIN,
        update_interval=UPDATE_INTERVAL,
        update_method=controller.update,
    )

    device = device_registry.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        name=entry.title,
        manufacturer="Victron Energy",
        model=entry.data.get(CONF_MODEL, None),
        serial_number=entry.data.get(CONF_SERIAL_NUMBER, None),
        identifiers={(DOMAIN, port)},
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        KEY_CONTEXT: Context(
            controller, coordinator, device.id, DeviceInfo(identifiers={(DOMAIN, port)})
        )
    }

    await controller.start()
    entry.async_on_unload(controller.stop)

    await coordinator.async_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await _async_setup_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_setup_services(hass: HomeAssistant) -> None:
    async def _handle_set_remote_panel_state(call: ServiceCall) -> None:
        device_id = call.data[CONF_DEVICE_ID]
        mode = mode_from_value(call.data[CONF_MODE])
        current_limit = call.data.get(CONF_CURRENT_LIMIT, None)
        await set_remote_panel_state(hass, device_id, mode, current_limit)

    hass.services.async_register(
        DOMAIN,
        SERVICE_NAME,
        _handle_set_remote_panel_state,
        schema=SERVICE_SCHEMA,
    )


async def set_remote_panel_state(
    hass: HomeAssistant, device_id: str, mode: Mode, current_limit: float | None
) -> None:
    device = device_registry.async_get(hass).async_get(device_id)
    if device is None:
        raise DeviceNotFound(f"Device ID {device_id} is not valid")

    for entry_id in device.config_entries:
        entry_data = hass.data[DOMAIN].get(entry_id, None)
        if entry_data is not None:
            context = entry_data[KEY_CONTEXT]
            await context.controller.set_remote_panel_state(mode, current_limit)
            await context.coordinator.async_request_refresh()
            return

    raise HomeAssistantError(f"Device ID {device_id} cannot handle this request")
