import SwiftUI

struct TaskDetailView: View {
    @EnvironmentObject private var store: TaskStore
    @Environment(\.dismiss) private var dismiss

    let task: Task
    @State private var showEdit = false

    private var current: Task {
        store.tasks.first { $0.id == task.id } ?? task
    }

    var body: some View {
        List {
            Section {
                HStack {
                    Image(systemName: current.isCompleted ? "checkmark.circle.fill" : "circle")
                        .font(.title)
                        .foregroundColor(current.isCompleted ? .accentColor : .secondary)
                    Text(current.title)
                        .font(.title2.bold())
                }
            }

            if !current.notes.isEmpty {
                Section("メモ") {
                    Text(current.notes)
                }
            }

            Section("詳細") {
                LabeledContent("優先度", value: current.priority.label)

                if let date = current.reminderDate {
                    LabeledContent("リマインド") {
                        Label(
                            date.formatted(date: .long, time: .shortened),
                            systemImage: "bell"
                        )
                        .foregroundColor(current.isOverdue ? .red : .primary)
                    }
                }

                LabeledContent(
                    "作成日",
                    value: current.createdAt.formatted(date: .abbreviated, time: .shortened)
                )
            }

            Section {
                Button(current.isCompleted ? "未完了に戻す" : "完了にする") {
                    store.toggleComplete(current)
                }
                .foregroundColor(current.isCompleted ? .orange : .accentColor)

                Button("タスクを削除", role: .destructive) {
                    store.delete(current)
                    NotificationManager.shared.cancelReminder(for: current)
                    dismiss()
                }
            }
        }
        .navigationTitle("タスク詳細")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("編集") { showEdit = true }
            }
        }
        .sheet(isPresented: $showEdit) {
            AddTaskView(editingTask: current)
        }
    }
}
