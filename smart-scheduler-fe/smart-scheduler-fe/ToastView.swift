//
//  ToastView.swift
//  smart-scheduler-fe
//
//  Toast notification system for success and error messages
//

import SwiftUI

enum ToastType {
    case success
    case error
    
    var color: Color {
        switch self {
        case .success:
            return .green
        case .error:
            return .red
        }
    }
    
    var icon: String {
        switch self {
        case .success:
            return "checkmark.circle.fill"
        case .error:
            return "exclamationmark.circle.fill"
        }
    }
}

struct Toast: Identifiable {
    let id = UUID()
    let message: String
    let type: ToastType
}

struct ToastView: View {
    let toast: Toast
    @Binding var isPresented: Bool
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: toast.type.icon)
                .font(.system(size: 20, weight: .semibold))
                .foregroundColor(.white)
            
            Text(toast.message)
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(.white)
                .lineLimit(2)
            
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
        .background(toast.type.color)
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.2), radius: 8, x: 0, y: 4)
        .padding(.horizontal, 16)
        .padding(.top, 8)
        .transition(.move(edge: .top).combined(with: .opacity))
    }
}

struct ToastModifier: ViewModifier {
    @Binding var toast: Toast?
    
    func body(content: Content) -> some View {
        content
            .overlay(alignment: .topTrailing) {
                if let toast = toast {
                    ToastView(toast: toast, isPresented: Binding(
                        get: { toast != nil },
                        set: { if !$0 { self.toast = nil } }
                    ))
                    .zIndex(1000)
                    .animation(.spring(response: 0.3, dampingFraction: 0.7), value: toast != nil)
                    .onAppear {
                        // Auto-dismiss after 3 seconds
                        DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                            withAnimation {
                                self.toast = nil
                            }
                        }
                    }
                }
            }
    }
}

extension View {
    func toast(_ toast: Binding<Toast?>) -> some View {
        modifier(ToastModifier(toast: toast))
    }
}
