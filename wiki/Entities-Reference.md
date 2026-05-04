# Entities Reference

The main README contains the full entity table. This page explains how to think about the groups.

## Sensors

Sensors are read-only. They report what the VE.Bus device or MK3 interface says.

Main groups:

- AC input: voltage, current, power, frequency, and current limit.
- AC output: voltage, current, power, and frequency.
- Battery: voltage, ripple voltage, power, charge/discharge power, state of charge, charger current, and inverter current.
- Energy: battery energy into and out of the battery.
- Device state: actual mode, front panel mode, detailed charge state, firmware version, and indicators.
- Diagnostics: number of AC inputs, reported phases, interface flags, signed load current, and similar troubleshooting values.

## Binary Sensors

Binary sensors are yes/no status items.

They include front-panel indicator lights, remote panel detection, current-limit control state, remote inputs, interface standby state, virtual switch position, and multi-functional relay state.

## Switches

Switches change behaviour. Some are everyday controls, and some are installer-level settings.

Everyday controls:

- `Remote Panel Standby`
- `Battery Monitor`
- `Charge Enabled`

Advanced controls:

- `UPS Function`
- `PowerAssist`
- `Dynamic Current Limiter`
- `Weak AC Input`
- `AES`
- `Stop After Excessive Bulk`
- `Storage Mode`
- `Ground Relay`
- `Accept Wide Frequency Range`
- `Remote Overrules AC1`
- `Remote Overrules AC2`
- `Tubular Plate Traction Battery Curve`
- `AES Low Power Shutdown`

If a switch changes how the unit accepts AC power, charges batteries, or handles grounding, read [Advanced VE.Bus Settings](Advanced-VE.Bus-Settings.md) before changing it.

## Numbers

Number entities set current limits, charge voltages, charge current, battery monitor values, low DC thresholds, absorption timing, and AES tuning values.

Treat battery voltage and current settings as battery-manual settings, not "try it and see" settings.

## Selects and Buttons

- `Remote Panel Mode` selects the requested operating mode.
- `Force Equalise`, `Force Absorption`, and `Force Float` request charge-state actions on supported devices.

Only use forced charge buttons when you know that charge stage is appropriate for the battery.
