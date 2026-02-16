import SwiftUI
import XCTest
@testable import KalshiDashboard

final class DashboardViewSnapshotTests: XCTestCase {
    @MainActor
    func testOverviewPreviewRenders() {
        let vm = DashboardViewModel()
        vm.state = .sample
        let view = OverviewView().environmentObject(vm)
        let renderer = ImageRenderer(content: view.frame(width: 390, height: 844))
        XCTAssertNotNil(renderer.uiImage)
    }

    @MainActor
    func testWidgetSmallRenders() {
        let entry = KalshiEntry(date: .now, state: .sample)
        let widget = KalshiWidgetEntryView(entry: entry)
            .environment(\.widgetFamily, .systemSmall)
        let renderer = ImageRenderer(content: widget.frame(width: 170, height: 170))
        XCTAssertNotNil(renderer.uiImage)
    }
}
