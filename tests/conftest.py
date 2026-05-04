from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PACKAGE = ROOT / "victron_vebus_mk3_protocol_package"

sys.path.insert(0, str(PROTOCOL_PACKAGE))
