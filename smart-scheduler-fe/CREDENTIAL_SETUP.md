# Google Calendar Credential Setup Guide

This guide explains how to set up Google OAuth2 credentials for the Smart Scheduler iOS/macOS app.

## Overview

The app uses OAuth2 to authenticate with Google Calendar. The authentication flow works as follows:

1. **App handles OAuth** - The Swift app manages the OAuth flow using `ASWebAuthenticationSession`
2. **Tokens stored securely** - Access tokens and refresh tokens are stored in the iOS/macOS Keychain
3. **Tokens sent to backend** - The app sends the access token with each API request
4. **Backend uses tokens** - The backend uses the access token to make Google Calendar API calls

## Setup Steps

### 1. Create OAuth 2.0 Credentials in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client ID**

### 2. Configure OAuth Client (IMPORTANT: Use "Web application")

**⚠️ Important:** Since we're using `ASWebAuthenticationSession` with redirect URIs, you need to create a **"Web application"** OAuth client, NOT an iOS or macOS client.

1. Application type: **Web application**
2. Name: Smart Scheduler (or any name you prefer)
3. **Authorized redirect URIs**: Add the following:
   - `https://satarora.com/oauth/callback` (replace with your actual domain)
   
   **Why HTTPS domain?** Google requires HTTPS for sensitive scopes (Calendar access). You'll host an HTML page at this URL that redirects to your app's custom URL scheme. `ASWebAuthenticationSession` will intercept the custom scheme redirect.
   
