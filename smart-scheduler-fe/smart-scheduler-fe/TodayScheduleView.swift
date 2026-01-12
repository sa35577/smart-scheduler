//
//  TodayScheduleView.swift
//  smart-scheduler-fe
//
//  Displays today's calendar events
//

import SwiftUI

struct TodayScheduleView: View {
    let events: [CalendarEvent]
    let isLoading: Bool
    @Binding var isPresented: Bool
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                // Header
                Text("Today's Schedule")
                    .font(.title2)
                    .fontWeight(.bold)
                    .padding(.top)
                
                // Events List
                if isLoading {
                    VStack(spacing: 15) {
                        ProgressView()
                        Text("Loading events...")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxHeight: .infinity)
                } else if events.isEmpty {
                    VStack(spacing: 15) {
                        Image(systemName: "calendar.badge.plus")
                            .font(.system(size: 50))
                            .foregroundColor(.secondary)
                        Text("No events scheduled for today")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        Text("Create a schedule to get started!")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxHeight: .infinity)
                } else {
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(Array(events.enumerated()), id: \.offset) { index, event in
                                TodayEventRow(event: event, index: index)
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle("Today")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        isPresented = false
                    }
                }
            }
        }
    }
}

struct TodayEventRow: View {
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
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
                
                Rectangle()
                    .fill(Color.blue)
                    .frame(width: 2)
                    .frame(maxHeight: .infinity)
                
                Text(formatTime(event.end))
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.blue)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
            .frame(width: 60, alignment: .trailing)
            
            // Event details
            VStack(alignment: .leading, spacing: 6) {
                Text(event.summary)
                    .font(.headline)
                    .foregroundColor(.primary)
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
        // Try ISO8601 format first
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        if let date = isoFormatter.date(from: dateString) {
            return date
        }
        
        // Try without fractional seconds
        isoFormatter.formatOptions = [.withInternetDateTime]
        if let date = isoFormatter.date(from: dateString) {
            return date
        }
        
        // Try with timezone
        isoFormatter.formatOptions = [.withInternetDateTime, .withTimeZone]
        if let date = isoFormatter.date(from: dateString) {
            return date
        }
        
        // Fallback: try DateFormatter with common formats
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        
        // Try ISO format with DateFormatter
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        if let date = formatter.date(from: dateString) {
            return date
        }
        
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZ"
        if let date = formatter.date(from: dateString) {
            return date
        }
        
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
        if let date = formatter.date(from: dateString) {
            return date
        }
        
        print("⚠️ Failed to parse date: \(dateString)")
        return nil
    }
}

#Preview {
    TodayScheduleView(
        events: [
            CalendarEvent(summary: "Team Standup", start: "2025-01-15T09:00:00Z", end: "2025-01-15T09:30:00Z", already_in_calendar: true, event_id: nil, original_start: nil, original_end: nil, is_modified: false),
            CalendarEvent(summary: "Lunch", start: "2025-01-15T12:00:00Z", end: "2025-01-15T13:00:00Z", already_in_calendar: true, event_id: nil, original_start: nil, original_end: nil, is_modified: false)
        ],
        isLoading: false,
        isPresented: .constant(true)
    )
}
