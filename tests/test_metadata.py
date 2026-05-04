from __future__ import annotations

import json
from pathlib import Path
import tomllib


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
    assert manifest["requirements"] == [
        "pyserial==3.5",
        "pyserial-asyncio-fast==0.16",
    ]
    assert "victron_vebus_mk3_protocol" in manifest["loggers"]


def test_protocol_package_metadata_points_to_this_repository() -> None:
    pyproject = tomllib.loads(
        (ROOT / "victron_vebus_mk3_protocol_package" / "pyproject.toml").read_text()
    )

    assert pyproject["project"]["urls"] == {
        "Homepage": (
            "https://github.com/usersaynoso/victron-vebus-mk3-control/tree/main/"
            "victron_vebus_mk3_protocol_package"
        ),
        "Issues": "https://github.com/usersaynoso/victron-vebus-mk3-control/issues",
    }


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


def test_readme_uses_public_names_and_service_domain() -> None:
    readme = (ROOT / "README.md").read_text()
    old_owner = "j9" + "brown/"
    old_service = "victron" + "_mk3.set_remote_panel_state"

    assert "# Victron VE.Bus MK3 Control" in readme
    assert "victron_vebus_mk3.set_remote_panel_state" in readme
    assert "usersaynoso/victron-vebus-mk3-control" in readme
    assert (
        "https://my.home-assistant.io/redirect/hacs_repository/"
        "?owner=usersaynoso&repository=victron-vebus-mk3-control&category=integration"
    ) in readme
    assert "https://my.home-assistant.io/badges/hacs_repository.svg" in readme
    assert (
        "[![Open your Home Assistant instance and open this repository in HACS.]"
        "(https://my.home-assistant.io/badges/hacs_repository.svg)]"
    ) in readme
    assert old_owner not in readme
    assert old_service not in readme


def test_integration_bundles_protocol_module_instead_of_unpublished_package() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    protocol = COMPONENT / "protocol.py"

    assert protocol.is_file()
    assert all(
        "victron-vebus-mk3-protocol" not in requirement
        for requirement in manifest["requirements"]
    )


def test_public_docs_introduce_integration_without_migration_language() -> None:
    public_docs = [ROOT / "README.md", *(ROOT / "wiki").glob("*.md")]
    blocked_phrases = (
        "renamed",
        "new integration identity",
        "old integration",
        "old domain",
        "Migration from",
        "victron_mk3",
        "victron-mk3-hass",
        "started as a fork",
    )

    for path in public_docs:
        content = path.read_text()
        for phrase in blocked_phrases:
            assert phrase not in content, f"{path}: {phrase}"


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
        "Credits-and-License.md",
    }

    wiki = ROOT / "wiki"
    assert {path.name for path in wiki.glob("*.md")} == expected


def test_wiki_home_links_to_rendered_github_wiki_pages() -> None:
    home = (ROOT / "wiki" / "Home.md").read_text()
    expected_page_slugs = (
        "Installation",
        "First-Setup",
        "Safe-Control-Guide",
        "Entities-Reference",
        "Energy-Dashboard",
        "Troubleshooting",
    )

    assert "raw.githubusercontent.com/wiki" not in home
    assert "](Installation.md)" not in home
    for slug in expected_page_slugs:
        assert (
            "https://github.com/usersaynoso/victron-vebus-mk3-control/wiki/"
            f"{slug}"
        ) in home


def test_license_files_preserve_original_and_current_copyright_notices() -> None:
    for license_path in (
        ROOT / "LICENSE",
        ROOT / "victron_vebus_mk3_protocol_package" / "LICENSE",
    ):
        license_text = license_path.read_text()

        assert "Copyright (c) 2024 Jeff Brown" in license_text
        assert "Copyright (c) 2026 Chris Taylor-Guest" in license_text


def test_brand_assets_exist_for_hacs_validation() -> None:
    brand = COMPONENT / "brand"

    assert (brand / "icon.png").is_file()
    assert (brand / "dark_icon.png").is_file()
    assert not (brand / "logo.png").exists()
