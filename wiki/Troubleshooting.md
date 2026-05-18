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

## Entities Are Disabled

Some entities are disabled by default to reduce polling and database writes. This is expected for low-level diagnostic entities and for L2-L4 AC phase sensors on most single-phase systems.

Enable extra entities only when you need them. If Home Assistant becomes slow or restarts on a low-memory system, increase the integration update interval before enabling more high-frequency sensors.

## Download Diagnostics For A GitHub Issue

When opening a GitHub issue, attach a diagnostics file from Home Assistant. It includes redacted Home Assistant runtime details, integration settings, controller state, the latest VE.Bus data, current entity states, and recent integration errors.

1. In Home Assistant, go to Settings -> Devices & services.
2. Select **Victron VE.Bus MK3 Control**.
3. Click the **...** menu next to **Victron VE.Bus MK3 Control**.
4. Select **Download diagnostics**.
5. Save the downloaded file.
6. Open a GitHub issue using the required problem report form.
7. Attach the diagnostics file in the diagnostics upload field. If GitHub will not accept the file, zip it first and attach the `.zip`.

The diagnostics file redacts the configured serial number and serial device path, but you should still review any file before sharing it publicly.

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
