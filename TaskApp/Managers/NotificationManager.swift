import Foundation
import UserNotifications

class NotificationManager {
    static let shared = NotificationManager()

    // MARK: - Permission

    func requestAuthorization() async -> Bool {
        let center = UNUserNotificationCenter.current()
        do {
            return try await center.requestAuthorization(options: [.alert, .badge, .sound])
        } catch {
            return false
        }
    }

    func checkAuthorizationStatus() async -> UNAuthorizationStatus {
        await UNUserNotificationCenter.current().notificationSettings().authorizationStatus
    }

    // MARK: - Schedule / Cancel

    /// Schedules a local notification for the given task.
    /// If a reminder already exists for this task it is replaced.
    func scheduleReminder(for task: Task) {
        guard let date = task.reminderDate, date > Date() else { return }

        cancelReminder(for: task)

        let content = UNMutableNotificationContent()
        content.title = task.title
        content.body = task.notes.isEmpty ? "タスクのリマインダー" : task.notes
        content.sound = .default
        content.badge = 1
        content.userInfo = ["taskID": task.id.uuidString]

        let components = Calendar.current.dateComponents(
            [.year, .month, .day, .hour, .minute],
            from: date
        )
        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
        let request = UNNotificationRequest(
            identifier: notificationID(for: task),
            content: content,
            trigger: trigger
        )

        UNUserNotificationCenter.current().add(request)
    }

    func cancelReminder(for task: Task) {
        UNUserNotificationCenter.current()
            .removePendingNotificationRequests(withIdentifiers: [notificationID(for: task)])
    }

    func cancelAll() {
        UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
    }

    // MARK: - Badge reset

    func resetBadge() {
        UNUserNotificationCenter.current().setBadgeCount(0)
    }

    // MARK: - Helpers

    private func notificationID(for task: Task) -> String {
        "task-reminder-\(task.id.uuidString)"
    }
}
