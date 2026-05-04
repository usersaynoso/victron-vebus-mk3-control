# Entities Reference

These are the possible MK3-readable and MK3-writable entities exposed in Home Assistant. The connected VE.Bus device decides which ones are created: unsupported charger, AC-input, current-limit, or setting entities are hidden. Read-only entities only show what the device reports. Configuration entities and buttons change device behavior, so use the guidance in the last column before changing them.

## Sensors

| Entity key | Name | What it means and why you might care | States, options, and changing guidance |
| --- | --- | --- | --- |
| `ac_input_voltage` | AC Input Voltage | Shows the incoming mains, shore, or generator voltage on the main input. This helps you see whether outside power is present and healthy. | Read-only. |
| `ac_input_current` | AC Input Current | Shows how much current the unit is taking from the main incoming power source. This helps you avoid overloading a shore hookup or generator. | Read-only. |
| `ac_input_power` | AC Input Power | Shows the total power moving through the incoming power side. Positive usually means power is being used from the input; negative can mean power is flowing back toward the input. | Read-only. Use this for Home Assistant grid power only if the Victron unit measures the same grid point you want to track. |
| `ac_input_frequency` | AC Input Frequency | Shows how steady the incoming AC power timing is. This is useful for checking generator or shore power quality. | Read-only. |
| `ac_output_voltage` | AC Output Voltage | Shows the voltage being supplied to your loads from the unit output. This helps confirm that the unit is powering connected circuits correctly. | Read-only. |
| `ac_output_current` | AC Output Current | Shows how much current your connected loads are using from the unit output. This helps you understand load size. | Read-only. |
| `ac_output_power` | AC Output Power | Shows the power being delivered to the loads connected after the unit. This is a quick view of how much the protected circuits are using. | Read-only. |
| `ac_output_frequency` | AC Output Frequency | Shows the AC timing on the unit output. This helps confirm that the output power looks normal. | Read-only. |
| `ac_input_voltage_l2` | AC Input Voltage L2 | Shows incoming voltage on input line 2. A line is one separate live feed in a larger electrical system. | Read-only. Disabled by default because most users do not need extra lines. |
| `ac_input_current_l2` | AC Input Current L2 | Shows how much current input line 2 is taking from mains, shore, or generator power. | Read-only. Disabled by default. |
| `ac_output_voltage_l2` | AC Output Voltage L2 | Shows output voltage on line 2, for systems that report more than one output line. | Read-only. Disabled by default. |
| `ac_output_current_l2` | AC Output Current L2 | Shows output current on line 2, for systems that report more than one output line. | Read-only. Disabled by default. |
| `ac_input_voltage_l3` | AC Input Voltage L3 | Shows incoming voltage on input line 3. This is only useful on systems with more than two live lines. | Read-only. Disabled by default. |
| `ac_input_current_l3` | AC Input Current L3 | Shows incoming current on line 3. | Read-only. Disabled by default. |
| `ac_output_voltage_l3` | AC Output Voltage L3 | Shows output voltage on line 3. | Read-only. Disabled by default. |
| `ac_output_current_l3` | AC Output Current L3 | Shows output current on line 3. | Read-only. Disabled by default. |
| `ac_input_voltage_l4` | AC Input Voltage L4 | Shows incoming voltage on line 4 when a device reports it. This is rare and normally only useful for advanced installations. | Read-only. Disabled by default. |
| `ac_input_current_l4` | AC Input Current L4 | Shows incoming current on line 4 when a device reports it. | Read-only. Disabled by default. |
| `ac_output_voltage_l4` | AC Output Voltage L4 | Shows output voltage on line 4 when a device reports it. | Read-only. Disabled by default. |
| `ac_output_current_l4` | AC Output Current L4 | Shows output current on line 4 when a device reports it. | Read-only. Disabled by default. |
| `ac_input_current_limit` | AC Input Current Limit | Shows the current limit currently being applied to incoming power. This matters because it controls how much the unit may draw from shore power or a generator. | Read-only. Change the writable current limit entities if you need to adjust it. |
| `ac_input_current_limit_maximum` | AC Input Current Limit Maximum | Shows the highest incoming current limit the connected device reports. | Read-only. Use it as a guide for safe values. |
| `ac_input_current_limit_minimum` | AC Input Current Limit Minimum | Shows the lowest incoming current limit the connected device reports. | Read-only. Use it as a guide for safe values. |
| `last_active_ac_input` | Last Active AC Input | Shows which incoming power input was used most recently. This is useful on units that can switch between more than one shore, grid, or generator input. | Read-only. Options are AC input 1, AC input 2, AC input 3, AC input 4, or Unknown. |
| `number_of_ac_inputs` | Number Of AC Inputs | Shows how many incoming power inputs the unit reports. This helps explain why some input controls may or may not appear. | Read-only. |
| `reported_ac_number_of_phases` | Reported AC Number Of Phases | Shows how many live AC lines the unit reports for the first input. A phase is one live AC line in a larger electrical system, and this can help diagnose larger installations. | Read-only. Disabled by default because ordinary users rarely need it. |
| `interface_flags` | Interface Flags | Shows a raw diagnostic number from the MK3 USB adaptor. It is mainly useful when troubleshooting with developers. | Read-only. Disabled by default. |
| `battery_voltage` | Battery Voltage | Shows the battery voltage the unit sees. This helps you spot a low or unusually high battery. | Read-only. |
| `battery_ripple_voltage` | Battery Ripple Voltage | Shows small repeated wobble in battery voltage. A high value can point to loose wiring, stressed batteries, or heavy pulsing loads. | Read-only. |
| `battery_power` | Battery Power | Shows power at the battery using the device's own sign direction. Positive means charging and negative means discharging. | Read-only. |
| `battery_charge_discharge_power` | Battery Charge Discharge Power | Shows the same battery power with the sign direction used by Home Assistant's battery energy view. Positive means discharging and negative means charging. | Read-only. Use this for Home Assistant Energy battery power. |
| `battery_state_of_charge` | Battery State of Charge | Shows how full the battery is as a percentage. It is available when the device battery monitor is enabled and supported. | Read-only. |
| `battery_charger_current` | Battery Charger Current | Shows current going from the charger into the battery. This helps you see charging strength. | Read-only. |
| `battery_inverter_current` | Battery Inverter Current | Shows current going from the battery into the inverter side. This helps you see battery use while powering loads. | Read-only. |
| `signed_ac_load_current` | Signed AC Load Current | Shows load current with a plus or minus sign so advanced users can see direction. Most users can leave it hidden. | Read-only. Disabled by default. |
| `device_state` | Device State | Shows the broad operating state of the unit. It helps explain whether the unit is off, charging, inverting, passing power through, or starting up. | Read-only. Options include Down, Starting, Off, Linked unit, Inverting at full power, Inverting at reduced power, Inverter energy saving, Helping AC input with battery power, Passing AC through, and Charging. |
| `vebus_charge_state` | Detailed Charge State | Shows the detailed charging stage reported by the unit. This helps explain what kind of battery charging is happening right now. | Read-only. Options include Not charging, Starting charge check, Fast charging, Finishing charge, Maintaining full battery, Long-term battery care, Scheduled top-up charge, Forced finishing charge, Battery balancing charge, Fast charging stopped, and Unknown. |
| `firmware_version` | Firmware Version | Shows the firmware version reported by the unit. This is useful when comparing behavior or reporting issues. | Read-only. |
| `lit_indicators` | Lit Indicators | Shows which front-panel indicator lights are on. It is kept for compatibility and gives a combined status view. | Read-only. Values may include Mains, Bulk, Absorption, Float, Inverter, Overload, Low battery, and Temperature. Use the individual indicator entities below for simple yes/no automations. |
| `blinking_indicators` | Blinking Indicators | Shows which front-panel indicator lights are blinking. Blinking usually means the unit is showing a warning, progress, or special state. | Read-only. Values may include Mains, Bulk, Absorption, Float, Inverter, Overload, Low battery, and Temperature. Use the individual indicator entities below for simple yes/no automations. |
| `front_panel_mode` | Front Panel Mode | Shows the position the physical front switch appears to request. This helps explain why Home Assistant commands may not take effect. | Read-only. Options are Off, On, and Charger only. |
| `ignore_ac_input_state` | Ignore AC Input State | Shows whether the unit is currently ignoring incoming AC power. This can explain why it stays on battery even when mains, shore, or generator power is present. | Read-only. Off means the input can be used. On means the input is being ignored. |
| `actual_mode` | Actual Mode | Shows what the unit is actually doing after the physical switch and other inputs are considered. This is often the best status entity for dashboards. | Read-only. Options are Off, On, Charger only, Inverter only, and Pass through. |
| `battery_energy_into` | Battery Energy Into | Adds up energy charged into the battery over time. This is useful for Home Assistant Energy battery tracking. | Read-only total. Restored after restart. |
| `battery_energy_out_of` | Battery Energy Out Of | Adds up energy taken out of the battery over time. This is useful for Home Assistant Energy battery tracking. | Read-only total. Restored after restart. |

