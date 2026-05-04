# Migration from Victron MK3

This project uses a new Home Assistant domain:

```text
victron_vebus_mk3
```

The older fork used:

```text
victron_mk3
```

Home Assistant treats those as different integrations.

## Recommended Migration

1. Note any dashboards, automations, and scripts that use old entity IDs or the old service prefix.
2. Disable or remove the old integration.
3. Install **Victron VE.Bus MK3 Control**.
4. Add the new integration.
5. Update automations from `victron_mk3.*` to `victron_vebus_mk3.*`.
6. Check dashboards and rename entity IDs if needed.

## Why Entity IDs May Change

Home Assistant entity IDs are based on the integration domain, device name, and entity name. Because the domain changed, Home Assistant may create new entities rather than reusing the old ones.

This is expected. It is mildly annoying, but far less annoying than a permanent domain name that no longer describes the project.
