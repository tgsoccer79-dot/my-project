import SwiftUI

struct TaskListView: View {
    @EnvironmentObject private var store: TaskStore
    @State private var showAdd = false
    @State private var selectedFilter: Filter = .pending
    @State private var searchText = ""

    enum Filter: String, CaseIterable {
        case pending  = "未完了"
        case upcoming = "期日順"
        case completed = "完了済"
    }

    private var filteredTasks: [Task] {
        let base: [Task]
        switch selectedFilter {
        case .pending:   base = store.pendingTasks
        case .upcoming:  base = store.upcomingTasks
        case .completed: base = store.completedTasks
        }

        guard !searchText.isEmpty else { return base }
        return base.filter {
            $0.title.localizedCaseInsensitiveContains(searchText) ||
            $0.notes.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Filter picker
                Picker("フィルター", selection: $selectedFilter) {
                    ForEach(Filter.allCases, id: \.self) {
                        Text($0.rawValue).tag($0)
                    }
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)
                .padding(.vertical, 8)

                if filteredTasks.isEmpty {
                    emptyState
                } else {
                    List {
                        ForEach(filteredTasks) { task in
                            NavigationLink(destination: TaskDetailView(task: task)) {
                                TaskRowView(task: task) {
                                    store.toggleComplete(task)
                                }
                            }
                        }
                        .onDelete { offsets in
                            let ids = offsets.map { filteredTasks[$0].id }
                            ids.forEach { id in
                                if let t = store.tasks.first(where: { $0.id == id }) {
                                    NotificationManager.shared.cancelReminder(for: t)
                                }
                            }
                            store.tasks.removeAll { ids.contains($0.id) }
                        }
                    }
                    .listStyle(.insetGrouped)
                }
            }
            .navigationTitle("タスク")
            .searchable(text: $searchText, prompt: "タスクを検索")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showAdd = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showAdd) {
                AddTaskView()
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: selectedFilter == .completed ? "checkmark.circle" : "tray")
                .font(.system(size: 56))
                .foregroundColor(.secondary)
            Text(emptyMessage)
                .font(.headline)
                .foregroundColor(.secondary)
            if selectedFilter == .pending {
                Button("タスクを追加") { showAdd = true }
                    .buttonStyle(.borderedProminent)
            }
            Spacer()
        }
        .frame(maxWidth: .infinity)
    }

    private var emptyMessage: String {
        switch selectedFilter {
        case .pending:   return "タスクがありません"
        case .upcoming:  return "期日のあるタスクがありません"
        case .completed: return "完了済みのタスクがありません"
        }
    }
}