## Binary Sensors

| Entity key | Name | What it means and why you might care | States, options, and changing guidance |
| --- | --- | --- | --- |
| `mains_indicator` | Mains Indicator | Shows whether the mains or shore power indicator light is active. This is easier to automate than the combined indicator sensor. | Read-only. On means the indicator is lit or blinking. Off means it is not active. |
| `bulk_indicator` | Bulk Indicator | Shows whether the fast-charging indicator light is active. This helps you see when the battery is in the main charging stage. | Read-only. On means the indicator is lit or blinking. |
| `absorption_indicator` | Absorption Indicator | Shows whether the finishing-charge indicator light is active. This means the battery is being held near full to finish charging. | Read-only. On means the indicator is lit or blinking. |
| `float_indicator` | Float Indicator | Shows whether the battery-maintenance indicator light is active. This usually means the battery is full and being gently maintained. | Read-only. On means the indicator is lit or blinking. |
| `inverter_indicator` | Inverter Indicator | Shows whether the inverter indicator light is active. This helps you see whether the unit is supplying power from the battery side. | Read-only. On means the indicator is lit or blinking. |
| `overload_indicator` | Overload Indicator | Shows whether the overload warning light is active. This can mean connected loads are asking for too much power. | Read-only. On means the indicator is lit or blinking and should be checked. |
| `low_battery_indicator` | Low Battery Indicator | Shows whether the low battery warning light is active. This can mean the battery is low or under heavy strain. | Read-only. On means the indicator is lit or blinking and should be checked. |
| `temperature_indicator` | Temperature Indicator | Shows whether the temperature warning light is active. This can mean the unit is hot or has reduced output to protect itself. | Read-only. On means the indicator is lit or blinking and should be checked. |
| `remote_panel_detected` | Remote Panel Detected | Shows whether the unit detects a remote control panel or equivalent control connection. This helps explain who is controlling the unit. | Read-only. On means a remote panel is detected. |
| `current_limit_controlled_by_panel` | Current Limit Controlled By Panel | Shows whether an external panel is currently setting the incoming current limit. This matters because Home Assistant may not be the only controller. | Read-only. On means the external panel is controlling the limit. |
| `external_control_panel_dedicated` | External Control Panel Dedicated | Shows whether the connected external control panel is treated as the dedicated controller for the unit. | Read-only. On means the external panel has a dedicated control role. |
| `remote_generator_selected_state` | Remote Generator Selected State | Shows whether the remote input says the generator input is selected. This helps diagnose generator changeover wiring. | Read-only. On means the generator-selected input is active. |
| `onboard_remote_inverter_switch` | Onboard Remote Inverter Switch | Shows whether the built-in remote inverter switch input is active. This can explain why the inverter is enabled or disabled outside Home Assistant. | Read-only. On means that input is active. |
| `interface_panel_detect` | Interface Panel Detect | Shows whether the MK3 USB adaptor is presenting itself as a control panel. This is mainly useful for troubleshooting. | Read-only. Disabled by default. |
| `interface_standby` | Interface Standby | Shows whether the MK3 USB adaptor is asking the unit to stay awake while off. This helps explain standby behavior. | Read-only. |
| `virtual_switch_position` | Virtual Switch Position | Shows a yes/no switch position stored inside the unit. It can help diagnose remote control behavior. | Read-only. On means the reported virtual switch is active. |
| `multi_functional_relay_state` | Multi-functional Relay State | Shows whether the unit's programmable relay is active. A relay is an internal switch that can control or signal other equipment. | Read-only. On means the relay is active. |

