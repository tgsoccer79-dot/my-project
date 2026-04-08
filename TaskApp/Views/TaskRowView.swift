import SwiftUI

struct TaskRowView: View {
    let task: Task
    let onToggle: () -> Void

    private var priorityColor: Color {
        switch task.priority {
        case .high:   return .red
        case .medium: return .orange
        case .low:    return .green
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            // Completion toggle
            Button(action: onToggle) {
                Image(systemName: task.isCompleted ? "checkmark.circle.fill" : "circle")
                    .font(.title2)
                    .foregroundColor(task.isCompleted ? .accentColor : .secondary)
            }
            .buttonStyle(.plain)

            VStack(alignment: .leading, spacing: 4) {
                Text(task.title)
                    .font(.body)
                    .strikethrough(task.isCompleted)
                    .foregroundColor(task.isCompleted ? .secondary : .primary)

                if let date = task.reminderDate {
                    Label(
                        date.formatted(date: .abbreviated, time: .shortened),
                        systemImage: "bell"
                    )
                    .font(.caption)
                    .foregroundColor(task.isOverdue ? .red : .secondary)
                }

                if !task.notes.isEmpty {
                    Text(task.notes)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
            }

            Spacer()

            // Priority indicator
            Circle()
                .fill(priorityColor)
                .frame(width: 10, height: 10)
        }
        .padding(.vertical, 4)
        .contentShape(Rectangle())
    }
}
