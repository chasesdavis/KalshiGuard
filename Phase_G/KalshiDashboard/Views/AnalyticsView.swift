import Charts
import SwiftUI

struct AnalyticsView: View {
    @EnvironmentObject private var vm: DashboardViewModel

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                GlassCard {
                    Text("Historical Equity")
                        .font(.headline)
                    Chart(vm.state.history) { point in
                        LineMark(
                            x: .value("Time", point.timestamp),
                            y: .value("Value", point.value)
                        )
                        .foregroundStyle(AppTheme.accent)
                    }
                    .frame(height: 220)
                }

                GlassCard {
                    Text("Risk Posture")
                        .font(.headline)
                    Text(vm.state.portfolio.liveTrading ? "Live" : "Read-only")
                        .foregroundStyle(vm.state.portfolio.liveTrading ? .yellow : .green)
                    Text("Total Exposure: \(vm.state.portfolio.totalExposure, format: .currency(code: "USD"))")
                    Text("Buying Power: \(vm.state.portfolio.buyingPower, format: .currency(code: "USD"))")
                }
            }
            .padding()
        }
        .background(Color.black.ignoresSafeArea())
    }
}
