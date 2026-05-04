# Energy Dashboard

## Battery Storage

Use these entities in Settings -> Dashboards -> Energy:

| Home Assistant setting | Entity |
| --- | --- |
| Energy charged | `Battery Energy Into` |
| Energy discharged | `Battery Energy Out Of` |
| Type of power measurement | `Battery Charge Discharge Power` |
| Direction | `Standard` |

`Battery Charge Discharge Power` follows Home Assistant's battery convention:

- Positive means the battery is discharging.
- Negative means the battery is charging.

## Grid Power

`AC Input Power` can be used as instantaneous grid-side power only when the VE.Bus device measures the same grid connection point you want to display.

If some loads, solar, or generators bypass the VE.Bus device, use a separate site meter for grid energy. Otherwise the Energy dashboard will only show the portion of the site measured by the VE.Bus device.

## What This Integration Does Not Provide Yet

The integration does not currently provide cumulative grid import/export energy sensors. Use another meter or integration for full grid import/export accounting.
