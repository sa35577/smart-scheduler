//
//  APIService.swift
//  smart-scheduler-fe
//
//  Handles all backend API communication
//

import Foundation
import Observation

@Observable
class APIService {
    private let baseURL: String
    private let authManager: GoogleAuthManager
    
    init(baseURL: String? = nil, authManager: GoogleAuthManager) {
        // Use provided URL, or environment-based default
        #if DEBUG
        // Development: Use Railway for testing, or localhost for local dev
        // Change this to "http://localhost:8000" when testing locally
        self.baseURL = baseURL ?? "https://smart-scheduler-production-240b.up.railway.app"
        #else
        // Production: Railway deployed backend URL
        self.baseURL = baseURL ?? "https://smart-scheduler-production-240b.up.railway.app"
        #endif
        self.authManager = authManager
    }
    
    // MARK: - Schedule Operations
    
    /// Generate a schedule from a user's rant/description
    func generateSchedule(rant: String) async throws -> ScheduleResponse {
        let accessToken = try await authManager.getValidAccessToken()
        let idToken = authManager.idToken
        
        if idToken != nil {
            print("✅ Sending id_token with request (length: \(idToken!.count))")
        } else {
            print("⚠️ No id_token available - user may need to re-authenticate")
        }
        
        let request = ScheduleRequest(rant: rant, access_token: accessToken, id_token: idToken)
        return try await post("/schedule/generate", body: request)
    }
    
    /// Provide feedback to adjust the current schedule
    func provideFeedback(scheduleId: String, feedback: String) async throws -> ScheduleResponse {
        let accessToken = try await authManager.getValidAccessToken()
        let idToken = authManager.idToken
        
        let request = FeedbackRequest(schedule_id: scheduleId, feedback: feedback, access_token: accessToken, id_token: idToken)
        return try await post("/schedule/feedback", body: request)
    }
    
    /// Get the current schedule for a session
    func getSchedule(scheduleId: String) async throws -> ScheduleResponse {
        let accessToken = try await authManager.getValidAccessToken()
        
        let url = URL(string: "\(baseURL)/schedule/\(scheduleId)?access_token=\(accessToken)")!
        return try await get(url: url)
    }
    
    /// Commit the schedule to Google Calendar
    func commitSchedule(scheduleId: String) async throws -> CommitResponse {
        let accessToken = try await authManager.getValidAccessToken()
        
        let request = CommitRequest(schedule_id: scheduleId, access_token: accessToken)
        return try await post("/schedule/commit", body: request)
    }
    
    // MARK: - Calendar Operations
    
    /// Get today's events
    func getTodayEvents() async throws -> TodayEventsResponse {
        let accessToken = try await authManager.getValidAccessToken()
        let idToken = authManager.idToken
        
        let request = TokenRequest(access_token: accessToken, id_token: idToken)
        return try await post("/calendar/today", body: request)
    }
    
    /// Get current date
    func getCurrentDate() async throws -> CurrentDateResponse {
        let accessToken = try await authManager.getValidAccessToken()
        let idToken = authManager.idToken
        
        let request = TokenRequest(access_token: accessToken, id_token: idToken)
        return try await post("/calendar/current-date", body: request)
    }
    
    // MARK: - Generic HTTP Methods
    
    private func post<T: Codable, U: Codable>(_ path: String, body: T) async throws -> U {
        let url = URL(string: "\(baseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw APIError.serverError(errorResponse.detail)
            }
            throw APIError.httpError(httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(U.self, from: data)
    }
    
    private func get<T: Codable>(url: URL) async throws -> T {
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw APIError.serverError(errorResponse.detail)
            }
            throw APIError.httpError(httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
}

// MARK: - Request/Response Models

struct ScheduleRequest: Codable {
    let rant: String
    let access_token: String
    let id_token: String?  // JWT with user email for backend logging
}

struct FeedbackRequest: Codable {
    let schedule_id: String
    let feedback: String
    let access_token: String
    let id_token: String?  // JWT with user email for backend logging
}

struct CommitRequest: Codable {
    let schedule_id: String
    let access_token: String
}

struct TokenRequest: Codable {
    let access_token: String
    let id_token: String?  // JWT with user email for backend logging
}

struct ScheduleResponse: Codable {
    let schedule_id: String
    let schedule: [CalendarEvent]
    let message: String?
}

struct CommitResponse: Codable {
    let message: String
    let schedule: [CalendarEvent]
}

struct TodayEventsResponse: Codable {
    let events: [CalendarEvent]
}

struct CurrentDateResponse: Codable {
    let current_date: String
}

struct CalendarEvent: Codable {
    let summary: String
    let start: String
    let end: String
    let already_in_calendar: Bool?
    let event_id: String?
    let original_start: String?
    let original_end: String?
    let is_modified: Bool?
    
    var eventStatus: EventStatus {
        if let alreadyInCalendar = already_in_calendar, alreadyInCalendar {
            if let isModified = is_modified, isModified {
                return .modified
            }
            return .existing
        }
        return .new
    }
}

enum EventStatus {
    case new
    case existing
    case modified
}

struct ErrorResponse: Codable {
    let detail: String
}

enum APIError: Error {
    case invalidResponse
    case httpError(Int)
    case serverError(String)
    case decodingError(Error)
}

