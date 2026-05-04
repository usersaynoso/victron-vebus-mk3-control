from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "victron_vebus_mk3"

PLATFORM_FILES = {
    "binary_sensor": COMPONENT / "binary_sensor.py",
    "button": COMPONENT / "button.py",
    "number": COMPONENT / "number.py",
    "select": COMPONENT / "select.py",
    "sensor": COMPONENT / "sensor.py",
    "switch": COMPONENT / "switch.py",
}

EXPECTED_STATE_LABELS = {
    ("select", "remote_panel_mode"): {
        "off",
        "on",
        "charger_only",
        "inverter_only",
        "pass_through",
    },
    ("sensor", "actual_mode"): {
        "off",
        "on",
        "charger_only",
        "inverter_only",
        "pass_through",
    },
    ("sensor", "front_panel_mode"): {"off", "on", "charger_only"},
    ("sensor", "ignore_ac_input_state"): {"off", "on"},
    ("sensor", "last_active_ac_input"): {
        "ac_input_1",
        "ac_input_2",
        "ac_input_3",
        "ac_input_4",
        "unknown",
    },
    ("sensor", "device_state"): {
        "down",
        "startup",
        "off",
        "slave",
        "invert_full",
        "invert_half",
        "invert_aes",
        "power_assist",
        "bypass",
        "state_charge",
    },
    ("sensor", "vebus_charge_state"): {
        "not_charging",
        "initializing",
        "bulk",
        "absorption",
        "float",
        "storage",
        "repeated_absorption",
        "forced_absorption",
        "equalise",
        "bulk_stopped",
        "unknown",
    },
    ("sensor", "lit_indicators"): {
        "none",
        "mains",
        "bulk",
        "absorption",
        "float",
        "inverter",
        "overload",
        "low_battery",
        "temperature",
    },
    ("sensor", "blinking_indicators"): {
        "none",
        "mains",
        "bulk",
        "absorption",
        "float",
        "inverter",
        "overload",
        "low_battery",
        "temperature",
    },
}


def test_entity_keys_are_unique_across_platform_unique_id_suffixes() -> None:
    inventory = _source_inventory()
    keys = [key for platform_keys in inventory.values() for key in platform_keys]
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)

    assert duplicates == []


def test_all_entities_have_translations_in_strings_and_english() -> None:
    inventory = _source_inventory()

    for translation_path in (
        COMPONENT / "strings.json",
        COMPONENT / "translations" / "en.json",
    ):
        translations = _translation_inventory(translation_path)
        assert translations == inventory

        payload = json.loads(translation_path.read_text())
        for (platform, key), expected_states in EXPECTED_STATE_LABELS.items():
            states = payload["entity"][platform][key].get("state")
            assert states is not None, f"{translation_path}: {platform}.{key}"
            assert expected_states <= set(states)


def test_all_entities_have_readme_inventory_rows() -> None:
    inventory = _source_inventory()
    readme = (ROOT / "README.md").read_text()
    missing = []

    for key in sorted(key for keys in inventory.values() for key in keys):
        if f"| `{key}` |" not in readme:
            missing.append(key)

    assert missing == []


def test_all_entities_have_detailed_wiki_reference_rows() -> None:
    inventory = _source_inventory()
    wiki_reference = (ROOT / "wiki" / "Entities-Reference.md").read_text()
    missing = []

    for key in sorted(key for keys in inventory.values() for key in keys):
        if f"| `{key}` |" not in wiki_reference:
            missing.append(key)

    assert missing == []


def test_readme_keeps_entity_inventory_concise() -> None:
    readme = (ROOT / "README.md").read_text()
    entity_inventory = readme.split("## Entity Inventory", 1)[1].split(
        "## Home Assistant Energy", 1
    )[0]

    assert "What it means and why you might care" not in entity_inventory


def test_entity_reference_avoids_gx_only_or_protocol_jargon() -> None:
    entity_reference = (ROOT / "wiki" / "Entities-Reference.md").read_text()

    for blocked_phrase in (
        "RAM variable",
        "Hub4",
        "D-Bus",
        "MicroGrid",
        "volatile GX",
        "ESS",
    ):
        assert blocked_phrase not in entity_reference


def _source_inventory() -> dict[str, set[str]]:
    inventory = {
        platform: _literal_entity_keys(path.read_text())
        for platform, path in PLATFORM_FILES.items()
    }
    inventory["sensor"].update(_generated_ac_phase_sensor_keys())
    return inventory


def _literal_entity_keys(source: str) -> set[str]:
    keys = set(re.findall(r'(?<!translation_)key="([^"]+)"', source))
    keys.update(re.findall(r'led_description\(\s*"([^"]+)"', source))
    return keys


def _generated_ac_phase_sensor_keys() -> set[str]:
    const_source = (COMPONENT / "const.py").read_text()
    match = re.search(r"AC_PHASES_POLLED = (\d+)", const_source)
    assert match is not None

    keys = set()
    for phase in range(1, int(match.group(1)) + 1):
        suffix = "" if phase == 1 else f"_l{phase}"
        keys.update(
            {
                f"ac_input_voltage{suffix}",
                f"ac_input_current{suffix}",
                f"ac_output_voltage{suffix}",
                f"ac_output_current{suffix}",
            }
        )
    return keys


def _translation_inventory(path: Path) -> dict[str, set[str]]:
    payload = json.loads(path.read_text())
    return {
        platform: set(payload["entity"].get(platform, {}))
        for platform in PLATFORM_FILES
    }
