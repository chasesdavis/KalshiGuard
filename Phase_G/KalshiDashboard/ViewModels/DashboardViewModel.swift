import Foundation
import SwiftUI
import UIKit

@MainActor
final class DashboardViewModel: ObservableObject {
    @Published var state: DashboardState = .sample
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?

    private let session: URLSession
    private var timer: Timer?

    /// Configure for local WiFi Flask endpoint or ngrok URL.
    private let baseURL = URL(string: "http://127.0.0.1:5000")!
    private let apiToken = ProcessInfo.processInfo.environment["IOS_DASHBOARD_TOKEN"] ?? ""

    init(session: URLSession = .shared) {
        self.session = session
    }

    deinit {
        timer?.invalidate()
    }

    func startPolling() {
        refresh()
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 12, repeats: true) { [weak self] _ in
            Task { await self?.refresh() }
        }
    }

    func refresh() {
        Task {
            await refresh()
        }
    }

    func refresh() async {
        isLoading = true
        defer { isLoading = false }

        do {
            var request = URLRequest(url: baseURL.appending(path: "ios/dashboard"))
            if !apiToken.isEmpty {
                request.setValue("Bearer \(apiToken)", forHTTPHeaderField: "Authorization")
            }
            let (data, response) = try await session.data(for: request)
            try validate(response: response)

            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            decoder.keyDecodingStrategy = .convertFromSnakeCase
            state = try decoder.decode(DashboardState.self, from: data)
            errorMessage = nil
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
        } catch {
            errorMessage = "Refresh failed: \(error.localizedDescription)"
        }
    }

    func triggerApprovalStub(approvalID: String) async {
        do {
            var request = URLRequest(url: baseURL.appending(path: "execute_approved"))
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            if !apiToken.isEmpty {
                request.setValue("Bearer \(apiToken)", forHTTPHeaderField: "Authorization")
            }
            let payload = ["approval_id": approvalID, "approved": true] as [String : Any]
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            let (_, response) = try await session.data(for: request)
            try validate(response: response)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        } catch {
            UINotificationFeedbackGenerator().notificationOccurred(.error)
            errorMessage = "Approval call failed: \(error.localizedDescription)"
        }
    }

    private func validate(response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else { throw URLError(.badServerResponse) }
        guard 200..<300 ~= http.statusCode else { throw URLError(.badServerResponse) }
    }
}
