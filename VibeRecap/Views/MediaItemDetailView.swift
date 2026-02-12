//
//  MediaItemDetailView.swift
//  VibeRecap
//
//  Created by Gabriel Pinheiro de Carvalho on 12/02/26.
//

import SwiftUI
import SwiftData

struct MediaItemDetailView: View {
    @Environment(\.modelContext) private var modelContext

    @Bindable var mediaItem: MediaItem

    @State private var isActionInProgress = false
    @State private var currentActionTitle: String?
    @State private var actionErrorMessage: String?

    @AppStorage("backendBaseUrl") private var backendBaseUrlText = "http://127.0.0.1:8000"

    var body: some View {
        List {
            Section {
                Button {
                    startTranscription()
                } label: {
                    if isActionInProgress, currentActionTitle == "Transcrever" {
                        HStack(spacing: 10) {
                            ProgressView()
                            Text("Transcrevendo…")
                        }
                    } else {
                        Text("Transcrever")
                    }
                }
                .disabled(isActionInProgress)

                Button {
                    startBreakdown()
                } label: {
                    if isActionInProgress, currentActionTitle == "Breakdown" {
                        HStack(spacing: 10) {
                            ProgressView()
                            Text(secondStepInProgressText)
                        }
                    } else {
                        Text(secondStepButtonTitle)
                    }
                }
                .disabled(isActionInProgress)
            }

            Section("Transcript") {
                if let transcriptText = mediaItem.transcriptText, transcriptText.isEmpty == false {
                    Text(transcriptText)
                        .textSelection(.enabled)
                } else {
                    Text("Ainda não transcrito.")
                        .foregroundStyle(.secondary)
                }
            }

            if mediaItem.sourceType == .audioFile {
                Section("Recap") {
                    if recapBullets.isEmpty == false {
                        ForEach(recapBullets, id: \.self) { bulletText in
                            Text("• \(bulletText)")
                        }
                    } else {
                        Text("Ainda não gerado.")
                            .foregroundStyle(.secondary)
                    }
                }
            } else {
                Section("Breakdown (JSON)") {
                    if let breakdownJson = mediaItem.breakdownJson, breakdownJson.isEmpty == false {
                        Text(breakdownJson)
                            .textSelection(.enabled)
                    } else {
                        Text("Ainda não gerado.")
                            .foregroundStyle(.secondary)
                    }
                }
            }

            if let lastErrorMessage = mediaItem.lastErrorMessage, lastErrorMessage.isEmpty == false {
                Section("Erro") {
                    Text(lastErrorMessage)
                        .foregroundStyle(.red)
                }
            }
        }
        .navigationTitle(navigationTitleText)
        .navigationBarTitleDisplayMode(.inline)
        .alert("Erro", isPresented: isActionErrorPresented) {
            Button("OK") {
                actionErrorMessage = nil
            }
        } message: {
            Text(actionErrorMessage ?? "")
        }
    }

    private var navigationTitleText: String {
        if mediaItem.sourceType == .audioFile {
            return "Áudio"
        }

        if mediaItem.sourceType == .url {
            return "Link"
        }

        return "Item"
    }

    private var secondStepButtonTitle: String {
        if mediaItem.sourceType == .audioFile {
            return "Gerar recap"
        }

        return "Gerar breakdown"
    }

    private var secondStepInProgressText: String {
        if mediaItem.sourceType == .audioFile {
            return "Gerando recap…"
        }

        return "Gerando breakdown…"
    }

