import WidgetKit
import SwiftUI

// MARK: - Timeline Entry

struct TaskEntry: TimelineEntry {
    let date: Date
    let tasks: [Task]
}

// MARK: - Provider

struct TaskProvider: TimelineProvider {
    func placeholder(in context: Context) -> TaskEntry {
        TaskEntry(date: .now, tasks: Task.placeholders)
    }

    func getSnapshot(in context: Context, completion: @escaping (TaskEntry) -> Void) {
        completion(TaskEntry(date: .now, tasks: loadTasks()))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<TaskEntry>) -> Void) {
        let tasks = loadTasks()
        let entry = TaskEntry(date: .now, tasks: tasks)
        // Refresh every 15 minutes so the widget stays in sync
        let nextUpdate = Calendar.current.date(byAdding: .minute, value: 15, to: .now)!
        let timeline = Timeline(entries: [entry], policy: .after(nextUpdate))
        completion(timeline)
    }

    private func loadTasks() -> [Task] {
        // Read from the shared App Group UserDefaults
        guard
            let defaults = UserDefaults(suiteName: "group.com.yourcompany.taskapp"),
            let data = defaults.data(forKey: "saved_tasks"),
            let tasks = try? JSONDecoder().decode([Task].self, from: data)
        else { return [] }

        return tasks
            .filter { !$0.isCompleted }
            .sorted { lhs, rhs in
                let order: [Task.Priority] = [.high, .medium, .low]
                if lhs.priority != rhs.priority {
                    return order.firstIndex(of: lhs.priority)! < order.firstIndex(of: rhs.priority)!
                }
                return (lhs.reminderDate ?? .distantFuture) < (rhs.reminderDate ?? .distantFuture)
            }
    }
}

// MARK: - Small Widget View

struct SmallWidgetView: View {
    let tasks: [Task]

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Label("タスク", systemImage: "checkmark.circle")
                .font(.caption.bold())
                .foregroundColor(.accentColor)

            Divider()

            if tasks.isEmpty {
                Text("タスクなし")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ForEach(tasks.prefix(3)) { task in
                    HStack(spacing: 6) {
                        Circle()
                            .fill(priorityColor(task.priority))
                            .frame(width: 6, height: 6)
                        Text(task.title)
                            .font(.caption)
                            .lineLimit(1)
                    }
                }

                if tasks.count > 3 {
                    Text("他 \(tasks.count - 3) 件")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()
        }
        .padding()
    }
}

// MARK: - Medium Widget View

struct MediumWidgetView: View {
    let tasks: [Task]

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                Label("未完了タスク", systemImage: "checklist")
                    .font(.caption.bold())
                    .foregroundColor(.accentColor)

                Divider()

                ForEach(tasks.prefix(4)) { task in
                    HStack(spacing: 8) {
                        Circle()
                            .fill(priorityColor(task.priority))
                            .frame(width: 8, height: 8)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(task.title)
                                .font(.caption)
                                .lineLimit(1)
                            if let date = task.reminderDate {
                                Text(date.formatted(.dateTime.month().day().hour().minute()))
                                    .font(.caption2)
                                    .foregroundColor(task.isOverdue ? .red : .secondary)
                            }
                        }
                    }
                }

                if tasks.count > 4 {
                    Text("他 \(tasks.count - 4) 件")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }

                Spacer()
            }

            Spacer()

            // Summary badge
            VStack(spacing: 4) {
                Text("\(tasks.count)")
                    .font(.system(size: 36, weight: .bold, design: .rounded))
                    .foregroundColor(.accentColor)
                Text("件")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .frame(width: 70)
        }
        .padding()
    }
}

// MARK: - Widget Entry View (dispatcher)

struct TaskWidgetEntryView: View {
    @Environment(\.widgetFamily) var family
    let entry: TaskEntry

    var body: some View {
        switch family {
        case .systemSmall:
            SmallWidgetView(tasks: entry.tasks)
        case .systemMedium:
            MediumWidgetView(tasks: entry.tasks)
        default:
            MediumWidgetView(tasks: entry.tasks)
        }
    }
}

// MARK: - Widget definition

struct TaskWidget: Widget {
    let kind = "TaskWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: TaskProvider()) { entry in
            TaskWidgetEntryView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("タスク")
        .description("未完了のタスクをホーム画面で確認できます。")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

// MARK: - Helpers

private func priorityColor(_ priority: Task.Priority) -> Color {
    switch priority {
    case .high:   return .red
    case .medium: return .orange
    case .low:    return .green
    }
}

// MARK: - Placeholder data

extension Task {
    static var placeholders: [Task] {
        [
            Task(title: "企画書を仕上げる", priority: .high),
            Task(title: "ミーティング準備", priority: .medium),
            Task(title: "メールを返信する", priority: .low),
        ]
    }
}
