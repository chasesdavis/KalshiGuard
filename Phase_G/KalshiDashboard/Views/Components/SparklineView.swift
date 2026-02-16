import Charts
import SwiftUI

struct SparklineView: View {
    let points: [EquityPoint]

    var body: some View {
        Chart(points) { point in
            LineMark(
                x: .value("Time", point.timestamp),
                y: .value("Equity", point.value)
            )
            .interpolationMethod(.catmullRom)
            .foregroundStyle(AppTheme.indigo)

            AreaMark(
                x: .value("Time", point.timestamp),
                y: .value("Equity", point.value)
            )
            .foregroundStyle(AppTheme.indigo.opacity(0.15))
        }
        .chartXAxis(.hidden)
        .chartYAxis(.hidden)
        .frame(height: 90)
    }
}
