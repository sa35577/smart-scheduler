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
    @State private var inputMode: InputMode = .speech
    @State private var typedText: String = ""
    @FocusState private var isTextFieldFocused: Bool
    @State private var showSchedule = false
    @State private var isAdjusting = false
    @State private var adjustmentText: String = ""
    @State private var showTodaySchedule = false
    @State private var todayEvents: [CalendarEvent] = []
    @State private var isLoadingTodayEvents = false
    
    enum InputMode {
        case speech
        case text
    }
    
    init() {
        let authManager = GoogleAuthManager()
        _authManager = State(initialValue: authManager)
        _apiService = State(initialValue: APIService(authManager: authManager))
    }
    
    // Computed property to get the current input text
    private var currentInputText: String {
        switch inputMode {
        case .speech:
            return speechManager.transcript
        case .text:
            return typedText
        }
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
                    // Input Mode Selector
                    Picker("Input Mode", selection: $inputMode) {
                        Text("🎤 Speech").tag(InputMode.speech)
                        Text("⌨️ Text").tag(InputMode.text)
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal)
                    
                    // Status Header
                    Text(inputMode == .speech && speechManager.isRecording ? "Listening to your rant..." : "Smart Scheduler")
                        .font(.headline)
                        .foregroundColor(inputMode == .speech && speechManager.isRecording ? .red : .primary)
                    
                    // Input Area - Different based on mode
                    if inputMode == .speech {
                        // Speech Mode - Live Text Display
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
                    } else {
                        // Text Mode - Text Input Field
                        TextEditor(text: $typedText)
                            .font(.system(size: 20, weight: .medium, design: .rounded))
                            .padding(8)
                            .frame(maxHeight: .infinity)
                            .background(Color(.secondarySystemBackground))
                            .cornerRadius(20)
                            .overlay(
                                Group {
                                    if typedText.isEmpty {
                                        VStack {
                                            HStack {
                                                Text("Type your schedule request here...")
                                                    .foregroundColor(.secondary)
                                                    .padding(.leading, 12)
                                                    .padding(.top, 16)
                                                Spacer()
                                            }
                                            Spacer()
                                        }
                                    }
                                }
                            )
                            .focused($isTextFieldFocused)
                    }
                    
                    // Submit Button (Only shows when not recording and text exists)
                    if !currentInputText.isEmpty && (inputMode == .text || !speechManager.isRecording) {
                        Button(action: sendToBackend) {
                            HStack {
                                if isLoading {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                }
                                Text(isLoading ? "Processing..." : isAdjusting ? "Update Schedule" : "Generate Schedule")
                                    .fontWeight(.bold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(15)
                        }
                        .disabled(isLoading)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                    
                    // Show Schedule Button (if schedule exists and not adjusting)
                    if let scheduleId = scheduleId, !currentSchedule.isEmpty, !isAdjusting {
                        Button(action: {
                            showSchedule = true
                        }) {
                            HStack {
                                Image(systemName: "calendar")
                                Text("View Schedule")
                            }
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.purple)
                            .foregroundColor(.white)
                            .cornerRadius(15)
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
            .overlay(alignment: .bottomTrailing) {
                // Floating button to view today's schedule
                if authManager.isAuthenticated {
                    Button(action: loadTodaySchedule) {
                        HStack(spacing: 8) {
                            Image(systemName: "calendar")
                            Text("Today")
                        }
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .background(Color.blue)
                        .cornerRadius(25)
                        .shadow(color: .black.opacity(0.2), radius: 5, x: 0, y: 2)
                    }
                    .padding(.trailing, 20)
                    .padding(.bottom, 20)
                }
            }
            .sheet(isPresented: $showSchedule) {
                if let scheduleId = scheduleId {
                    ScheduleView(
                        schedule: currentSchedule,
                        scheduleId: scheduleId,
                        isPresented: $showSchedule,
                        onAdjust: {
                            showSchedule = false
                            isAdjusting = true
                            // Pre-fill with adjustment prompt
                            if inputMode == .text {
                                typedText = "Adjust the schedule: "
                                isTextFieldFocused = true
                            } else {
                                // Switch to text mode for adjustments
                                inputMode = .text
                                typedText = "Adjust the schedule: "
                                isTextFieldFocused = true
                            }
                        },
                        onCommit: {
                            commitSchedule()
                            showSchedule = false
                        }
                    )
                }
            }
            .sheet(isPresented: $showTodaySchedule) {
                TodayScheduleView(
                    events: todayEvents,
                    isLoading: isLoadingTodayEvents,
                    isPresented: $showTodaySchedule
                )
            }
        }
    }
    
    func loadTodaySchedule() {
        showTodaySchedule = true
        isLoadingTodayEvents = true
        
        Task {
            do {
                let response = try await apiService.getTodayEvents()
                await MainActor.run {
                    todayEvents = response.events
                    isLoadingTodayEvents = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = "Failed to load today's schedule: \(error.localizedDescription)"
                    isLoadingTodayEvents = false
                }
            }
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
        let textToSend = currentInputText
        guard !textToSend.isEmpty else { return }
        
        isLoading = true
        errorMessage = nil
        
        // Dismiss keyboard if in text mode
        if inputMode == .text {
            isTextFieldFocused = false
        }
        
        Task {
            do {
                let response: ScheduleResponse
                
                if isAdjusting, let scheduleId = scheduleId {
                    // Provide feedback to adjust existing schedule
                    response = try await apiService.provideFeedback(scheduleId: scheduleId, feedback: textToSend)
                } else {
                    // Generate new schedule
                    response = try await apiService.generateSchedule(rant: textToSend)
                }
                
                await MainActor.run {
                    scheduleId = response.schedule_id
                    currentSchedule = response.schedule
                    isLoading = false
                    errorMessage = nil
                    isAdjusting = false
                    
                    // Clear input after successful submission
                    if inputMode == .text {
                        typedText = ""
                    } else {
                        speechManager.transcript = ""
                    }
                    
                    // Automatically show the schedule
                    if !response.schedule.isEmpty {
                        showSchedule = true
                    }
                }
            } catch {
                await MainActor.run {
                    errorMessage = "Failed to \(isAdjusting ? "adjust" : "generate") schedule: \(error.localizedDescription)"
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
                    self.currentSchedule = []
                    self.showSchedule = false
                    // Clear input based on current mode
                    if inputMode == .text {
                        typedText = ""
                    } else {
                        speechManager.transcript = ""
                    }
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
        typedText = ""
        errorMessage = nil
    }
}

#Preview {
    ContentView()
}
