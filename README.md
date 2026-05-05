# Victron VE.Bus MK3 Control

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

Local Home Assistant monitoring and control for Victron VE.Bus inverter/chargers and inverter-only devices through the Victron MK3-USB interface.

Use this integration when you want Home Assistant to read useful VE.Bus data, set remote panel mode, adjust supported current limits, and expose safe configuration controls without a GX device or cloud account.

Full setup, safety notes, troubleshooting, and entity explanations are in the [project wiki](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki).

## Highlights

- Compatible with supported VE.Bus inverter/chargers such as MultiPlus/Quattro units and VE.Bus inverter-only units such as Phoenix/Inverter Compact models.
- AC input/output, battery, power, energy, indicator, and diagnostic sensors.
- Remote panel mode control: `on`, `off`, `charger_only`, `inverter_only`, and `pass_through`; inverter-only units show only `off` and `on`.
- Home Assistant Energy battery tracking with charge/discharge power and cumulative battery energy sensors.
- Supported VE.Bus setting switches, numbers, selects, and buttons. On inverter-only units, charger-specific entities are not applicable.
- `victron_vebus_mk3.set_remote_panel_state` service for automations.

## Install

Open the repository directly in HACS:

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=usersaynoso&repository=victron-vebus-mk3-control&category=integration)

Or install it manually through HACS:

1. In HACS, add this repository as a custom integration repository:
   `https://github.com/usersaynoso/victron-vebus-mk3-control`
2. Install **Victron VE.Bus MK3 Control**.
3. Restart Home Assistant.
4. Plug in the Victron MK3-USB interface.
5. Go to Settings -> Devices & services and add **Victron VE.Bus MK3 Control**.
6. If it is not auto-discovered, enter or select the MK3-USB serial device path in the setup form.

Manual installation is also supported by copying `custom_components/victron_vebus_mk3` into Home Assistant's `custom_components` directory. See the [Installation wiki page](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/Installation) for details.

## Safety

This integration can change real inverter or inverter/charger behaviour. Check battery voltages, charge current, input limits, and advanced settings against your battery manual or installer settings before changing them. Hardware controls and external panels may override Home Assistant, so use `Actual Mode` as the source of truth when the requested mode and actual behaviour differ.

## Polling And Entity Load

The integration polls the MK3 interface every 2 seconds by default. You can change this in the integration options under Settings -> Devices & services -> Victron VE.Bus MK3 Control -> Configure. The minimum is 1 second.

Shorter intervals make dashboards react faster, but they also create more Home Assistant state updates and recorder work. If Home Assistant runs on a low-memory device, increase the interval before enabling extra diagnostic or additional AC phase entities.

Some entities are disabled by default on purpose. Low-level diagnostics and L2-L4 AC phase sensors are available for systems that need them, but keeping them off avoids unnecessary polling and database writes on typical single-phase systems.

## Reporting Issues

If you need help with a problem, download diagnostics before opening a GitHub issue: Settings -> Devices & services -> Victron VE.Bus MK3 Control -> three-dot menu -> Download diagnostics. Attach that file to the required GitHub issue form so the report includes redacted VE.Bus data, entity states, and recent integration errors.

## Remote Panel Modes

| Mode | Request |
| --- | --- |
| `on` | Enable charger and inverter. |
| `off` | Disable charger and inverter. |
| `charger_only` | Enable charger and disable inverter. |
| `inverter_only` | Enable inverter and disable charger. |
| `pass_through` | Disable charging while keeping pass-through available when incoming AC is present. |

On inverter-only VE.Bus units, Home Assistant shows a simpler `off` and `on` remote panel control. Charger modes and charger-specific entities are hidden when the connected device explicitly reports that it does not support them.

## Entity Inventory

The tables below list possible entity keys exposed by the integration. The connected device's VE.Bus capabilities decide which entities are created; unsupported charger or AC-input entities are hidden. The detailed purpose, options, and safety guidance for each entity are in the [Entities Reference wiki page](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/Entities-Reference).

