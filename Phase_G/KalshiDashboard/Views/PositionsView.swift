import SwiftUI

struct PositionsView: View {
    @EnvironmentObject private var vm: DashboardViewModel

    var body: some View {
        List(vm.state.positions) { position in
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(position.ticker)
                        .font(.headline)
                    Spacer()
                    Text(position.unrealizedPnl, format: .currency(code: "USD"))
                        .foregroundStyle(position.unrealizedPnl >= 0 ? AppTheme.positive : AppTheme.negative)
                }
                Text("\(position.side) • \(position.contracts) ctr @ \(position.avgPrice, format: .number.precision(.fractionLength(2)))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(.vertical, 4)
            .listRowBackground(Color.clear)
        }
        .scrollContentBackground(.hidden)
        .background(Color.black.ignoresSafeArea())
    }
}
