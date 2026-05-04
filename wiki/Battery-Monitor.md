# Battery Monitor

## What It Does

The VE.Bus battery monitor estimates battery fullness and can provide `Battery State of Charge`.

It depends on settings such as:

- `Battery Capacity`
- `State of Charge When Bulk Finished`
- `Charge Efficiency`

## Enabling It

Set `Battery Capacity` to the battery bank capacity in amp-hours. Then turn on `Battery Monitor`.

Setting `Battery Capacity` to `0` disables the battery monitor on devices that support this behaviour.

## Important Settings

`Battery Capacity` should match the usable battery bank the Victron device is managing.

`Charge Efficiency` may be represented as a fraction. For example, `0.95` means 95 percent.

`State of Charge When Bulk Finished` affects how the unit estimates fullness when the fast-charging stage ends.

## Safety Notes

Battery monitor settings affect reporting and charge behaviour assumptions. They are not just dashboard decoration. Use values that match your battery system rather than values that make the graph look cheerful.
