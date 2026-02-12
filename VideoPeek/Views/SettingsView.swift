//
//  SettingsView.swift
//  VideoPeek
//
//  Created by Gabriel Pinheiro de Carvalho on 12/02/26.
//

import SwiftUI
import UIKit

struct SettingsView: View {
    @AppStorage(AppDefaults.backendBaseUrlKey) private var backendBaseUrlText = AppDefaults.defaultBackendBaseUrl
    @State private var youtubeCookiesDebugText: String?
    @State private var youtubeCookiesDebugError: String?
    @State private var isFetchingYoutubeCookies = false
    @State private var isYoutubeCookiesSheetPresented = false

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

            Section("Debug") {
                Button {
                    Task { @MainActor in
                        await fetchYoutubeCookiesDebug()
                    }
                } label: {
                    if isFetchingYoutubeCookies {
                        HStack {
                            ProgressView()
                            Text("Carregando cookies do YouTube…")
                        }
                    } else {
                        Text("Ver cookies do YouTube (backend)")
                    }
                }
                .disabled(isFetchingYoutubeCookies)

                if let youtubeCookiesDebugError, youtubeCookiesDebugError.isEmpty == false {
                    Text(youtubeCookiesDebugError)
                        .font(.footnote)
                        .foregroundStyle(.red)
                        .textSelection(.enabled)
                }
            }
        }
        .navigationTitle("Settings")
        .sheet(isPresented: $isYoutubeCookiesSheetPresented) {
            NavigationStack {
                ScrollView {
                    Text(youtubeCookiesDebugText ?? "")
                        .font(.system(.footnote, design: .monospaced))
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding()
                }
                .navigationTitle("YouTube cookies")
                .toolbar {
                    ToolbarItem(placement: .topBarLeading) {
                        Button("Fechar") {
                            isYoutubeCookiesSheetPresented = false
                        }
                    }
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Copiar") {
                            UIPasteboard.general.string = youtubeCookiesDebugText ?? ""
                        }
                        .disabled((youtubeCookiesDebugText ?? "").isEmpty)
                    }
                }
            }
        }
    }

    @MainActor
    private func fetchYoutubeCookiesDebug() async {
        youtubeCookiesDebugError = nil
        youtubeCookiesDebugText = nil
        isFetchingYoutubeCookies = true
        defer { isFetchingYoutubeCookies = false }

        do {
            let baseUrl = backendBaseUrlText.trimmingCharacters(in: .whitespacesAndNewlines)
            guard let url = URL(string: baseUrl) else {
                youtubeCookiesDebugError = "Base URL inválida."
                return
            }

            let client = BackendClient(baseUrl: url)
            let response = try await client.debugYoutubeCookies()

            var lines: [String] = []
            lines.append("path: \(response.path)")
            lines.append("exists: \(response.exists)")
            if let size = response.size_bytes {
                lines.append("size_bytes: \(size)")
            }
            if let mtime = response.mtime_iso {
                lines.append("mtime_iso: \(mtime)")
            }
            if let storage = response.storage_dir {
                lines.append("storage_dir: \(storage)")
            }
            if let error = response.error, error.isEmpty == false {
                lines.append("error: \(error)")
            }
            lines.append("")
            lines.append(response.content ?? "")

            youtubeCookiesDebugText = lines.joined(separator: "\n")
            isYoutubeCookiesSheetPresented = true
        } catch {
            youtubeCookiesDebugError = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack {
        SettingsView()
    }
}

