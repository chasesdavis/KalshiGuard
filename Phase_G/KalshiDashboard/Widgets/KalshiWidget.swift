import SwiftUI
import WidgetKit

struct KalshiEntry: TimelineEntry {
    let date: Date
    let state: DashboardState
}

struct KalshiProvider: TimelineProvider {
    func placeholder(in context: Context) -> KalshiEntry {
        KalshiEntry(date: .now, state: .sample)
    }

    func getSnapshot(in context: Context, completion: @escaping (KalshiEntry) -> Void) {
        completion(KalshiEntry(date: .now, state: .sample))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<KalshiEntry>) -> Void) {
        let entry = KalshiEntry(date: .now, state: .sample)
        let refresh = Calendar.current.date(byAdding: .minute, value: 15, to: .now) ?? .now.addingTimeInterval(900)
        completion(Timeline(entries: [entry], policy: .after(refresh)))
    }
}

struct KalshiWidgetEntryView: View {
    var entry: KalshiProvider.Entry
    @Environment(\.widgetFamily) private var family

    var body: some View {
        switch family {
        case .systemSmall:
            small
        case .systemMedium:
            medium
        default:
            large
        }
    }

    private var small: some View {
        VStack(alignment: .leading) {
            Text("KalshiGuard")
                .font(.caption)
            Text(entry.state.portfolio.portfolioValue, format: .currency(code: "USD"))
                .font(.title3.bold())
        }
        .containerBackground(for: .widget) { Color.indigo.opacity(0.2) }
    }

    private var medium: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Top Positions")
                .font(.headline)
            ForEach(entry.state.positions.prefix(2)) { position in
                Text("\(position.ticker): \(position.unrealizedPnl, format: .currency(code: "USD"))")
                    .font(.caption)
            }
        }
        .containerBackground(for: .widget) { Color.indigo.opacity(0.2) }
    }

    private var large: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("KalshiGuard Mini Dashboard")
                .font(.headline)
            Text("Exposure: \(entry.state.portfolio.totalExposure, format: .currency(code: "USD"))")
            Text("Buying Power: \(entry.state.portfolio.buyingPower, format: .currency(code: "USD"))")
        }
        .containerBackground(for: .widget) { Color.indigo.opacity(0.2) }
    }
}

struct KalshiWidget: Widget {
    let kind: String = "KalshiWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: KalshiProvider()) { entry in
            KalshiWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("KalshiGuard")
        .description("Read-only risk-first dashboard widgets.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}
