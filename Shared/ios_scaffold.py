"""Generate Phase G Swift scaffold files.

Usage:
    python Shared/ios_scaffold.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE_G = ROOT / "Phase_G" / "KalshiDashboard"

TEMPLATES = {
    "App/KalshiDashboardApp.swift": "import SwiftUI\n\n@main\nstruct KalshiDashboardApp: App {\n    var body: some Scene {\n        WindowGroup {\n            ContentView()\n        }\n    }\n}\n",
    "ContentView.swift": "import SwiftUI\n\nstruct ContentView: View {\n    var body: some View {\n        Text(\"KalshiGuard\")\n    }\n}\n",
}


def main() -> None:
    for rel_path, content in TEMPLATES.items():
        destination = PHASE_G / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            continue
        destination.write_text(content, encoding="utf-8")
        print(f"Created {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
