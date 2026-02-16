import SwiftUI

struct OverviewView: View {
    @EnvironmentObject private var vm: DashboardViewModel

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
                header
                pnlCards
                GlassCard {
                    Text("Equity Trend")
                        .font(.headline)
                    SparklineView(points: vm.state.history)
                }
                approvalButton
            }
            .padding()
        }
        .background(
            LinearGradient(colors: [AppTheme.indigo.opacity(0.5), .black], startPoint: .topLeading, endPoint: .bottomTrailing)
                .ignoresSafeArea()
        )
        .task { vm.startPolling() }
        .refreshable { await vm.refresh() }
    }

    private var header: some View {
        GlassCard {
            Text("KalshiGuard")
                .font(.title2.bold())
            Text("Phase: \(vm.state.phase)")
                .foregroundStyle(.secondary)
            Text("Updated: \(vm.state.lastUpdated.formatted(date: .omitted, time: .standard))")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    private var pnlCards: some View {
        HStack(spacing: 12) {
            GlassCard {
                Text("Portfolio")
                    .font(.caption)
                Text(vm.state.portfolio.portfolioValue, format: .currency(code: "USD"))
                    .font(.title3.bold())
            }
            GlassCard {
                Text("Day PnL")
                    .font(.caption)
                Text(vm.state.portfolio.dailyPnl, format: .currency(code: "USD"))
                    .font(.title3.bold())
                    .foregroundStyle(vm.state.portfolio.dailyPnl >= 0 ? AppTheme.positive : AppTheme.negative)
            }
        }
    }

    private var approvalButton: some View {
        Button {
            Task { await vm.triggerApprovalStub(approvalID: UUID().uuidString) }
        } label: {
            Label("Send Approval Stub", systemImage: "paperplane.fill")
                .frame(maxWidth: .infinity)
                .padding()
        }
        .buttonStyle(.borderedProminent)
        .tint(AppTheme.accent)
    }
}
