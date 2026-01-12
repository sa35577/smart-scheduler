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
    let onCancel: () -> Void
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
                    Button(action: {
                        onCancel()
                        isPresented = false
                    }) {
                        HStack(spacing: 4) {
                            Image(systemName: "xmark.circle.fill")
                            Text("Cancel")
                        }
                        .fontWeight(.semibold)
                        .foregroundColor(.red)
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
                HStack {
                    Text(event.summary)
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    // Status badge
                    Group {
                        switch event.eventStatus {
                        case .new:
                            Label("New", systemImage: "plus.circle.fill")
                                .font(.caption2)
                                .foregroundColor(.blue)
                        case .existing:
                            Label("Existing", systemImage: "checkmark.circle.fill")
                                .font(.caption2)
                                .foregroundColor(.green)
                        case .modified:
                            Label("Moved", systemImage: "arrow.right.circle.fill")
                                .font(.caption2)
                                .foregroundColor(.orange)
                        }
                    }
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(
                        event.eventStatus == .new ? Color.blue.opacity(0.1) :
                        event.eventStatus == .existing ? Color.green.opacity(0.1) :
                        Color.orange.opacity(0.1)
                    )
                    .cornerRadius(8)
                }
                
                // Show original time if event was moved
                if event.eventStatus == .modified,
                   let originalStart = event.original_start,
                   let originalEnd = event.original_end {
                    HStack {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.caption2)
                            .foregroundColor(.orange)
                        Text("Was: \(formatTime(originalStart)) → \(formatTime(originalEnd))")
                            .font(.caption)
                            .foregroundColor(.secondary)
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
            CalendarEvent(summary: "Morning Meeting", start: "2025-01-15T09:00:00Z", end: "2025-01-15T10:00:00Z", already_in_calendar: false, event_id: nil, original_start: nil, original_end: nil, is_modified: false),
            CalendarEvent(summary: "Lunch Break", start: "2025-01-15T12:00:00Z", end: "2025-01-15T13:00:00Z", already_in_calendar: true, event_id: "test-id-1", original_start: nil, original_end: nil, is_modified: false),
            CalendarEvent(summary: "Project Review", start: "2025-01-15T15:00:00Z", end: "2025-01-15T16:30:00Z", already_in_calendar: true, event_id: "test-id-2", original_start: "2025-01-15T14:00:00Z", original_end: "2025-01-15T15:00:00Z", is_modified: true)
        ],
        scheduleId: "test-id",
        isPresented: .constant(true),
        onAdjust: {},
        onCommit: {},
        onCancel: {}
    )
}
