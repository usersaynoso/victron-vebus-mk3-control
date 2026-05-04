# Advanced VE.Bus Settings

These settings can change how the inverter/charger accepts AC power, charges batteries, or behaves under load.

## AC Input Behaviour

`UPS Function` controls strict incoming AC checking. Leave it on for normal fast-transfer behaviour. Turning it off can help with poor generator power, but it also accepts power the unit would otherwise reject.

`Weak AC Input` makes the unit more tolerant of imperfect AC input. Use it only when a known generator or supply needs it.

`Accept Wide Frequency Range` allows a wider incoming AC frequency range. This can help some generators, but stricter checking is safer for normal mains or shore power.

`Dynamic Current Limiter` helps with weaker generators by adjusting current draw. Leave it off unless your generator needs that behaviour.

## Load Support

`PowerAssist` lets the inverter help incoming AC when loads exceed the input limit. This is useful, but it can draw from the battery during heavy loads.

`Assist Current Boost Factor` tunes that help. Treat it as installer-level.

## Battery Care

`AES`, `AES Low Current Limit`, and `AES Current Hysteresis` tune automatic inverter energy saving.

`Storage Mode` supports long-term battery care by lowering maintenance charging after the battery has been full for a while.

`Stop After Excessive Bulk` protects against charging that stays in fast charge too long. Leave it on unless you have a specific reason.

`Tubular Plate Traction Battery Curve` is for a specific lead-acid battery type. Leave it off unless your battery documentation says otherwise.

## Grounding and Remote Override

`Ground Relay` affects grounding behaviour. Leave it alone unless your installer tells you to change it.

`Remote Overrules AC1` and `Remote Overrules AC2` control whether the remote current limit overrides saved input limits. Use them only if Home Assistant or an external panel is intentionally managing those inputs.

When in doubt, document the original value before changing anything. Future-you will appreciate the breadcrumb trail.
