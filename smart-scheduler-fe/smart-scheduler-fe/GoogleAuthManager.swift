//
//  GoogleAuthManager.swift
//  smart-scheduler-fe
//
//  Manages Google OAuth2 authentication and token storage
//

import Foundation
import Security
import Observation
import CryptoKit

@Observable
class GoogleAuthManager: NSObject {
    private let keychainService = "com.smart-scheduler.google-auth"
    private let accessTokenKey = "google_access_token"
    private let idTokenKey = "google_id_token"
    private let refreshTokenKey = "google_refresh_token"
    private let tokenExpiryKey = "google_token_expiry"
    
    // Retain the authentication session to prevent deallocation
    private var authSession: ASWebAuthenticationSession?
    
    // OAuth2 configuration - loaded from OAuthConfig
    // See OAuthConfig.swift to update these values
    private let clientId = OAuthConfig.clientId
    private let redirectURI = OAuthConfig.redirectURI
    private let callbackURLScheme = OAuthConfig.callbackURLScheme
    private let scopes = OAuthConfig.scopes
    
    // Track authentication state for SwiftUI observation
    // This property changes when tokens are saved/deleted, triggering UI updates
    // Accessing this in isAuthenticated ensures SwiftUI observes changes
    private var _authStateVersion: Int = 0
    
    var isAuthenticated: Bool {
        // Access _authStateVersion to ensure SwiftUI observes this computed property
        _ = _authStateVersion
        return accessToken != nil && !isTokenExpired
    }
    
    var accessToken: String? {
        return getAccessToken()
    }
    
    var idToken: String? {
        return getIdToken()
    }
    
    private var isTokenExpired: Bool {
        guard let expiryDate = getTokenExpiry() else { return true }
        return expiryDate < Date()
    }
    
    // MARK: - Public Methods
    
    /// Get a valid access token, refreshing if necessary
    func getValidAccessToken() async throws -> String {
        // Check if we have a valid token
        if let token = accessToken, !isTokenExpired {
            return token
        }
        
        // Try to refresh the token
        if let refreshToken = getRefreshToken() {
            return try await refreshAccessToken(refreshToken: refreshToken)
        }
        
        // No valid token and no refresh token - need to authenticate
        throw AuthError.notAuthenticated
    }
    
