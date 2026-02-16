# Phase G — iOS Companion App 📱

**Status:** ✅ Implemented

Phase G delivers a production-oriented SwiftUI dashboard and WidgetKit bundle for KalshiGuard with a strict **risk-first, read-only-by-default** posture.

## Included Deliverables

- SwiftUI app shell with tabbed UX:
  - `Overview` (portfolio cards, equity sparkline, approval-stub action)
  - `Positions` (open positions list)
  - `Analytics` (historical chart + risk posture)
- Glassmorphism visual system (indigo theme), SF Symbols, and haptic feedback hooks.
- WidgetKit implementation for `systemSmall`, `systemMedium`, and `systemLarge`.
- `DashboardViewModel` API polling for Flask endpoint `/ios/dashboard` with token auth support.
- Safe approval stub client call to `/execute_approved`.
- Theos packaging files for roothide-compatible jailbreak workflows (`.deb`).
- XCTest rendering checks for SwiftUI preview/snapshot sanity.

## Security Model

- No secrets are embedded in code.
- Dashboard auth token is read from environment (`IOS_DASHBOARD_TOKEN`).
- Flask endpoint validates token when configured.

## API Contract (App -> Flask)

- `GET /ios/dashboard`
  - Returns status, portfolio summary, synthetic historical equity points, and tracked positions.
- `POST /execute_approved`
  - UI workflow stub only.
  - Returns `executed: false` intentionally to preserve capital while enabling app integration.

## File Layout

- `KalshiDashboard/` — Swift sources
- `KalshiDashboardTests/` — XCTest rendering checks
- `Theos/` — packaging metadata and makefile

## Build (Xcode)

1. Open/create an Xcode iOS 17+ project and add files under `Phase_G/KalshiDashboard`.
2. Ensure frameworks are linked: `SwiftUI`, `WidgetKit`, `Charts`.
3. Set bundle ID (suggested): `com.chasesdavis.kalshidashboard`.
4. Run on device/simulator.

## Build (.deb via Theos)

```bash
cd Phase_G/Theos
export THEOS=/opt/theos
make package
```

Generated package appears under `.theos/_/`.

## TrollStore / Roothide Notes

- Build/sign `.ipa` with your normal iOS signing path, then install through TrollStore.
- For jailbreak `.deb`, install with Sileo/Zebra on roothide environment.
- This app is local-network + token based and does not perform direct live trading.

## Runtime Configuration

- Flask API should be reachable from device (LAN IP or ngrok tunnel).
- Optional token gate:
  - Set `IOS_DASHBOARD_TOKEN` in backend environment.
  - Set same env value for app runtime (scheme env vars).

## Validation Targets

- Python endpoint tests: `Phase_A/tests/test_api.py`
- Swift rendering checks: `Phase_G/KalshiDashboardTests/DashboardViewSnapshotTests.swift`

