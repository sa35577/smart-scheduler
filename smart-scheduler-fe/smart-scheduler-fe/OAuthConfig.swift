//
//  OAuthConfig.swift
//  smart-scheduler-fe
//
//  OAuth2 configuration for Google Calendar authentication
//

import Foundation

struct OAuthConfig {
    // Google OAuth2 Client Configuration
    // Get these values from Google Cloud Console > APIs & Services > Credentials > Your iOS OAuth Client
    
    static let clientId = "167925471103-qpepk4psv6m38i6tnbctkum3rjmn58eo.apps.googleusercontent.com"
    
    // Google's auto-generated iOS URL scheme (from Google Cloud Console > Additional information > iOS URL scheme)
    // Format: com.googleusercontent.apps.{CLIENT_ID_PART}
    static let iosURLScheme = "com.googleusercontent.apps.167925471103-qpepk4psv6m38i6tnbctkum3rjmn58eo"
    
    // Redirect URI for OAuth flow (uses the iOS URL scheme)
    static var redirectURI: String {
        return "\(iosURLScheme):/oauth/callback"
    }
    
    // Callback URL scheme for ASWebAuthenticationSession (must match Xcode URL Types)
    static var callbackURLScheme: String {
        return iosURLScheme
    }
    
    // OAuth scopes
    static let scopes = [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.readonly",
        "openid",  // Required to get id_token (JWT) with user email
        "https://www.googleapis.com/auth/userinfo.email"  // Explicitly request email scope
    ]
}
