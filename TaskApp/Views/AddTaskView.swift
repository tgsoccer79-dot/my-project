import SwiftUI

struct AddTaskView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var store: TaskStore

    // Editing an existing task when non-nil
    var editingTask: Task?

    @State private var title: String = ""
    @State private var notes: String = ""
    @State private var priority: Task.Priority = .medium
    @State private var hasReminder: Bool = false
    @State private var reminderDate: Date = Date().addingTimeInterval(3600)
    @State private var showPermissionAlert = false

    private var isEditing: Bool { editingTask != nil }

    var body: some View {
        NavigationStack {
            Form {
                Section("タスク") {
                    TextField("タイトル", text: $title)
                    TextField("メモ", text: $notes, axis: .vertical)
                        .lineLimit(3...6)
                }

                Section("優先度") {
                    Picker("優先度", selection: $priority) {
                        ForEach(Task.Priority.allCases, id: \.self) { p in
                            Text(p.label).tag(p)
                        }
                    }
                    .pickerStyle(.segmented)
                }

                Section("リマインド") {
                    Toggle("リマインド通知", isOn: $hasReminder)
                    if hasReminder {
                        DatePicker(
                            "日時",
                            selection: $reminderDate,
                            in: Date()...,
                            displayedComponents: [.date, .hourAndMinute]
                        )
                    }
                }
            }
            .navigationTitle(isEditing ? "タスクを編集" : "新しいタスク")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("キャンセル") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(isEditing ? "保存" : "追加") {
                        saveTask()
                    }
                    .disabled(title.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .alert("通知の許可が必要です", isPresented: $showPermissionAlert) {
                Button("設定を開く") {
                    if let url = URL(string: UIApplication.openSettingsURLString) {
                        UIApplication.shared.open(url)
                    }
                }
                Button("キャンセル", role: .cancel) { hasReminder = false }
            } message: {
                Text("リマインド通知を使うには、設定アプリで通知を許可してください。")
            }
            .onChange(of: hasReminder) { _, enabled in
                if enabled {
                    Task { await requestNotificationPermission() }
                }
            }
            .onAppear { populateIfEditing() }
        }
    }

    // MARK: - Helpers

    private func populateIfEditing() {
        guard let task = editingTask else { return }
        title = task.title
        notes = task.notes
        priority = task.priority
        if let date = task.reminderDate {
            hasReminder = true
            reminderDate = date
        }
    }

    private func saveTask() {
        var task = editingTask ?? Task(title: "")
        task.title = title.trimmingCharacters(in: .whitespaces)
        task.notes = notes
        task.priority = priority
        task.reminderDate = hasReminder ? reminderDate : nil

        if isEditing {
            store.update(task)
        } else {
            store.add(task)
        }

        if hasReminder {
            NotificationManager.shared.scheduleReminder(for: task)
        } else {
            NotificationManager.shared.cancelReminder(for: task)
        }

        dismiss()
    }

    private func requestNotificationPermission() async {
        let granted = await NotificationManager.shared.requestAuthorization()
        if !granted {
            await MainActor.run { showPermissionAlert = true }
        }
    }
}
