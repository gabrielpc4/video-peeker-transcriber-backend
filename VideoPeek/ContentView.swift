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
    @State private var selectedMediaItem: MediaItem?
    @State private var autoTranscribeImportedIdentifier: String?

    @State private var isImportInProgress = false
    @State private var importErrorMessage: String?

    @State private var isSettingsPresented = false

    @AppStorage("backendBaseUrl") private var backendBaseUrlText = "http://127.0.0.1:8000"

    var body: some View {
        NavigationStack {
            List {
                Section("Video a ser trabalhado") {
                    TextField("Cole link do YouTube ou Instagram", text: $pasteUrlText)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                        .submitLabel(.go)
                        .onSubmit {
                            addPastedUrlItem(shouldNavigateAndAutoTranscribe: true)
                        }
                        .onChange(of: pasteUrlText) { oldValue, newValue in
                            let trimmedOldValue = oldValue.trimmingCharacters(in: .whitespacesAndNewlines)
                            let trimmedNewValue = newValue.trimmingCharacters(in: .whitespacesAndNewlines)

                            if trimmedOldValue.isEmpty == false {
                                return
                            }

                            if trimmedNewValue.isEmpty {
                                return
                            }

                            if looksLikeUrl(text: trimmedNewValue) == false {
                                return
                            }

                            addPastedUrlItem(shouldNavigateAndAutoTranscribe: true)
                        }
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
                            Button {
                                autoTranscribeImportedIdentifier = nil
                                selectedMediaItem = item
                            } label: {
                                MediaItemRowView(mediaItem: item)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }
            .navigationTitle("VideoPeek")
            .navigationDestination(item: $selectedMediaItem) { item in
                let shouldAutoTranscribe = autoTranscribeImportedIdentifier == item.importedItemIdentifier
                MediaItemDetailView(
                    mediaItem: item,
                    shouldStartTranscriptionOnAppear: shouldAutoTranscribe
                )
            }
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

    private func addPastedUrlItem(shouldNavigateAndAutoTranscribe: Bool) {
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

            if shouldNavigateAndAutoTranscribe {
                autoTranscribeImportedIdentifier = importedItemIdentifier
                selectedMediaItem = newItem
            }

            Task { @MainActor in
                await resolveTitleIfPossible(mediaItem: newItem)
            }
        } catch {
            importErrorMessage = error.localizedDescription
        }
    }

    private func looksLikeUrl(text: String) -> Bool {
        if text.hasPrefix("http://") == false && text.hasPrefix("https://") == false {
            return false
        }

        guard let urlValue = URL(string: text) else {
            return false
        }

        let hostText = (urlValue.host ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if hostText.isEmpty {
            return false
        }

        return true
    }

    @MainActor
    private func resolveTitleIfPossible(mediaItem: MediaItem) async {
        if mediaItem.sourceType != .url {
            return
        }

        let sourceUrlText = (mediaItem.sourceUrl ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if sourceUrlText.isEmpty {
            return
        }

        guard let remoteItemIdentifier = mediaItem.remoteItemIdentifier, remoteItemIdentifier.isEmpty == false else {
            // Do not create remote items just to resolve a title; creation happens on transcribe/summary.
            return
        }

        let baseUrlText = backendBaseUrlText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let baseUrl = URL(string: baseUrlText) else {
            return
        }

        do {
            let client = BackendClient(baseUrl: baseUrl)

            let itemResponse = try await client.getItem(itemId: remoteItemIdentifier)
            if let titleText = itemResponse.title_text, titleText.isEmpty == false {
                mediaItem.titleText = titleText
                try modelContext.save()
            }
        } catch {
            // Keep host fallback if title lookup fails.
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: [MediaItem.self], inMemory: true)
}