    private var recapBullets: [String] {
        let rawJsonText = (mediaItem.breakdownJson ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if rawJsonText.isEmpty {
            return []
        }

        guard let rawJsonData = rawJsonText.data(using: .utf8) else {
            return []
        }

        guard
            let rawObject = try? JSONSerialization.jsonObject(with: rawJsonData, options: []),
            let rawDictionary = rawObject as? [String: Any]
        else {
            return []
        }

        guard let rawBullets = rawDictionary["recapBullets"] as? [Any] else {
            return []
        }

        let bulletTexts = rawBullets.compactMap { item -> String? in
            guard let textItem = item as? String else {
                return nil
            }

            let trimmedText = textItem.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmedText.isEmpty {
                return nil
            }

            return trimmedText
        }

        return bulletTexts
    }

    private var isActionErrorPresented: Binding<Bool> {
        Binding(
            get: {
                actionErrorMessage != nil
            },
            set: { isPresented in
                if isPresented == false {
                    actionErrorMessage = nil
                }
            }
        )
    }

    private func startTranscription() {
        if isActionInProgress {
            return
        }

        isActionInProgress = true
        currentActionTitle = "Transcrever"
        actionErrorMessage = nil

        Task { @MainActor in
            defer {
                isActionInProgress = false
                currentActionTitle = nil
            }

            do {
                try await transcribe()
            } catch {
                actionErrorMessage = error.localizedDescription
            }
        }
    }

    private func startBreakdown() {
        if isActionInProgress {
            return
        }

        isActionInProgress = true
        currentActionTitle = "Breakdown"
        actionErrorMessage = nil

        Task { @MainActor in
            defer {
                isActionInProgress = false
                currentActionTitle = nil
            }

            do {
                try await breakdown()
            } catch {
                actionErrorMessage = error.localizedDescription
            }
        }
    }

    private func backendBaseUrl() throws -> URL {
        let rawText = backendBaseUrlText.trimmingCharacters(in: .whitespacesAndNewlines)

        guard let url = URL(string: rawText) else {
            throw MediaItemActionError.invalidBackendUrl
        }

        return url
    }

    private func ensureRemoteItemExists(client: BackendClient) async throws -> String {
        if let remoteItemIdentifier = mediaItem.remoteItemIdentifier, remoteItemIdentifier.isEmpty == false {
            return remoteItemIdentifier
        }

        let remoteItemIdentifier: String

        if mediaItem.sourceType == .url {
            let sourceUrlText = (mediaItem.sourceUrl ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
            if sourceUrlText.isEmpty {
                throw MediaItemActionError.missingSourceUrl
            }

            remoteItemIdentifier = try await client.createUrlItem(sourceUrl: sourceUrlText)
        } else if mediaItem.sourceType == .audioFile {
            let localFileUrl = try resolveLocalAudioFileUrl()
            remoteItemIdentifier = try await client.uploadAudioItem(fileUrl: localFileUrl)
        } else {
            throw MediaItemActionError.unsupportedSourceType
        }

        mediaItem.remoteItemIdentifier = remoteItemIdentifier
        try modelContext.save()

        return remoteItemIdentifier
    }

    private func resolveLocalAudioFileUrl() throws -> URL {
        guard let storedFilename = mediaItem.storedFilename, storedFilename.isEmpty == false else {
            throw MediaItemActionError.missingStoredFilename
        }

        guard let containerUrl = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: AppGroupConstants.appGroupIdentifier) else {
            throw ShareImportError.missingAppGroupContainer
        }

        let mediaFolderUrl = containerUrl.appendingPathComponent(AppGroupConstants.mediaFolderName, isDirectory: true)
        let fileUrl = mediaFolderUrl.appendingPathComponent(storedFilename, isDirectory: false)

        if FileManager.default.fileExists(atPath: fileUrl.path) == false {
            throw MediaItemActionError.missingLocalMediaFile(filename: storedFilename)
        }

        return fileUrl
    }

    private func transcribe() async throws {
        let client = BackendClient(baseUrl: try backendBaseUrl())
        let itemId = try await ensureRemoteItemExists(client: client)

        mediaItem.transcriptionStatus = .running
        mediaItem.lastErrorMessage = nil
        try modelContext.save()

        _ = try await client.startTranscription(itemId: itemId)
        let finalResponse = try await pollUntilFinished(itemId: itemId, client: client, kind: "transcription")

        mediaItem.transcriptionStatusRaw = finalResponse.transcription_status
        mediaItem.detectedLanguage = finalResponse.detected_language
        mediaItem.transcriptText = finalResponse.transcript_text
        mediaItem.lastErrorMessage = finalResponse.last_error
        try modelContext.save()
    }

    private func breakdown() async throws {
        let transcriptText = (mediaItem.transcriptText ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if transcriptText.isEmpty {
            throw MediaItemActionError.missingTranscriptForBreakdown
        }

        let client = BackendClient(baseUrl: try backendBaseUrl())
        let itemId = try await ensureRemoteItemExists(client: client)

        mediaItem.breakdownStatus = .running
        mediaItem.lastErrorMessage = nil
        try modelContext.save()

        _ = try await client.startBreakdown(itemId: itemId)
        let finalResponse = try await pollUntilFinished(itemId: itemId, client: client, kind: "breakdown")

        mediaItem.breakdownStatusRaw = finalResponse.breakdown_status
        mediaItem.breakdownJson = finalResponse.breakdown_json
        mediaItem.lastErrorMessage = finalResponse.last_error
        try modelContext.save()
    }

    private func pollUntilFinished(itemId: String, client: BackendClient, kind: String) async throws -> BackendClient.ItemResponse {
        var remainingAttempts = 120

        while remainingAttempts > 0 {
            let response = try await client.getItem(itemId: itemId)

            if kind == "transcription" {
                if response.transcription_status == JobStatus.completed.rawValue {
                    return response
                }

                if response.transcription_status == JobStatus.failed.rawValue {
                    return response
                }
            } else {
                if response.breakdown_status == JobStatus.completed.rawValue {
                    return response
                }

                if response.breakdown_status == JobStatus.failed.rawValue {
                    return response
                }
            }

            try await Task.sleep(nanoseconds: 1_000_000_000)
            remainingAttempts -= 1
        }

        throw MediaItemActionError.pollingTimedOut
    }
}

enum MediaItemActionError: LocalizedError {
    case invalidBackendUrl
    case missingSourceUrl
    case missingStoredFilename
    case missingLocalMediaFile(filename: String)
    case missingTranscriptForBreakdown
    case unsupportedSourceType
    case pollingTimedOut

    var errorDescription: String? {
        switch self {
        case .invalidBackendUrl:
            return "URL do backend inválida."
        case .missingSourceUrl:
            return "Esse item não tem link salvo."
        case .missingStoredFilename:
            return "Esse item não tem arquivo local salvo."
        case let .missingLocalMediaFile(filename):
            return "Não achei o arquivo local: \(filename)"
        case .missingTranscriptForBreakdown:
            return "Antes de gerar breakdown, você precisa transcrever."
        case .unsupportedSourceType:
            return "Tipo de item não suportado."
        case .pollingTimedOut:
            return "Demorou demais para finalizar. Tente de novo."
        }
    }
}

#Preview {
    NavigationStack {
        MediaItemDetailView(
            mediaItem: MediaItem(
                importedItemIdentifier: UUID().uuidString,
                createdAt: Date(),
                sourceType: .url,
                sourceUrl: "https://example.com",
                storedFilename: nil
            )
        )
    }
    .modelContainer(for: [MediaItem.self], inMemory: true)
}

