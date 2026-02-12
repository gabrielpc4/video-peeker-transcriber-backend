//
//  ContentView.swift
//  myprojectname
//
//  Created by Gabriel Carvalho on 12/02/26.
//

import SwiftUI
import SwiftData

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.scenePhase) private var scenePhase

    @Query(sort: \MediaItem.createdAt, order: .reverse)
    private var mediaItems: [MediaItem]

    @State private var pasteUrlText = ""

    @State private var isImportInProgress = false
    @State private var importErrorMessage: String?

    @State private var isSettingsPresented = false

    var body: some View {
        NavigationStack {
            List {
                Section("Adicionar link") {
                    TextField("Cole link do YouTube ou Instagram", text: $pasteUrlText)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()

                    Button("Adicionar") {
                        addPastedUrlItem()
                    }
                    .disabled(pasteUrlText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }

                if isImportInProgress {
                    Section {
                        HStack(spacing: 12) {
                            ProgressView()
                            Text("Importando do Share…")
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                Section("Itens") {
                    if mediaItems.isEmpty {
                        Text("Nada ainda. Compartilhe um áudio/link ou cole um link acima.")
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(mediaItems) { item in
                            NavigationLink {
                                MediaItemDetailView(mediaItem: item)
                            } label: {
                                MediaItemRowView(mediaItem: item)
                            }
                        }
                    }
                }
            }
            .navigationTitle("VibeRecap")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Settings") {
                        isSettingsPresented = true
                    }
                }
            }
            .task {
                await importPendingItems()
            }
            .onChange(of: scenePhase) { newScenePhase in
                if newScenePhase == .active {
                    Task {
                        await importPendingItems()
                    }
                }
            }
            .refreshable {
                await importPendingItems()
            }
            .alert("Erro", isPresented: isImportErrorPresented) {
                Button("OK") {
                    importErrorMessage = nil
                }
            } message: {
                Text(importErrorMessage ?? "")
            }
        }
        .sheet(isPresented: $isSettingsPresented) {
            NavigationStack {
                SettingsView()
            }
        }
    }

    private var isImportErrorPresented: Binding<Bool> {
        Binding(
            get: {
                importErrorMessage != nil
            },
            set: { isPresented in
                if isPresented == false {
                    importErrorMessage = nil
                }
            }
        )
    }

    private func importPendingItems() async {
        if isImportInProgress {
            return
        }

        isImportInProgress = true
        defer {
            isImportInProgress = false
        }

        do {
            let shareImportService = ShareImportService()
            let importedCount = try shareImportService.importPendingItems(modelContext: modelContext)
            _ = importedCount
        } catch {
            importErrorMessage = error.localizedDescription
        }
    }

    private func addPastedUrlItem() {
        let trimmedUrlText = pasteUrlText.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedUrlText.isEmpty {
            return
        }

        let importedItemIdentifier = UUID().uuidString

        let newItem = MediaItem(
            importedItemIdentifier: importedItemIdentifier,
            createdAt: Date(),
            sourceType: .url,
            sourceUrl: trimmedUrlText,
            storedFilename: nil
        )

        modelContext.insert(newItem)

        do {
            try modelContext.save()
            pasteUrlText = ""
        } catch {
            importErrorMessage = error.localizedDescription
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: [MediaItem.self], inMemory: true)
}
