# First Setup

## Basic Setup

1. Connect the MK3-USB interface to the Victron VE.Bus device.
2. Connect the MK3-USB interface to the Home Assistant machine.
3. Add **Victron VE.Bus MK3 Control** in Home Assistant.
4. Select the detected device or choose the MK3-USB serial device from the list.
5. Submit the setup form.

## First Checks

After setup, check these first:

- `Firmware Version` should become available.
- `Battery Voltage` should show a realistic battery voltage.
- `Actual Mode` should match what the unit is doing.
- `Lit Indicators` or the individual indicator binary sensors should match the front panel lights.

If these are unavailable, the device may be asleep, the selected serial port may be wrong, or another program may still be using the MK3 interface.

## Recommended Starting Settings

- Leave `Remote Panel Standby` on if you want Home Assistant to keep control when the inverter/charger is off.
- Leave charger voltage and current settings unchanged until you have checked the battery manual.
- Leave advanced VE.Bus switches unchanged unless you know why they are needed.

The safest first dashboard is a read-only dashboard. It is less dramatic, and drama is best left to TV rather than battery chargers.