## Switches

| Entity key | Name | What it means and why you might care | States, options, and changing guidance |
| --- | --- | --- | --- |
| `remote_panel_standby` | Remote Panel Standby | Keeps the unit awake enough for the MK3 USB adaptor to keep control when the unit is off. This prevents losing remote control while off. | On keeps the unit awake and uses a little more battery. Off allows deeper sleep. Safe to change, but leaving it on is usually best for reliable Home Assistant control. |
| `battery_monitor` | Battery Monitor | Enables or disables the unit's own battery fullness tracking. This is needed for battery percentage reporting on supported devices. | On enables battery percentage tracking. Off disables it. Only turn it off if you do not want the unit estimating battery fullness. |
| `charge_enabled` | Charge Enabled | Controls whether the unit may charge batteries from incoming AC power while preserving the inverter side setting. | On allows charging. Off stops AC battery charging. Turn this off only if you want the unit to stop charging batteries from incoming power. |
| `ups_function` | UPS Function | Controls strict checking of incoming AC power for fast transfer behavior. It can reject poor generator power. | On keeps strict checking. Off relaxes checking. Leave on unless a generator or shore supply is being rejected and you understand the tradeoff. |
| `power_assist` | PowerAssist | Allows the battery inverter to help when incoming shore or generator power is not enough for the load. | On can support heavy loads using battery power. Off stops that help. Change only if you understand your input limit and load size. |
| `dynamic_current_limiter` | Dynamic Current Limiter | Lets the unit adjust how much current it draws from weaker generators. | On can be useful for unstable generators. Off uses the normal limit. Leave off unless your generator needs it. |
| `weak_ac_input` | Weak AC Input | Allows the unit to accept less perfect incoming AC power. This can help with some generators but may accept power you would otherwise reject. | On is more tolerant. Off is stricter. Leave off unless a known generator or shore supply needs it. |
| `aes` | AES | Controls AES, the automatic energy-saving inverter mode that lowers idle power use when loads are small. | On saves battery when loads are light. Off keeps the inverter fully ready. Safe for many systems, but turn off if small loads behave badly. |
| `stop_after_excessive_bulk` | Stop After Excessive Bulk | Controls whether the charger stops if fast charging runs for too long. This protects against a battery that is not charging normally. | On stops after too much fast charging. Off keeps trying. Leave on unless an installer tells you otherwise. |
| `storage_mode` | Storage Mode | Enables a long-term battery care mode that lowers the maintenance charge level after the battery has been full for a while. | On is useful for batteries left connected for long periods. Off keeps normal maintenance charging. Safe to change when you know your battery preference. |
| `ground_relay` | Ground Relay | Controls an internal grounding relay used by some installations for electrical safety behavior. | On enables the relay. Off disables it. Leave this alone unless your installer tells you to change it. |
| `accept_wide_frequency_range` | Accept Wide Frequency Range | Allows incoming AC power whose timing is farther from normal. This can help some generators. | On accepts a wider range. Off is stricter. Leave off unless your generator or shore power needs it. |
| `remote_overrules_ac1` | Remote Overrules AC1 | Allows the remote current limit to override the saved limit for incoming power input 1. | On lets the remote limit win. Off uses the saved device setting. Change only if you intentionally control input 1 from Home Assistant or a panel. |
| `remote_overrules_ac2` | Remote Overrules AC2 | Allows the remote current limit to override the saved limit for incoming power input 2. | On lets the remote limit win. Off uses the saved device setting. Change only if you intentionally control input 2 from Home Assistant or a panel. |
| `tubular_plate_traction_battery_curve` | Tubular Plate Traction Battery Curve | Selects a charging behavior intended for a specific heavy-duty lead-acid battery type. | On uses that battery curve. Off uses the normal curve. Leave off unless your battery manual says this is the correct battery type. |
| `aes_low_power_shutdown` | AES Low Power Shutdown | Lets energy-saving inverter mode shut down more deeply when the load is very small. | On can save more battery. Off keeps the inverter more ready for tiny loads. Leave off if small devices need uninterrupted power. |

