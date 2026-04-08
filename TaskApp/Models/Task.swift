import Foundation

struct Task: Identifiable, Codable, Equatable {
    var id: UUID = UUID()
    var title: String
    var notes: String = ""
    var isCompleted: Bool = false
    var priority: Priority = .medium
    var reminderDate: Date?
    var createdAt: Date = Date()

    enum Priority: String, Codable, CaseIterable {
        case high = "high"
        case medium = "medium"
        case low = "low"

        var label: String {
            switch self {
            case .high: return "高"
            case .medium: return "中"
            case .low: return "低"
            }
        }

        var color: String {
            switch self {
            case .high: return "red"
            case .medium: return "orange"
            case .low: return "green"
            }
        }
    }

    var isOverdue: Bool {
        guard let date = reminderDate, !isCompleted else { return false }
        return date < Date()
    }
}
