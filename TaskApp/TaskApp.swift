import SwiftUI

@main
struct TaskApp: App {
    @StateObject private var store = TaskStore.shared
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(store)
                .task {
                    // Request notification permission on first launch
                    _ = await NotificationManager.shared.requestAuthorization()
                }
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                NotificationManager.shared.resetBadge()
            }
        }
    }
}
