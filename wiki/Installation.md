# Installation

## HACS Installation

Open the repository directly in HACS:
[Install Victron VE.Bus MK3 Control](https://my.home-assistant.io/redirect/hacs_repository/?owner=usersaynoso&repository=victron-vebus-mk3-control&category=integration)

Or install it manually through HACS:

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository:
   `https://github.com/usersaynoso/victron-vebus-mk3-control`
3. Choose category `Integration`.
4. Install **Victron VE.Bus MK3 Control**.
5. Restart Home Assistant.
6. Plug in the Victron MK3-USB interface.
7. Go to Settings -> Devices & services and add the integration.

## Manual Installation

1. Copy `custom_components/victron_vebus_mk3` into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Plug in the MK3-USB interface.
4. Add **Victron VE.Bus MK3 Control** from Settings -> Devices & services.

## USB Notes

- The MK3-USB adaptor appears as a serial port.
- On Linux and Home Assistant OS it often looks like `/dev/ttyUSB0` or `/dev/serial/by-id/...`.
- On macOS it often looks like `/dev/tty.usbserial-...`.
- On Windows it may look like `COM3`.

If auto-discovery does not find it, enter or choose the detected MK3-USB serial device in the setup form.
If Home Assistant offers manual entry, you can use the serial path as a fallback.

## After Installing

Open the device page and check the basic read-only sensors first:

- Firmware Version
- AC Input Voltage
- AC Output Voltage
- Battery Voltage
- Actual Mode

If those look sensible, move on to control and configuration.
