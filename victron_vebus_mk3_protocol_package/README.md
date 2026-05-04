# Victron VE.Bus MK3 Protocol

Python protocol library for local communication with Victron VE.Bus charger/inverter devices through the Victron MK3-USB interface.

This package is intended to be used by the `Victron VE.Bus MK3 Control` Home Assistant integration. It handles the low-level serial protocol so the integration can focus on Home Assistant entities, services, and user-facing behaviour.

## Package Details

- Distribution name: `victron-vebus-mk3-protocol`
- Import name: `victron_vebus_mk3_protocol`
- Current version: `1.0.0`
- Source: `https://github.com/usersaynoso/victron-vebus-mk3-control/tree/main/victron_vebus_mk3_protocol_package`

## What It Provides

- MK3-USB serial connection handling.
- VE.Bus status requests for LEDs, AC data, DC data, power, configuration, and firmware version.
- Remote panel state commands for on, off, charger-only, and inverter-only behaviour.
- Interface flag control, including standby support.
- A probe helper that checks whether an MK3 interface is present and responding.
- A small optional CLI for direct testing.

## Install for Development

```bash
python -m pip install -e ".[cli]"
```

## Basic Probe Example

```python
import asyncio
from victron_vebus_mk3_protocol import probe


async def main() -> None:
    result = await probe("/dev/tty.usbserial-example")
    print(result.name)


asyncio.run(main())
```

## CLI Example

```bash
python cli.py probe /dev/tty.usbserial-example
python cli.py monitor /dev/tty.usbserial-example
```

## Notes

This library talks to real power equipment. It does not know your battery chemistry, cable size, generator limit, shore hookup, or whether someone has left the kettle on. Keep system limits configured correctly in VictronConnect or VEConfigure and treat control commands with the same care you would give a physical control panel.

## Credits and License

This package is MIT licensed. The package license preserves required copyright notices for original and current work; those notices identify copyright in contributed portions and do not imply ownership of the entire current repository by any one contributor. It is independent work and is not an official Victron Energy product.
