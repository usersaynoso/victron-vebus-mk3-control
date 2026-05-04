# Victron VE.Bus MK3 Control Wiki

Welcome to the user guide for **Victron VE.Bus MK3 Control**.

This integration connects Home Assistant to supported Victron VE.Bus inverter/chargers through the MK3-USB interface. It provides local monitoring, careful control, and enough information to build useful dashboards without a GX device or cloud account.

## Start Here

- [Installation](Installation.md)
- [First Setup](First-Setup.md)
- [Safe Control Guide](Safe-Control-Guide.md)
- [Entities Reference](Entities-Reference.md)
- [Energy Dashboard](Energy-Dashboard.md)
- [Troubleshooting](Troubleshooting.md)

## What This Integration Is For

- Reading AC input and output values.
- Reading battery voltage, power, state of charge, and energy totals.
- Controlling remote panel mode and current limit.
- Exposing supported VE.Bus configuration settings in Home Assistant.
- Building automations that respect your inverter/charger limits.

## What This Integration Is Not

- It is not an official Victron Energy product.
- It is not a substitute for VictronConnect, VEConfigure, or installer knowledge.
- It does not know your battery chemistry, safe charge voltage, generator rating, or cable size.

If a setting can affect charging, AC acceptance, grounding, or inverter behaviour, read the relevant page before changing it.