4. Save the **Client ID** and **Client Secret** (you'll need both)
   - **Note**: Even though we use PKCE, Google's "Web application" OAuth clients still require the client_secret for token exchange
   - This is a limitation of using Web application clients for mobile apps
   - For better security, consider using a backend proxy for token exchange (see Security Considerations below)

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Fill in the required information:
   - User Type: External (or Internal if using Google Workspace)
   - App name: Smart Scheduler
   - User support email: Your email
   - Developer contact: Your email
3. Add scopes:
   - `https://www.googleapis.com/auth/calendar.events`
   - `https://www.googleapis.com/auth/calendar.readonly`
4. Add test users (if app is in testing mode)

### 4. Configure URL Scheme in Xcode

1. Open your Xcode project
2. Select your app target
3. Go to **Info** tab
4. Under **URL Types**, click **+** to add a new URL type:
   - **Identifier**: `com.smart-scheduler.oauth`
   - **URL Schemes**: `com.smart-scheduler`
   - **Role**: Editor

This is the custom URL scheme that `ASWebAuthenticationSession` will use to redirect back to your app after authentication. Note: This is different from the redirect URI in Google Cloud Console (which must be HTTP/HTTPS).

### 5. Update Client ID and Secret in Code

1. Open `GoogleAuthManager.swift`
2. Find these lines:
   ```swift
   private let clientId: String = "YOUR_CLIENT_ID_HERE"
   private let clientSecret: String = "YOUR_CLIENT_SECRET_HERE"
   ```
3. Replace both placeholders with your actual values from step 2

**Example:**
```swift
private let clientId: String = "123456789-abcdefghijklmnop.apps.googleusercontent.com"
private let clientSecret: String = "GOCSPX-abcdefghijklmnopqrstuvwxyz"
```

**⚠️ Security Note**: Storing the client_secret in your app is not ideal for security. Consider:
- Using a backend proxy to handle token exchange (more secure)
- Or accepting this limitation for development/testing

### 6. Set Up HTML Redirect Page

You need to host an HTML page at your redirect URI that redirects to your app's custom URL scheme.

1. **Create the HTML file** (`oauth/callback/index.html` or `oauth/callback.html`):
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>Redirecting...</title>
   </head>
   <body>
       <script>
           // Redirect to app's custom URL scheme, preserving query parameters
           window.location.replace("com.smart-scheduler://page" + window.location.search);
       </script>
       <p>Redirecting to app...</p>
   </body>
   </html>
   ```

2. **Host it** at your redirect URI (e.g., `https://satarora.com/oauth/callback`)
   - GitHub Pages, Netlify, Vercel, or your own server
   - Must be accessible via HTTPS

3. **Update the redirect URI** in `GoogleAuthManager.swift`:
   ```swift
   private let redirectURI: String = "https://satarora.com/oauth/callback"
   ```

### 7. Verify Redirect URI Configuration

**Important distinction:**
- **Google Cloud Console redirect URI**: `https://satarora.com/oauth/callback` (must be HTTPS for sensitive scopes)
- **HTML page redirects to**: `com.smart-scheduler://page?code=...` (custom scheme)
- **App callback URL scheme**: `com.smart-scheduler` (configured in Xcode)

Make sure:

1. ✅ The redirect URI `https://satarora.com/oauth/callback` is added in Google Cloud Console (step 2)
2. ✅ The HTML redirect page is hosted and accessible
3. ✅ The URL scheme `com.smart-scheduler` is configured in Xcode (step 4)
4. ✅ The `redirectURI` in `GoogleAuthManager.swift` matches your domain
5. ✅ The `callbackURLScheme` in `GoogleAuthManager.swift` is set to `com.smart-scheduler`

**How it works:** 
- Google redirects to `https://satarora.com/oauth/callback?code=...`
- Your HTML page immediately redirects to `com.smart-scheduler://page?code=...`
- `ASWebAuthenticationSession` intercepts the custom scheme and closes the popup
- Your app receives the callback and completes the OAuth flow

## How It Works

### Authentication Flow

```
User taps "Sign in with Google"
    ↓
App opens ASWebAuthenticationSession (popup)
    ↓
User authorizes in popup
    ↓
Google redirects to: https://satarora.com/oauth/callback?code=...
    ↓
HTML page redirects to: com.smart-scheduler://page?code=...
    ↓
ASWebAuthenticationSession intercepts custom scheme
    ↓
Popup closes, app receives callback URL
    ↓
App extracts authorization code
    ↓
App exchanges code for access_token + refresh_token
    ↓
Tokens stored in Keychain
    ↓
App can now make API calls with access_token
```

### Token Management

- **Access Token**: Short-lived (typically 1 hour), sent with each API request
- **Refresh Token**: Long-lived, used to get new access tokens when they expire
- **Automatic Refresh**: The app automatically refreshes expired access tokens using the refresh token
- **Secure Storage**: All tokens stored in iOS/macOS Keychain (encrypted)

### Backend Integration

The backend (`app.py`) already accepts `access_token` in request bodies:

```python
class ScheduleRequest(BaseModel):
    rant: str
    access_token: str  # ← App sends this
```

The backend uses the token to create Google Calendar service instances:

```python
calendar_manager = CalendarManager(access_token=req.access_token)
```

## Security Considerations

1. **Never commit credentials**: The `clientId` should ideally be stored in a secure configuration file or environment variable
2. **Keychain storage**: Tokens are automatically encrypted by iOS/macOS Keychain
3. **HTTPS only**: All API calls should use HTTPS in production
4. **Token expiration**: Access tokens expire after 1 hour; refresh tokens are used automatically

## Troubleshooting

### "Access blocked: Authorization Error - Error 401: invalid_client"
**This is the most common error!** It means:
- ❌ The `clientId` is still set to `"YOUR_CLIENT_ID_HERE"` (placeholder)
- ❌ You created an iOS/macOS OAuth client instead of a Web application client
- ❌ The Client ID doesn't exist or is from a different project

**Solution:**
1. Make sure you created a **"Web application"** OAuth client (not iOS/macOS)
2. Copy the Client ID from Google Cloud Console
3. Replace `"YOUR_CLIENT_ID_HERE"` in `GoogleAuthManager.swift` with your actual Client ID
4. Make sure the redirect URI `http://localhost:8080` is added in Google Cloud Console (not the custom URL scheme)

### "Invalid Redirect: You are using a sensitive scope. URI must use https:// as the scheme"
**This error occurs when trying to add a custom URL scheme in Google Cloud Console.**

**Solution:**
- Use an HTTPS domain you control (e.g., `https://satarora.com/oauth/callback`) as the redirect URI in Google Cloud Console
- Host an HTML page at that URL that redirects to your app's custom URL scheme
- Google requires HTTPS for sensitive scopes, but your HTML page bridges to the custom scheme
- `ASWebAuthenticationSession` will intercept the custom scheme redirect

### "Safari can't open the page because it couldn't connect to the server"
**This happens if you use localhost and there's no server running.**

**Solution:**
- Use an HTTPS domain instead of localhost
- Host the HTML redirect page on that domain
- This is the recommended approach for production and development

### "Invalid redirect URI" error
- Make sure the URL scheme in Xcode matches the `redirectURI` in code
- Verify the redirect URI is added in Google Cloud Console under "Authorized redirect URIs"
- The redirect URI must match exactly (including the `:/` part)

### "Token refresh failed" error
- The refresh token may have been revoked
- User needs to re-authenticate

### "Not authenticated" error
- Check that `clientId` is set correctly (not the placeholder)
- Verify OAuth consent screen is configured
- Ensure the redirect URI is properly configured

## Alternative: Using Google Sign-In SDK

For a more integrated experience, you could use the [Google Sign-In SDK](https://developers.google.com/identity/sign-in/ios) instead of manual OAuth2. This would require:

1. Adding the SDK via Swift Package Manager or CocoaPods
2. Different authentication flow
3. Similar token management approach

The current implementation uses manual OAuth2 for more control and fewer dependencies.

