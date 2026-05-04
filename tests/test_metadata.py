from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "victron_vebus_mk3"


def test_manifest_uses_v1_name_domain_and_protocol_package() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text())

    assert manifest["domain"] == "victron_vebus_mk3"
    assert manifest["name"] == "Victron VE.Bus MK3 Control"
    assert manifest["codeowners"] == ["@usersaynoso"]
    assert manifest["version"] == "1.0.0"
    assert manifest["documentation"] == (
        "https://github.com/usersaynoso/victron-vebus-mk3-control/"
    )
    assert manifest["issue_tracker"] == (
        "https://github.com/usersaynoso/victron-vebus-mk3-control/issues"
    )
    assert manifest["requirements"] == ["victron-vebus-mk3-protocol==1.0.0"]
    assert "victron_vebus_mk3_protocol" in manifest["loggers"]


def test_hacs_metadata_uses_public_display_name() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text())

    assert hacs == {
        "name": "Victron VE.Bus MK3 Control",
        "render_readme": True,
    }


def test_service_selector_uses_new_domain() -> None:
    services = (COMPONENT / "services.yaml").read_text()
    old_domain = "victron" + "_mk3"

    assert 'integration: "victron_vebus_mk3"' in services
    assert old_domain not in services


def test_readme_uses_new_public_names_and_credit_footer() -> None:
    readme = (ROOT / "README.md").read_text()
    old_owner = "j9" + "brown/"
    old_service = "victron" + "_mk3.set_remote_panel_state"

    assert "# Victron VE.Bus MK3 Control" in readme
    assert "victron_vebus_mk3.set_remote_panel_state" in readme
    assert "usersaynoso/victron-vebus-mk3-control" in readme
    assert (
        "This project started as a fork of Jeff Brown's `victron-mk3-hass` "
        "and has since been extended."
    ) in readme
    assert old_owner not in readme
    assert old_service not in readme


def test_wiki_pages_exist_for_user_documentation() -> None:
    expected = {
        "Home.md",
        "Installation.md",
        "First-Setup.md",
        "Safe-Control-Guide.md",
        "Entities-Reference.md",
        "Energy-Dashboard.md",
        "Battery-Monitor.md",
        "Advanced-VE.Bus-Settings.md",
        "Services-and-Automations.md",
        "Troubleshooting.md",
        "Migration-from-Victron-MK3.md",
        "Credits-and-License.md",
    }

    wiki = ROOT / "wiki"
    assert {path.name for path in wiki.glob("*.md")} == expected


def test_brand_assets_exist_for_hacs_validation() -> None:
    brand = COMPONENT / "brand"

    assert (brand / "icon.png").is_file()
    assert (brand / "logo.png").is_file()