### Sensors

| Entity key | Name |
| --- | --- |
| `ac_input_voltage` | AC Input Voltage |
| `ac_input_current` | AC Input Current |
| `ac_input_power` | AC Input Power |
| `ac_input_frequency` | AC Input Frequency |
| `ac_output_voltage` | AC Output Voltage |
| `ac_output_current` | AC Output Current |
| `ac_output_power` | AC Output Power |
| `ac_output_frequency` | AC Output Frequency |
| `ac_input_voltage_l2` | AC Input Voltage L2 |
| `ac_input_current_l2` | AC Input Current L2 |
| `ac_output_voltage_l2` | AC Output Voltage L2 |
| `ac_output_current_l2` | AC Output Current L2 |
| `ac_input_voltage_l3` | AC Input Voltage L3 |
| `ac_input_current_l3` | AC Input Current L3 |
| `ac_output_voltage_l3` | AC Output Voltage L3 |
| `ac_output_current_l3` | AC Output Current L3 |
| `ac_input_voltage_l4` | AC Input Voltage L4 |
| `ac_input_current_l4` | AC Input Current L4 |
| `ac_output_voltage_l4` | AC Output Voltage L4 |
| `ac_output_current_l4` | AC Output Current L4 |
| `ac_input_current_limit` | AC Input Current Limit |
| `ac_input_current_limit_maximum` | AC Input Current Limit Maximum |
| `ac_input_current_limit_minimum` | AC Input Current Limit Minimum |
| `last_active_ac_input` | Last Active AC Input |
| `number_of_ac_inputs` | Number Of AC Inputs |
| `reported_ac_number_of_phases` | Reported AC Number Of Phases |
| `interface_flags` | Interface Flags |
| `battery_voltage` | Battery Voltage |
| `battery_ripple_voltage` | Battery Ripple Voltage |
| `battery_power` | Battery Power |
| `battery_charge_discharge_power` | Battery Charge Discharge Power |
| `battery_state_of_charge` | Battery State of Charge |
| `battery_charger_current` | Battery Charger Current |
| `battery_inverter_current` | Battery Inverter Current |
| `signed_ac_load_current` | Signed AC Load Current |
| `device_state` | Device State |
| `vebus_charge_state` | Detailed Charge State |
| `firmware_version` | Firmware Version |
| `lit_indicators` | Lit Indicators |
| `blinking_indicators` | Blinking Indicators |
| `front_panel_mode` | Front Panel Mode |
| `ignore_ac_input_state` | Ignore AC Input State |
| `actual_mode` | Actual Mode |
| `battery_energy_into` | Battery Energy Into |
| `battery_energy_out_of` | Battery Energy Out Of |

### Binary Sensors

| Entity key | Name |
| --- | --- |
| `mains_indicator` | Mains Indicator |
| `bulk_indicator` | Bulk Indicator |
| `absorption_indicator` | Absorption Indicator |
| `float_indicator` | Float Indicator |
| `inverter_indicator` | Inverter Indicator |
| `overload_indicator` | Overload Indicator |
| `low_battery_indicator` | Low Battery Indicator |
| `temperature_indicator` | Temperature Indicator |
| `remote_panel_detected` | Remote Panel Detected |
| `current_limit_controlled_by_panel` | Current Limit Controlled By Panel |
| `external_control_panel_dedicated` | External Control Panel Dedicated |
| `remote_generator_selected_state` | Remote Generator Selected State |
| `onboard_remote_inverter_switch` | Onboard Remote Inverter Switch |
| `interface_panel_detect` | Interface Panel Detect |
| `interface_standby` | Interface Standby |
| `virtual_switch_position` | Virtual Switch Position |
| `multi_functional_relay_state` | Multi-functional Relay State |

### Switches

