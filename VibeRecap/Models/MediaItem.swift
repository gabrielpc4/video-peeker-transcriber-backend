//
//  MediaItem.swift
//  VibeRecap
//
//  Created by Gabriel Pinheiro de Carvalho on 12/02/26.
//

import Foundation
import SwiftData

@Model
final class MediaItem {
    var importedItemIdentifier: String
    var createdAt: Date

    var sourceTypeRaw: String
    var sourceUrl: String?
    var storedFilename: String?

    var remoteItemIdentifier: String?

    var transcriptionStatusRaw: String
    var breakdownStatusRaw: String

    var detectedLanguage: String?
    var transcriptText: String?
    var breakdownJson: String?

    var lastErrorMessage: String?

    init(
        importedItemIdentifier: String,
        createdAt: Date,
        sourceType: MediaSourceType,
        sourceUrl: String?,
        storedFilename: String?
    ) {
        self.importedItemIdentifier = importedItemIdentifier
        self.createdAt = createdAt

        self.sourceTypeRaw = sourceType.rawValue
        self.sourceUrl = sourceUrl
        self.storedFilename = storedFilename

        self.remoteItemIdentifier = nil

        self.transcriptionStatusRaw = JobStatus.pending.rawValue
        self.breakdownStatusRaw = JobStatus.pending.rawValue

        self.detectedLanguage = nil
        self.transcriptText = nil
        self.breakdownJson = nil

        self.lastErrorMessage = nil
    }

    var sourceType: MediaSourceType {
        get {
            MediaSourceType(rawValue: sourceTypeRaw) ?? .unknown
        }
        set {
            sourceTypeRaw = newValue.rawValue
        }
    }

    var transcriptionStatus: JobStatus {
        get {
            JobStatus(rawValue: transcriptionStatusRaw) ?? .pending
        }
        set {
            transcriptionStatusRaw = newValue.rawValue
        }
    }

    var breakdownStatus: JobStatus {
        get {
            JobStatus(rawValue: breakdownStatusRaw) ?? .pending
        }
        set {
            breakdownStatusRaw = newValue.rawValue
        }
    }
}

enum MediaSourceType: String, Codable {
    case audioFile
    case url
    case unknown
}

enum JobStatus: String, Codable {
    case pending
    case running
    case completed
    case failed
}

