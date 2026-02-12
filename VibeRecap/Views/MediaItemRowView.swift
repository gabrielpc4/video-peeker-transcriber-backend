//
//  MediaItemRowView.swift
//  VibeRecap
//
//  Created by Gabriel Pinheiro de Carvalho on 12/02/26.
//

import SwiftUI

struct MediaItemRowView: View {
    let mediaItem: MediaItem

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 10) {
                Image(systemName: iconName)
                    .foregroundStyle(.secondary)

                Text(titleText)
                    .font(.headline)
            }

            Text(mediaItem.createdAt, style: .time)
                .font(.footnote)
                .foregroundStyle(.secondary)

            Text(statusText)
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
    }

    private var iconName: String {
        if mediaItem.sourceType == .audioFile {
            return "waveform"
        }

        if mediaItem.sourceType == .url {
            return "link"
        }

        return "questionmark.circle"
    }

    private var titleText: String {
        if mediaItem.sourceType == .audioFile {
            return "Áudio"
        }

        if mediaItem.sourceType == .url {
            return "Link"
        }

        return "Item"
    }

    private var statusText: String {
        let transcriptionStatus = mediaItem.transcriptionStatus
        let breakdownStatus = mediaItem.breakdownStatus

        if breakdownStatus == .completed {
            return "Breakdown pronto"
        }

        if breakdownStatus == .running {
            return "Gerando breakdown…"
        }

        if transcriptionStatus == .completed {
            return "Transcrito (pronto para breakdown)"
        }

        if transcriptionStatus == .running {
            return "Transcrevendo…"
        }

        if transcriptionStatus == .failed || breakdownStatus == .failed {
            return "Falhou"
        }

        return "Pendente"
    }
}

#Preview {
    MediaItemRowView(
        mediaItem: MediaItem(
            importedItemIdentifier: UUID().uuidString,
            createdAt: Date(),
            sourceType: .url,
            sourceUrl: "https://example.com",
            storedFilename: nil
        )
    )
}

