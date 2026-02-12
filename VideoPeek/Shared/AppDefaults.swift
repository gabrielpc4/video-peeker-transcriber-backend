//
//  AppDefaults.swift
//  VideoPeek
//

import Foundation

enum AppDefaults {
    static let backendBaseUrlKey = "backendBaseUrl"
    static let defaultBackendBaseUrl = "https://videopeek-backend.onrender.com"

    static func ensureDefaultsRegistered() {
        // This avoids different @AppStorage sites having different default values.
        UserDefaults.standard.register(defaults: [
            backendBaseUrlKey: defaultBackendBaseUrl,
        ])
    }
}