## Numbers

| Entity key | Name | What it means and why you might care | States, options, and changing guidance |
| --- | --- | --- | --- |
| `remote_panel_current_limit` | Remote Panel Current Limit | Sets the incoming current limit used by the remote panel control. This prevents overloading shore power or a generator. | Enter amps within the device range. Safe to change when matching a known shore hookup or generator rating. |
| `ac1_input_current_limit` | AC1 Input Current Limit | Sets the saved current limit for incoming power input 1. | Enter amps within the supported range. Set this no higher than the supply can safely provide. |
| `ac2_input_current_limit` | AC2 Input Current Limit | Sets the saved current limit for incoming power input 2 on devices that have one. | Enter amps within the supported range. Set this no higher than the supply can safely provide. |
| `absorption_voltage` | Absorption Voltage | Sets the finishing-charge voltage. This affects how the battery is charged near full. | Change only to match the battery manufacturer's recommended value. Wrong values can shorten battery life. |
| `float_voltage` | Float Voltage | Sets the gentle maintenance voltage used after charging is complete. | Change only to match the battery manufacturer's recommended value. |
| `charge_current` | Charge Current | Sets the maximum battery charging current. This controls how hard the charger can charge the battery. | Change only within the battery's safe charging limit. |
| `inverter_output_voltage` | Inverter Output Voltage | Sets the voltage the inverter tries to supply to connected loads. | Leave at the normal voltage for your country unless an installer tells you otherwise. |
| `repeated_absorption_time` | Repeated Absorption Time | Sets how long a scheduled top-up finishing charge lasts. This helps keep batteries healthy during long-term use. | Change only if you understand your battery maintenance needs. |
| `repeated_absorption_interval` | Repeated Absorption Interval | Sets how often the scheduled top-up finishing charge is repeated. | Change only if you understand your battery maintenance needs. |
| `maximum_absorption_time` | Maximum Absorption Time | Sets the longest time the charger may spend in the finishing-charge stage. | Change only to match battery recommendations. |
| `battery_capacity` | Battery Capacity | Sets the battery bank size so the unit can estimate battery fullness. | Enter amp-hours for the battery bank. Setting this to 0 disables the battery monitor. |
| `battery_soc_when_bulk_finished` | State of Charge When Bulk Finished | Sets the percentage fullness the unit assumes when fast charging has finished. This affects the battery percentage estimate. | Change only if you are tuning battery percentage accuracy. |
| `battery_charge_efficiency` | Charge Efficiency | Sets how much charged energy the unit expects the battery to keep. This affects the battery percentage estimate. | Values may be a fraction, such as 0.95 for 95%. Change only if you know your battery's expected efficiency. |
| `dc_input_low_shutdown` | DC Input Low Shut-down | Sets the battery voltage where the inverter turns off to protect the battery. | Change only to match battery recommendations. Too low can damage batteries; too high can turn loads off early. |
| `dc_input_low_restart` | DC Input Low Restart | Sets the battery voltage where the inverter may restart after a low-battery shutdown. | Change only to match battery recommendations. |
| `dc_input_low_pre_alarm` | DC Input Low Pre-alarm | Sets the battery voltage where the unit warns before a low-battery shutdown. | Change only to match battery recommendations. |
| `assist_current_boost_factor` | Assist Current Boost Factor | Sets how strongly the battery inverter helps incoming AC power during short heavy loads. | Installer-level setting. Leave alone unless you understand the input supply and load behavior. |
| `aes_low_current_limit` | AES Low Current Limit | Sets the low-load point used by automatic energy-saving inverter mode. | Change only if tuning energy saving for small loads. |
| `aes_current_hysteresis` | AES Current Hysteresis | Sets how much the load must change before automatic energy-saving mode switches state. This helps prevent rapid switching. | Change only if tuning energy saving for small loads. |

## Selects

| Entity key | Name | What it means and why you might care | States, options, and changing guidance |
| --- | --- | --- | --- |
| `remote_panel_mode` | Remote Panel Mode | Sets the same basic operating request as a remote control panel. The physical switch and other inputs can still override it. | Off disables the unit. On enables the available inverter or inverter/charger function. Charger only, inverter only, and pass through are shown only when the connected device supports those charger-related controls. |

## Buttons

| Entity key | Name | What it means and why you might care | States, options, and changing guidance |
| --- | --- | --- | --- |
| `force_equalise` | Force Equalise | Starts a strong battery balancing charge on supported devices. This is only appropriate for batteries that allow it. | Momentary action. Press only when the battery manufacturer says equalising is safe. |
| `force_absorption` | Force Absorption | Forces the finishing-charge stage on supported devices. This can be useful after a battery has been partly charged. | Momentary action. Use only when you intentionally want a finishing charge now. |
| `force_float` | Force Float | Forces the gentle maintenance charge stage on supported devices. This can stop stronger charging and hold the battery near full. | Momentary action. Use only when you intentionally want maintenance charging now. |