    /// Start the OAuth2 flow using ASWebAuthenticationSession with PKCE
    func authenticate() async throws {
        // Generate PKCE parameters for secure OAuth (iOS clients don't use client_secret)
        let codeVerifier = generateCodeVerifier()
        let codeChallenge = generateCodeChallenge(verifier: codeVerifier)
        
        // Build authorization URL with PKCE
        var components = URLComponents(string: "https://accounts.google.com/o/oauth2/v2/auth")!
        components.queryItems = [
            URLQueryItem(name: "client_id", value: clientId),
            URLQueryItem(name: "redirect_uri", value: redirectURI),
            URLQueryItem(name: "response_type", value: "code"),
            URLQueryItem(name: "include_granted_scopes", value: "true"),
            URLQueryItem(name: "scope", value: scopes.joined(separator: " ")),
            URLQueryItem(name: "access_type", value: "offline"), // Important: get refresh token
            URLQueryItem(name: "prompt", value: "consent"), // Force consent to get refresh token
            URLQueryItem(name: "code_challenge", value: codeChallenge),
            URLQueryItem(name: "code_challenge_method", value: "S256")
        ]
        
        guard let authURL = components.url else {
            throw AuthError.invalidURL
        }
        
        // Store code verifier for later use in token exchange
        let storedVerifier = codeVerifier
        
        // Use continuation to handle async callback
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            // Use ASWebAuthenticationSession for secure OAuth flow
            let session = ASWebAuthenticationSession(
                url: authURL,
                callbackURLScheme: self.callbackURLScheme
            ) { [weak self] callbackURL, error in
                if let error = error {
                    print("❌ ASWebAuthenticationSession error: \(error.localizedDescription)")
                    continuation.resume(throwing: error)
                    return
                }
                
                guard let callbackURL = callbackURL else {
                    print("❌ No callback URL received")
                    continuation.resume(throwing: AuthError.invalidCallbackURL)
                    return
                }
                
                print("✅ Received callback URL: \(callbackURL.absoluteString)")
                
                guard let components = URLComponents(url: callbackURL, resolvingAgainstBaseURL: true) else {
                    print("❌ Failed to parse callback URL")
                    continuation.resume(throwing: AuthError.invalidCallbackURL)
                    return
                }
                
                print("📋 Query items: \(components.queryItems?.map { "\($0.name)=\($0.value ?? "")" }.joined(separator: ", ") ?? "none")")
                
                guard let code = components.queryItems?.first(where: { $0.name == "code" })?.value else {
                    print("❌ No authorization code found in callback")
                    continuation.resume(throwing: AuthError.noAuthorizationCode)
                    return
                }
                
                print("✅ Found authorization code: \(code.prefix(20))...")
                
                // Exchange code for tokens
                Task { [weak self] in
                    guard let self = self else { 
                        print("❌ GoogleAuthManager deallocated")
                        continuation.resume(throwing: AuthError.tokenExchangeFailed("Manager deallocated"))
                        return
                    }
                    do {
                        try await self.handleOAuthCallback(code: code, codeVerifier: storedVerifier)
                        print("✅ Token exchange successful!")
                        continuation.resume()
                    } catch {
                        print("❌ Token exchange error: \(error)")
                        continuation.resume(throwing: error)
                    }
                }
            }
            
            session.presentationContextProvider = self
            // Retain the session to prevent deallocation
            self.authSession = session
            session.start()
        }
    }
    
    /// Handle OAuth callback with authorization code
    func handleOAuthCallback(code: String, codeVerifier: String) async throws {
        // Exchange authorization code for tokens using PKCE
        let tokenURL = URL(string: "https://oauth2.googleapis.com/token")!
        var request = URLRequest(url: tokenURL)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        
        var bodyComponents = URLComponents()
        bodyComponents.queryItems = [
            URLQueryItem(name: "code", value: code),
            URLQueryItem(name: "client_id", value: clientId),
            // iOS clients don't require client_secret - PKCE provides security
            URLQueryItem(name: "redirect_uri", value: redirectURI),
            URLQueryItem(name: "grant_type", value: "authorization_code"),
            URLQueryItem(name: "code_verifier", value: codeVerifier) // PKCE parameter
        ]
        request.httpBody = bodyComponents.query?.data(using: .utf8)
        
        print("🔄 Exchanging authorization code for token...")
        print("📤 Request URL: \(tokenURL.absoluteString)")
        print("📤 Redirect URI: \(redirectURI)")
        print("📤 Client ID: \(clientId.prefix(20))...")
        print("📤 Using PKCE (no client_secret needed for iOS clients)")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ Invalid HTTP response")
            throw AuthError.tokenExchangeFailed("Invalid HTTP response")
        }
        
        print("📥 Response status: \(httpResponse.statusCode)")
        
        guard httpResponse.statusCode == 200 else {
            let errorBody = String(data: data, encoding: .utf8) ?? "Unable to decode error"
            print("❌ Token exchange failed with status \(httpResponse.statusCode): \(errorBody)")
            throw AuthError.tokenExchangeFailed("Status \(httpResponse.statusCode): \(errorBody)")
        }
        
        let tokenResponse = try JSONDecoder().decode(TokenResponse.self, from: data)
        
        // Store tokens securely
        saveAccessToken(tokenResponse.access_token)
        if let idToken = tokenResponse.id_token {
            print("✅ Received id_token from Google (length: \(idToken.count))")
            saveIdToken(idToken)  // Store id_token for backend to decode
        } else {
            print("⚠️ No id_token in response - check that 'openid' scope is requested")
        }
        if let refreshToken = tokenResponse.refresh_token {
            saveRefreshToken(refreshToken)
        }
        if let expiresIn = tokenResponse.expires_in {
            let expiryDate = Date().addingTimeInterval(TimeInterval(expiresIn))
            saveTokenExpiry(expiryDate)
        }
        // Update auth state to trigger SwiftUI observation
        _authStateVersion += 1
    }
    
    /// Sign out and clear stored tokens
    func signOut() {
        deleteAccessToken()
        deleteIdToken()
        deleteRefreshToken()
        deleteTokenExpiry()
        // Update auth state to trigger SwiftUI observation
        _authStateVersion += 1
    }
    
    // MARK: - Private Methods
    
    private func refreshAccessToken(refreshToken: String) async throws -> String {
        let tokenURL = URL(string: "https://oauth2.googleapis.com/token")!
        var request = URLRequest(url: tokenURL)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        
        var bodyComponents = URLComponents()
        bodyComponents.queryItems = [
            URLQueryItem(name: "refresh_token", value: refreshToken),
            URLQueryItem(name: "client_id", value: clientId),
            URLQueryItem(name: "grant_type", value: "refresh_token")
        ]
        request.httpBody = bodyComponents.query?.data(using: .utf8)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            // Refresh failed - need to re-authenticate
            signOut()
            throw AuthError.tokenRefreshFailed
        }
        
        let tokenResponse = try JSONDecoder().decode(TokenResponse.self, from: data)
        
        // Update stored tokens
        saveAccessToken(tokenResponse.access_token)
        if let expiresIn = tokenResponse.expires_in {
            let expiryDate = Date().addingTimeInterval(TimeInterval(expiresIn))
            saveTokenExpiry(expiryDate)
        }
        
        return tokenResponse.access_token
    }
    
    // MARK: - Keychain Operations
    
    private func getAccessToken() -> String? {
        return getKeychainValue(key: accessTokenKey)
    }
    
    private func saveAccessToken(_ token: String) {
        saveKeychainValue(key: accessTokenKey, value: token)
    }
    
    private func deleteAccessToken() {
        deleteKeychainValue(key: accessTokenKey)
    }
    
    private func getIdToken() -> String? {
        return getKeychainValue(key: idTokenKey)
    }
    
    private func saveIdToken(_ token: String) {
        saveKeychainValue(key: idTokenKey, value: token)
    }
    
    private func deleteIdToken() {
        deleteKeychainValue(key: idTokenKey)
    }
    
    private func getRefreshToken() -> String? {
        return getKeychainValue(key: refreshTokenKey)
    }
    
    private func saveRefreshToken(_ token: String) {
        saveKeychainValue(key: refreshTokenKey, value: token)
    }
    
    private func deleteRefreshToken() {
        deleteKeychainValue(key: refreshTokenKey)
    }
    
    private func getTokenExpiry() -> Date? {
        guard let expiryString = getKeychainValue(key: tokenExpiryKey),
              let timeInterval = TimeInterval(expiryString) else {
            return nil
        }
        return Date(timeIntervalSince1970: timeInterval)
    }
    
    private func saveTokenExpiry(_ date: Date) {
        let timeInterval = String(date.timeIntervalSince1970)
        saveKeychainValue(key: tokenExpiryKey, value: timeInterval)
    }
    
    private func deleteTokenExpiry() {
        deleteKeychainValue(key: tokenExpiryKey)
    }
    
    // MARK: - PKCE Helpers
    
    /// Generate a random code verifier for PKCE
    private func generateCodeVerifier() -> String {
        let characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
        let length = 128
        return String((0..<length).map { _ in characters.randomElement()! })
    }
    
    /// Generate code challenge from verifier using SHA256
    private func generateCodeChallenge(verifier: String) -> String {
        let data = verifier.data(using: .utf8)!
        let hash = SHA256.hash(data: data)
        return Data(hash).base64URLEncodedString()
    }
    
    // MARK: - Keychain Helpers
    
    private func saveKeychainValue(key: String, value: String) {
        let data = value.data(using: .utf8)!
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
        ]
        
        // Delete existing item first
        SecItemDelete(query as CFDictionary)
        
        // Add new item
        SecItemAdd(query as CFDictionary, nil)
    }
    
    private func getKeychainValue(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return value
    }
    
    private func deleteKeychainValue(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key
        ]
        
        SecItemDelete(query as CFDictionary)
    }
}

