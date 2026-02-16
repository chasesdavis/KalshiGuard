import Foundation

struct DashboardState: Codable {
    let status: String
    let lastUpdated: Date
    let phase: String
    let portfolio: Portfolio
    let positions: [Position]
    let history: [EquityPoint]
}

struct Portfolio: Codable {
    let bankrollStart: Double
    let portfolioValue: Double
    let dailyPnl: Double
    let dailyPnlPercent: Double
    let totalExposure: Double
    let buyingPower: Double
    let liveTrading: Bool
}

struct Position: Codable, Identifiable {
    var id: String { ticker }
    let ticker: String
    let side: String
    let contracts: Int
    let avgPrice: Double
    let markPrice: Double
    let unrealizedPnl: Double
    let confidence: Double
}

struct EquityPoint: Codable, Identifiable {
    var id: Date { timestamp }
    let timestamp: Date
    let value: Double
}

extension DashboardState {
    static let sample = DashboardState(
        status: "ONLINE",
        lastUpdated: .now,
        phase: "G-companion-read-only",
        portfolio: Portfolio(
            bankrollStart: 50,
            portfolioValue: 50.4,
            dailyPnl: 0.4,
            dailyPnlPercent: 0.8,
            totalExposure: 1.7,
            buyingPower: 48.3,
            liveTrading: false
        ),
        positions: [
            Position(ticker: "FED-RATE-25MAR", side: "YES", contracts: 1, avgPrice: 0.48, markPrice: 0.52, unrealizedPnl: 0.04, confidence: 0.0),
            Position(ticker: "INFLATION-CPI", side: "YES", contracts: 1, avgPrice: 0.44, markPrice: 0.41, unrealizedPnl: -0.03, confidence: 0.0)
        ],
        history: (0..<24).map {
            EquityPoint(timestamp: Calendar.current.date(byAdding: .hour, value: -23 + $0, to: .now) ?? .now, value: 50 + Double($0) * 0.02)
        }
    )
}
