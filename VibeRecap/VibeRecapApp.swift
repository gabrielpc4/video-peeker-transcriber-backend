//
//  myprojectnameApp.swift
//  myprojectname
//
//  Created by Gabriel Carvalho on 12/02/26.
//

import SwiftUI
import SwiftData

@main
struct VibeRecapApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(for: [
            MediaItem.self,
        ])
    }
}
