//
//  SettingsView.swift
//  VideoPeek
//
//  Created by Gabriel Pinheiro de Carvalho on 12/02/26.
//

import SwiftUI

struct SettingsView: View {
    @AppStorage("backendBaseUrl") private var backendBaseUrlText = "http://127.0.0.1:8000"

    var body: some View {
        Form {
            Section("Backend") {
                TextField("Base URL", text: $backendBaseUrlText)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()

                Text("Para testar no device físico, use o IP da sua máquina na mesma rede.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("Settings")
    }
}

#Preview {
    NavigationStack {
        SettingsView()
    }
}

