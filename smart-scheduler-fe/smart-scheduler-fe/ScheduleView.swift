//
//  ScheduleView.swift
//  smart-scheduler-fe
//
//  Displays the proposed schedule and allows adjustments
//

import SwiftUI

struct ScheduleView: View {
    let schedule: [CalendarEvent]
    let scheduleId: String
    @Binding var isPresented: Bool
    let onAdjust: () -> Void
    let onCommit: () -> Void
    @State private var isLoading = false
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                // Header
                Text("Proposed Schedule")
                    .font(.title2)
                    .fontWeight(.bold)
                    .padding(.top)
                
                // Schedule List
                if schedule.isEmpty {
                    VStack(spacing: 15) {
                        Image(systemName: "calendar.badge.exclamationmark")
                            .font(.system(size: 50))
                            .foregroundColor(.secondary)
                        Text("No events scheduled")
                            .font(.headline)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxHeight: .infinity)
                } else {
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(Array(schedule.enumerated()), id: \.offset) { index, event in
                                ScheduleEventRow(event: event, index: index)
                            }
                        }
                        .padding()
                    }
                }
                
                // Action Buttons
                VStack(spacing: 12) {
                    Button(action: onAdjust) {
                        HStack {
                            Image(systemName: "pencil")
                            Text("Adjust Schedule")
                        }
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(15)
                    }
                    
                    Button(action: onCommit) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            }
                            Image(systemName: "checkmark.circle.fill")
                            Text(isLoading ? "Committing..." : "Commit to Calendar")
                        }
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(15)
                    }
                    .disabled(isLoading)
                }
                .padding(.horizontal)
                .padding(.bottom)
            }
            .navigationTitle("Schedule")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Back") {
                        isPresented = false
                    }
                }
            }
        }
    }
}

struct ScheduleEventRow: View {
    let event: CalendarEvent
    let index: Int
    
    var body: some View {
        HStack(alignment: .top, spacing: 15) {
            // Time indicator
            VStack(spacing: 4) {
                Text(formatTime(event.start))
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.blue)
                
                Rectangle()
                    .fill(Color.blue)
                    .frame(width: 2)
                    .frame(maxHeight: .infinity)
                
                Text(formatTime(event.end))
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.blue)
            }
            .frame(width: 50)
            
            // Event details
            VStack(alignment: .leading, spacing: 6) {
                Text(event.summary)
                    .font(.headline)
                    .foregroundColor(.primary)
                
                HStack(spacing: 4) {
                    Text(formatTime(event.start))
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("→")
                        .foregroundColor(.secondary)
                        .font(.caption)
                    Text(formatTime(event.end))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                if let alreadyInCalendar = event.already_in_calendar, alreadyInCalendar {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        Text("Already in calendar")
                            .font(.caption)
                            .foregroundColor(.green)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            
            Spacer()
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
    }
    
    private func formatTime(_ dateString: String) -> String {
        guard let date = parseDate(dateString) else { return "" }
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        formatter.dateStyle = .none
        return formatter.string(from: date)
    }
    
    private func parseDate(_ dateString: String) -> Date? {
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        if let date = isoFormatter.date(from: dateString) {
            return date
        }
        
        // Try without fractional seconds
        isoFormatter.formatOptions = [.withInternetDateTime]
        return isoFormatter.date(from: dateString)
    }
}

#Preview {
    ScheduleView(
        schedule: [
            CalendarEvent(summary: "Morning Meeting", start: "2025-01-15T09:00:00Z", end: "2025-01-15T10:00:00Z", already_in_calendar: false),
            CalendarEvent(summary: "Lunch Break", start: "2025-01-15T12:00:00Z", end: "2025-01-15T13:00:00Z", already_in_calendar: true),
            CalendarEvent(summary: "Project Review", start: "2025-01-15T14:00:00Z", end: "2025-01-15T15:30:00Z", already_in_calendar: false)
        ],
        scheduleId: "test-id",
        isPresented: .constant(true),
        onAdjust: {},
        onCommit: {}
    )
}
