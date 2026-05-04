# Services and Automations

## Service

The integration registers:

```text
victron_vebus_mk3.set_remote_panel_state
```

Fields:

- `device_id`: the Home Assistant device id.
- `mode`: `off`, `on`, `pass_through`, `charger_only`, or `inverter_only`.
- `current_limit`: optional AC input current limit in amps.

## Example: Set Charger Only

```yaml
action: victron_vebus_mk3.set_remote_panel_state
data:
  device_id: 54b361121006d7658fa486a9ebaf02bc
  mode: "charger_only"
  current_limit: 10
```

## Example: Stop Charging but Keep Pass-through Available

```yaml
action: victron_vebus_mk3.set_remote_panel_state
data:
  device_id: 54b361121006d7658fa486a9ebaf02bc
  mode: "pass_through"
```

## Automation Advice

- Use conservative current limits.
- Avoid rapid mode switching.
- Prefer conditions that check `Actual Mode`, battery voltage, and AC input state.
- Add manual overrides for important power automations.
