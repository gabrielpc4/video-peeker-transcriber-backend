//
//  BackendClient.swift
//  VibeRecap
//
//  Created by Gabriel Pinheiro de Carvalho on 12/02/26.
//

import Foundation

struct BackendClient {
    struct CreateItemResponse: Decodable {
        let item_id: String
    }

    struct ItemResponse: Decodable {
        let item_id: String
        let created_at_iso: String
        let source_type: String
        let source_url: String?

        let title_text: String?

        let transcription_status: String
        let enhanced_transcript_status: String
        let summary_status: String
        let breakdown_status: String

        let detected_language: String?
        let transcript_text: String?
        let enhanced_transcript_text: String?
        let enhanced_transcript_error: String?
        let summary_json: String?
        let breakdown_json: String?

        let last_error: String?
    }

    let baseUrl: URL
    let urlSession: URLSession

    init(baseUrl: URL, urlSession: URLSession = .shared) {
        self.baseUrl = baseUrl
        self.urlSession = urlSession
    }

    func createUrlItem(sourceUrl: String) async throws -> String {
        let url = baseUrl.appendingPathComponent("items")

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "content-type")

        let requestBody = ["source_url": sourceUrl]
        request.httpBody = try JSONSerialization.data(withJSONObject: requestBody, options: [])

        let (data, response) = try await urlSession.data(for: request)
        try validateHttpResponse(response: response, data: data)

        let decoded = try JSONDecoder().decode(CreateItemResponse.self, from: data)
        return decoded.item_id
    }

    func uploadAudioItem(fileUrl: URL) async throws -> String {
        let url = baseUrl.appendingPathComponent("items/upload")

        let boundaryText = "Boundary-\(UUID().uuidString)"

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundaryText)", forHTTPHeaderField: "content-type")

        let fileData = try Data(contentsOf: fileUrl)
        let filenameText = fileUrl.lastPathComponent

        var bodyData = Data()

        bodyData.append("--\(boundaryText)\r\n".data(using: .utf8)!)
        bodyData.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filenameText)\"\r\n".data(using: .utf8)!)
        bodyData.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
        bodyData.append(fileData)
        bodyData.append("\r\n".data(using: .utf8)!)
        bodyData.append("--\(boundaryText)--\r\n".data(using: .utf8)!)

        let (data, response) = try await urlSession.upload(for: request, from: bodyData)
        try validateHttpResponse(response: response, data: data)

        let decoded = try JSONDecoder().decode(CreateItemResponse.self, from: data)
        return decoded.item_id
    }

    func startTranscription(itemId: String, extendedOutput: Bool = false) async throws -> ItemResponse {
        let url = urlForItemAction(itemId: itemId, path: "transcribe", extendedOutput: extendedOutput)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await urlSession.data(for: request)
        try validateHttpResponse(response: response, data: data)

        return try JSONDecoder().decode(ItemResponse.self, from: data)
    }

    func startBreakdown(itemId: String, extendedOutput: Bool = false) async throws -> ItemResponse {
        let url = urlForItemAction(itemId: itemId, path: "breakdown", extendedOutput: extendedOutput)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await urlSession.data(for: request)
        try validateHttpResponse(response: response, data: data)

        return try JSONDecoder().decode(ItemResponse.self, from: data)
    }

    func startSummary(itemId: String, extendedOutput: Bool = false) async throws -> ItemResponse {
        let url = urlForItemAction(itemId: itemId, path: "summary", extendedOutput: extendedOutput)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await urlSession.data(for: request)
        try validateHttpResponse(response: response, data: data)

        return try JSONDecoder().decode(ItemResponse.self, from: data)
    }

    private func urlForItemAction(itemId: String, path: String, extendedOutput: Bool) -> URL {
        var components = URLComponents(url: baseUrl.appendingPathComponent("items/\(itemId)/\(path)"), resolvingAgainstBaseURL: false)!
        if extendedOutput {
            components.queryItems = [URLQueryItem(name: "extended_output", value: "true")]
        }
        return components.url!
    }

    func getItem(itemId: String) async throws -> ItemResponse {
        let url = baseUrl.appendingPathComponent("items/\(itemId)")
        let (data, response) = try await urlSession.data(from: url)
        try validateHttpResponse(response: response, data: data)
        return try JSONDecoder().decode(ItemResponse.self, from: data)
    }

    private func validateHttpResponse(response: URLResponse, data: Data) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw BackendClientError.invalidResponse
        }

        if (200 ... 299).contains(httpResponse.statusCode) {
            return
        }

        let responseBody = String(decoding: data, as: UTF8.self)
        throw BackendClientError.httpError(statusCode: httpResponse.statusCode, responseBody: responseBody)
    }
}

enum BackendClientError: LocalizedError {
    case invalidResponse
    case httpError(statusCode: Int, responseBody: String)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "Resposta inválida do backend."
        case let .httpError(statusCode, responseBody):
            return "Backend retornou HTTP \(statusCode).\n\n\(responseBody)"
        }
    }
}