// MARK: - Supporting Types

enum AuthError: Error, LocalizedError {
    case notAuthenticated
    case invalidURL
    case tokenExchangeFailed(String?)
    case tokenRefreshFailed
    case noAuthorizationCode
    case invalidCallbackURL
    
    var errorDescription: String? {
        switch self {
        case .notAuthenticated:
            return "Not authenticated. Please sign in."
        case .invalidURL:
            return "Invalid authorization URL."
        case .tokenExchangeFailed(let details):
            return "Failed to exchange authorization code for token. \(details ?? "")"
        case .tokenRefreshFailed:
            return "Failed to refresh access token."
        case .noAuthorizationCode:
            return "No authorization code received in callback."
        case .invalidCallbackURL:
            return "Invalid callback URL received."
        }
    }
}

struct TokenResponse: Codable {
    let access_token: String
    let refresh_token: String?
    let expires_in: Int?
    let token_type: String?
    let id_token: String?  // JWT containing user info (email, etc.)
}

#if os(macOS)
import AppKit
import AuthenticationServices
#endif

#if os(iOS)
import UIKit
import AuthenticationServices
#endif

// MARK: - Base64 URL Encoding Extension
extension Data {
    func base64URLEncodedString() -> String {
        return self.base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }
}

#if os(macOS) || os(iOS)
extension GoogleAuthManager: ASWebAuthenticationPresentationContextProviding {
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        #if os(macOS)
        return NSApplication.shared.windows.first { $0.isKeyWindow } ?? NSWindow()
        #elseif os(iOS)
        // Use the modern API for iOS 15+
        if let windowScene = UIApplication.shared.connectedScenes
            .first(where: { $0.activationState == .foregroundActive }) as? UIWindowScene,
           let window = windowScene.windows.first(where: { $0.isKeyWindow }) {
            return window
        }
        // Fallback: create a window with a window scene if available
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene {
            return UIWindow(windowScene: windowScene)
        }
        // Last resort fallback (deprecated but needed for older iOS versions)
        return UIApplication.shared.windows.first { $0.isKeyWindow } ?? UIWindow()
        #endif
    }
}
#endif

