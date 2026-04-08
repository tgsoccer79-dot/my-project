import Foundation
import Combine

class TaskStore: ObservableObject {
    @Published var tasks: [Task] = [] {
        didSet { save() }
    }

    private let saveKey = "saved_tasks"

    // Shared instance used by the widget
    static let shared = TaskStore()

    init() {
        load()
    }

    // MARK: - CRUD

    func add(_ task: Task) {
        tasks.append(task)
    }

    func update(_ task: Task) {
        guard let index = tasks.firstIndex(where: { $0.id == task.id }) else { return }
        tasks[index] = task
    }

    func delete(at offsets: IndexSet) {
        tasks.remove(atOffsets: offsets)
    }

    func delete(_ task: Task) {
        tasks.removeAll { $0.id == task.id }
    }

    func toggleComplete(_ task: Task) {
        var updated = task
        updated.isCompleted.toggle()
        update(updated)
    }

    // MARK: - Filtered views

    var pendingTasks: [Task] {
        tasks.filter { !$0.isCompleted }.sorted { lhs, rhs in
            // Overdue first, then by priority, then by creation date
            if lhs.isOverdue != rhs.isOverdue { return lhs.isOverdue }
            if lhs.priority != rhs.priority {
                let order: [Task.Priority] = [.high, .medium, .low]
                return order.firstIndex(of: lhs.priority)! < order.firstIndex(of: rhs.priority)!
            }
            return lhs.createdAt < rhs.createdAt
        }
    }

    var completedTasks: [Task] {
        tasks.filter { $0.isCompleted }
    }

    var upcomingTasks: [Task] {
        tasks.filter { !$0.isCompleted && $0.reminderDate != nil }
             .sorted { ($0.reminderDate ?? .distantFuture) < ($1.reminderDate ?? .distantFuture) }
    }

    // MARK: - Persistence

    private func save() {
        guard let data = try? JSONEncoder().encode(tasks) else { return }
        let defaults = sharedDefaults()
        defaults?.set(data, forKey: saveKey)
    }

    private func load() {
        guard
            let defaults = sharedDefaults(),
            let data = defaults.data(forKey: saveKey),
            let decoded = try? JSONDecoder().decode([Task].self, from: data)
        else { return }
        tasks = decoded
    }

    /// App Group shared UserDefaults so the widget can read the same data.
    private func sharedDefaults() -> UserDefaults? {
        // Replace "group.com.yourcompany.taskapp" with your actual App Group identifier.
        UserDefaults(suiteName: "group.com.yourcompany.taskapp") ?? .standard
    }
}
