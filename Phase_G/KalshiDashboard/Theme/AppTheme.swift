import SwiftUI

enum AppTheme {
    static let indigo = Color(red: 0.35, green: 0.36, blue: 0.95)
    static let accent = Color(red: 0.53, green: 0.67, blue: 0.98)
    static let positive = Color.green
    static let negative = Color.red

    static let glassGradient = LinearGradient(
        colors: [Color.white.opacity(0.22), Color.white.opacity(0.07)],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}
