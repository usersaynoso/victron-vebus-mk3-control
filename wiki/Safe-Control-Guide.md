# Safe Control Guide

## Remote Panel Modes

`Remote Panel Mode` asks the VE.Bus device to behave like a remote panel has requested one of these modes:

| Mode | Meaning |
| --- | --- |
| `on` | Charger and inverter are enabled. |
| `off` | Charger and inverter are disabled. |
| `charger_only` | Charger is enabled and inverter is disabled. |
| `inverter_only` | Inverter is enabled and charger is disabled. |
| `pass_through` | Charging is disabled while the inverter side stays enabled so incoming AC can pass through when available. |

## Why Home Assistant Might Not Win

The physical front switch, remote on/off input, external panels, and the device firmware can override Home Assistant. If `Remote Panel Mode` says one thing and `Actual Mode` says another, use `Actual Mode` as the truth.

## Current Limits

Use current limits to protect shore power, campsite hookups, generators, and other incoming AC sources.

Set the current limit no higher than the supply can safely provide. If the supply is 10 A, do not set 16 A just because the number box lets you. Home Assistant is helpful, not a licensed electrician in a tiny browser window.

## Standby Mode

`Remote Panel Standby` asks the MK3 interface to keep the device awake enough for control while it is off.

- On: more reliable remote control, slightly more battery use.
- Off: deeper sleep is allowed, but Home Assistant may not be able to wake the device.

For most Home Assistant users, standby on is the practical default.
