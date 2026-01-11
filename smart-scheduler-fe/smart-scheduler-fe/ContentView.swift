//
//  ContentView.swift
//  smart-scheduler-fe
//
//  Created by Sat Arora on 2026-01-05.
//

import SwiftUI

struct ContentView: View {
    @State private var speechManager = SpeechManager()
    @State private var authManager = GoogleAuthManager()
    @State private var apiService: APIService
    @State private var isAuthenticating = false
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var scheduleId: String?
    @State private var currentSchedule: [CalendarEvent] = []
    
    init() {
        let authManager = GoogleAuthManager()
        _authManager = State(initialValue: authManager)
        _apiService = State(initialValue: APIService(authManager: authManager))
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 25) {
                // Authentication Status
                if !authManager.isAuthenticated {
                    VStack(spacing: 15) {
                        Text("Sign in with Google to continue")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Button(action: authenticate) {
                            HStack {
                                Image(systemName: "person.circle.fill")
                                Text("Sign in with Google")
                            }
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(15)
                        }
                        .disabled(isAuthenticating)
                        
                        if isAuthenticating {
                            ProgressView()
                                .padding()
                        }
                    }
                    .padding()
                } else {
                    // Main Content
                    // Status Header
                    Text(speechManager.isRecording ? "Listening to your rant..." : "Smart Scheduler")
                        .font(.headline)
                        .foregroundColor(speechManager.isRecording ? .red : .primary)
                    
                    // Live Text Display
                    ScrollView {
                        Text(speechManager.transcript.isEmpty ? "Tap the mic and start talking about your day." : speechManager.transcript)
                            .font(.system(size: 20, weight: .medium, design: .rounded))
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .frame(maxHeight: .infinity)
                    .background(Color(.secondarySystemBackground))
                    .cornerRadius(20)
                    
                    // Record Button
                    Button(action: {
                        if speechManager.isRecording {
                            speechManager.stopRecording()
                        } else {
                            speechManager.startRecording()
                        }
                    }) {
                        ZStack {
                            Circle()
                                .fill(speechManager.isRecording ? Color.red.opacity(0.2) : Color.blue.opacity(0.2))
                                .frame(width: 90, height: 90)
                            
                            Image(systemName: speechManager.isRecording ? "stop.fill" : "mic.fill")
                                .font(.system(size: 40))
                                .foregroundColor(speechManager.isRecording ? .red : .blue)
                        }
                    }
                    
                    // Submit Button (Only shows when not recording and text exists)
                    if !speechManager.transcript.isEmpty && !speechManager.isRecording {
                        VStack(spacing: 10) {
                            Button(action: sendToBackend) {
                                HStack {
                                    if isLoading {
                                        ProgressView()
                                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    }
                                    Text(isLoading ? "Processing..." : "Update Schedule")
                                        .fontWeight(.bold)
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(15)
                            }
                            .disabled(isLoading)
                            
                            if let scheduleId = scheduleId {
                                Button(action: commitSchedule) {
                                    Text("Commit to Calendar")
                                        .fontWeight(.semibold)
                                        .frame(maxWidth: .infinity)
                                        .padding()
                                        .background(Color.green)
                                        .foregroundColor(.white)
                                        .cornerRadius(15)
                                }
                                .disabled(isLoading)
                            }
                        }
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                    
                    // Sign Out Button
                    Button(action: signOut) {
                        Text("Sign Out")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top)
                }
                
                // Error Message
                if let errorMessage = errorMessage {
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundColor(.red)
                        .padding()
                }
            }
            .padding()
            .navigationTitle("Smart Scheduler")
        }
    }
    
    // MARK: - Actions
    
    func authenticate() {
        isAuthenticating = true
        errorMessage = nil
        
        Task {
            do {
                try await authManager.authenticate()
                await MainActor.run {
                    isAuthenticating = false
                    errorMessage = nil
                }
            } catch {
                let errorMsg: String
                if let authError = error as? AuthError {
                    errorMsg = authError.errorDescription ?? "Authentication failed"
                } else {
                    errorMsg = "Authentication failed: \(error.localizedDescription)"
                }
                
                print("❌ Authentication error: \(error)")
                
                await MainActor.run {
                    errorMessage = errorMsg
                    isAuthenticating = false
                }
            }
        }
    }
    
    func sendToBackend() {
        guard !speechManager.transcript.isEmpty else { return }
        
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let response = try await apiService.generateSchedule(rant: speechManager.transcript)
                await MainActor.run {
                    scheduleId = response.schedule_id
                    currentSchedule = response.schedule
                    isLoading = false
                    errorMessage = nil
                }
            } catch {
                await MainActor.run {
                    errorMessage = "Failed to generate schedule: \(error.localizedDescription)"
                    isLoading = false
                }
            }
        }
    }
    
    func commitSchedule() {
        guard let scheduleId = scheduleId else { return }
        
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let response = try await apiService.commitSchedule(scheduleId: scheduleId)
                await MainActor.run {
                    isLoading = false
                    errorMessage = "Successfully committed schedule to calendar!"
                    self.scheduleId = nil
                    speechManager.transcript = ""
                }
            } catch {
                await MainActor.run {
                    errorMessage = "Failed to commit schedule: \(error.localizedDescription)"
                    isLoading = false
                }
            }
        }
    }
    
    func signOut() {
        authManager.signOut()
        scheduleId = nil
        currentSchedule = []
        speechManager.transcript = ""
        errorMessage = nil
    }
}

#Preview {
    ContentView()
}
