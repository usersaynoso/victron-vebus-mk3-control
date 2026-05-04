# Troubleshooting

## Integration Does Not Appear

- Confirm the folder is `custom_components/victron_vebus_mk3`.
- Confirm `manifest.json` contains `domain: victron_vebus_mk3`.
- Restart Home Assistant after installation.
- Check Home Assistant logs for requirement install errors.

## Cannot Connect

- Confirm the serial port path is correct.
- Confirm the MK3-USB interface is connected to both USB and VE.Bus.
- Close VictronConnect or any other program using the same serial port.
- Unplug and reconnect the MK3-USB interface.
- Make sure the VE.Bus device is awake.

## Entities Are Unavailable

Some entities only appear or become available when the connected device supports the underlying VE.Bus value.

Unavailable can mean:

- the device is asleep,
- the setting is not supported,
- the MK3 interface missed a reply,
- Home Assistant has not completed the next polling cycle.

## Mode Does Not Change

Check:

- physical front switch position,
- remote on/off input,
- external control panel,
- `Actual Mode`,
- `Front Panel Mode`,
- `Remote Panel Detected`.

The physical controls can override Home Assistant.

## Current Limit Does Not Change

Check whether `Current Limit Controlled By Panel` is on. An external panel may be setting the limit.

Also check `Remote Overrules AC1` and `Remote Overrules AC2` if your device supports them.

## Device Went Off and Will Not Wake

Connect AC input if available, or disconnect the MK3 interface from VE.Bus, wait for the unit to fully sleep, then use the physical switch to wake it. Once recovered, consider enabling `Remote Panel Standby`.
