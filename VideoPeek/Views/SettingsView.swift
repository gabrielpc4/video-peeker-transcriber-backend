//
//  SettingsView.swift
//  VideoPeek
//
//  Created by Gabriel Pinheiro de Carvalho on 12/02/26.
//

import SwiftUI

struct SettingsView: View {
    @AppStorage(AppDefaults.backendBaseUrlKey) private var backendBaseUrlText = AppDefaults.defaultBackendBaseUrl

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

