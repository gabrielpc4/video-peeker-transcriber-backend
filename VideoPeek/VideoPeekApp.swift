//
//  VideoPeekApp.swift
//  VideoPeek
//
//  Created by Gabriel Pinheiro de Carvalho on 12/02/26.
//

import SwiftUI
import SwiftData

@main
struct VideoPeekApp: App {
    init() {
        Task { @MainActor in
            ConsoleLogStore.shared.startCaptureIfNeeded()
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(ConsoleLogStore.shared)
        }
        .modelContainer(for: [
            MediaItem.self,
        ])
    }
}