| Entity key | Name |
| --- | --- |
| `remote_panel_standby` | Remote Panel Standby |
| `battery_monitor` | Battery Monitor |
| `charge_enabled` | Charge Enabled |
| `ups_function` | UPS Function |
| `power_assist` | PowerAssist |
| `dynamic_current_limiter` | Dynamic Current Limiter |
| `weak_ac_input` | Weak AC Input |
| `aes` | AES |
| `stop_after_excessive_bulk` | Stop After Excessive Bulk |
| `storage_mode` | Storage Mode |
| `ground_relay` | Ground Relay |
| `accept_wide_frequency_range` | Accept Wide Frequency Range |
| `remote_overrules_ac1` | Remote Overrules AC1 |
| `remote_overrules_ac2` | Remote Overrules AC2 |
| `tubular_plate_traction_battery_curve` | Tubular Plate Traction Battery Curve |
| `aes_low_power_shutdown` | AES Low Power Shutdown |

### Numbers

| Entity key | Name |
| --- | --- |
| `remote_panel_current_limit` | Remote Panel Current Limit |
| `ac1_input_current_limit` | AC1 Input Current Limit |
| `ac2_input_current_limit` | AC2 Input Current Limit |
| `absorption_voltage` | Absorption Voltage |
| `float_voltage` | Float Voltage |
| `charge_current` | Charge Current |
| `inverter_output_voltage` | Inverter Output Voltage |
| `repeated_absorption_time` | Repeated Absorption Time |
| `repeated_absorption_interval` | Repeated Absorption Interval |
| `maximum_absorption_time` | Maximum Absorption Time |
| `battery_capacity` | Battery Capacity |
| `battery_soc_when_bulk_finished` | State of Charge When Bulk Finished |
| `battery_charge_efficiency` | Charge Efficiency |
| `dc_input_low_shutdown` | DC Input Low Shut-down |
| `dc_input_low_restart` | DC Input Low Restart |
| `dc_input_low_pre_alarm` | DC Input Low Pre-alarm |
| `assist_current_boost_factor` | Assist Current Boost Factor |
| `aes_low_current_limit` | AES Low Current Limit |
| `aes_current_hysteresis` | AES Current Hysteresis |

### Selects

| Entity key | Name |
| --- | --- |
| `remote_panel_mode` | Remote Panel Mode |

### Buttons

| Entity key | Name |
| --- | --- |
| `force_equalise` | Force Equalise |
| `force_absorption` | Force Absorption |
| `force_float` | Force Float |

## Home Assistant Energy

For battery storage, use:

| Home Assistant setting | Entity |
| --- | --- |
| Energy charged | `Battery Energy Into` |
| Energy discharged | `Battery Energy Out Of` |
| Power measurement | `Battery Charge Discharge Power` |
| Direction | `Standard` |

`AC Input Power` can be used as an instantaneous grid-side power sensor only when the VE.Bus device measures the same grid connection point you want Home Assistant to display. See the [Energy Dashboard wiki page](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/Energy-Dashboard).

## Service

The `victron_vebus_mk3.set_remote_panel_state` service sets remote panel mode and optionally sets the current limit at the same time.

```yaml
action: victron_vebus_mk3.set_remote_panel_state
data:
  device_id: 54b361121006d7658fa486a9ebaf02bc
  mode: "charger_only"
  current_limit: 12.5
```

## Documentation

- [Installation](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/Installation)
- [First Setup](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/First-Setup)
- [Safe Control Guide](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/Safe-Control-Guide)
- [Entities Reference](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/Entities-Reference)
- [Energy Dashboard](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/Energy-Dashboard)
- [Services and Automations](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/Services-and-Automations)
- [Troubleshooting](https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/Troubleshooting)

## License

This project is MIT licensed. The license file preserves required copyright notices for original and current work; those notices identify copyright in contributed portions and do not imply ownership of the entire current repository by any one contributor.

Victron Energy, VE.Bus, MultiPlus, Quattro, and MK3-USB are Victron Energy names used here to describe compatible equipment. This project is independent and is not an official Victron Energy integration.
