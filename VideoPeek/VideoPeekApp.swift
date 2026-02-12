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
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(for: [
            MediaItem.self,
        ])
    }
}
