# Phase G — iOS Companion App 📱

**Status:** 🔜 Planned (can develop in parallel with any phase)

## What This Phase Will Do
- SwiftUI 5+ dashboard for iOS (roothide jailbreak compatible, iOS 17)
- Live portfolio view: P&L cards, positions, sparklines, historical graphs
- WidgetKit widgets: Small (balance + today P&L), Medium (top positions), Large (mini-dashboard)
- Glassmorphism UI, fluid animations, SF Symbols 6, haptics, dark/light mode
- Consumes KalshiGuard Flask API (token auth, local WiFi or ngrok)
- Secure local auth (biometrics)
- Bundle ID: com.chasesdavis.kalshidashboard

## Build Process
- Theos (roothide-compatible) or Xcode → .deb / .ipa
- Install via TrollStore / Sileo

## Key Files (to be created)
- `KalshiDashboard/` — Xcode project or Theos makefile
- `ContentView.swift` — Main dashboard
- `DashboardViewModel.swift` — API consumption layer
- `WidgetProvider.swift` — WidgetKit timeline provider
