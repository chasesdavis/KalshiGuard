import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var vm: DashboardViewModel

    var body: some View {
        TabView {
            OverviewView()
                .tabItem {
                    Label("Overview", systemImage: "gauge.with.dots.needle.33percent")
                }

            PositionsView()
                .tabItem {
                    Label("Positions", systemImage: "list.bullet.rectangle")
                }

            AnalyticsView()
                .tabItem {
                    Label("Analytics", systemImage: "chart.xyaxis.line")
                }
        }
        .tint(AppTheme.accent)
        .overlay(alignment: .top) {
            if let error = vm.errorMessage {
                Text(error)
                    .font(.caption)
                    .padding(8)
                    .background(Color.red.opacity(0.85))
                    .clipShape(Capsule())
                    .padding(.top, 8)
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(DashboardViewModel())
}
