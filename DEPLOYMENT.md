# Deployment Guide

Complete guide for deploying Smart Scheduler to production.

## Overview

Your app has three components to deploy:
1. **Backend API** (Python/FastAPI) - Currently `localhost:8000`
2. **iOS App** (Swift/SwiftUI) - Needs to point to deployed backend
3. **Google OAuth App** - Needs verification for production use

---

## Step 1: Deploy Backend API

### Option A: Deploy to Railway (Recommended - Easiest)

1. **Sign up at [Railway.app](https://railway.app)**
2. **Create a new project**
3. **Connect your GitHub repo** (or deploy from local)
4. **Configure the service:**
   - Root directory: `backend/`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - Environment variables:
     ```
     OPENAI_API_KEY=your_openai_key_here
     ```
5. **Get your backend URL:** Railway will give you a URL like `https://your-app.railway.app`
6. **Update CORS settings** in `backend/app.py`:
   ```python
   # Replace allow_origins=["*"] with:
   allow_origins=[
       "https://your-app.railway.app",
       "capacitor://localhost",  # For iOS app
       "ionic://localhost"        # Alternative iOS scheme
   ]
   ```

### Option B: Deploy to Render

1. **Sign up at [Render.com](https://render.com)**
2. **Create a new Web Service**
3. **Connect your GitHub repo**
4. **Settings:**
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - Environment: `Python 3`
   - Add environment variable: `OPENAI_API_KEY`
5. **Get your backend URL:** `https://your-app.onrender.com`

### Option C: Deploy to AWS/GCP/Azure

- **AWS:** Use Elastic Beanstalk or EC2
- **GCP:** Use Cloud Run or App Engine
- **Azure:** Use App Service

### After Deployment

1. **Test your backend:**
   ```bash
   curl https://your-backend-url.com/health
   ```
   Should return: `{"status": "really healthy"}`

2. **Note your backend URL** - you'll need it for the iOS app

---

## Step 2: Update iOS App for Production

### 2.1 Update Backend URL

1. **Open `smart-scheduler-fe/smart-scheduler-fe/APIService.swift`**
2. **Update the default baseURL:**
   ```swift
   init(baseURL: String = "https://your-backend-url.com", authManager: GoogleAuthManager) {
       self.baseURL = baseURL
       self.authManager = authManager
   }
   ```

3. **Or use environment-based configuration:**
   ```swift
   init(baseURL: String? = nil, authManager: GoogleAuthManager) {
       #if DEBUG
       self.baseURL = baseURL ?? "http://localhost:8000"
       #else
       self.baseURL = baseURL ?? "https://your-backend-url.com"
       #endif
       self.authManager = authManager
   }
   ```

### 2.2 Update Info.plist for Network Security

1. **Add App Transport Security exception** (if needed for HTTP during development):
   - Open `Info.plist`
   - Add:
   ```xml
   <key>NSAppTransportSecurity</key>
   <dict>
       <key>NSAllowsArbitraryLoads</key>
       <false/>
       <key>NSExceptionDomains</key>
       <dict>
           <key>your-backend-url.com</key>
           <dict>
               <key>NSExceptionAllowsInsecureHTTPLoads</key>
               <false/>
               <key>NSIncludesSubdomains</key>
               <true/>
           </dict>
       </dict>
   </dict>
   ```

---

## Step 3: Google OAuth App Verification

### 3.1 Prepare for Verification

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Navigate to:** APIs & Services > OAuth consent screen
3. **Complete all required fields:**
   - App name: "Smart Scheduler"
   - User support email: Your email
   - App logo: (Optional but recommended)
   - App domain: Your website (if you have one)
   - Developer contact: Your email
   - Scopes: Already configured (calendar.events, calendar.readonly)

### 3.2 Submit for Verification

1. **Click "PUBLISH APP"** (if in Testing mode)
2. **Or submit for verification** (if you want to publish to all users)
3. **Google will review your app** (can take 1-7 days)
4. **You may need to provide:**
   - Privacy Policy URL
   - Terms of Service URL
   - Video demonstration
   - Use case explanation

### 3.3 For Testing (Before Verification)

- **Add test users** in OAuth consent screen
- **Test users can use the app** without verification
- **Limit: 100 test users**

---

## Step 4: Prepare iOS App for App Store

### 4.1 Update App Configuration

1. **Open Xcode project**
2. **Select your target** → General tab
3. **Update:**
   - Display Name: "Smart Scheduler"
   - Bundle Identifier: `sat.smart-scheduler-fe` (or your preferred ID)
   - Version: `1.0.0`
   - Build: `1`

### 4.2 Configure App Icons and Launch Screen

1. **App Icon:**
   - Add app icon images to `Assets.xcassets/AppIcon.appiconset`
   - Sizes needed: 20x20, 29x29, 40x40, 60x60, 76x76, 83.5x83.5, 1024x1024

2. **Launch Screen:**
   - Already configured (UILaunchScreen_Generation = YES)

### 4.3 Update Privacy Permissions

1. **Info.plist already has:**
   - Microphone usage (for speech)
   - Speech recognition usage

2. **Add Privacy Policy** (required for App Store):
   - Create a privacy policy page
   - Host it somewhere (GitHub Pages, your website, etc.)
   - Add URL to App Store Connect

### 4.4 Build for App Store

1. **Select "Any iOS Device" or "Generic iOS Device"** as target
2. **Product → Archive**
3. **Wait for archive to complete**
4. **Click "Distribute App"**
5. **Choose "App Store Connect"**
6. **Follow the wizard**

---

## Step 5: App Store Connect Setup

### 5.1 Create App in App Store Connect

1. **Go to [App Store Connect](https://appstoreconnect.apple.com)**
2. **Click "+" → New App**
3. **Fill in:**
   - Platform: iOS
   - Name: Smart Scheduler
   - Primary Language: English
   - Bundle ID: `sat.smart-scheduler-fe`
   - SKU: `smart-scheduler-001` (unique identifier)

### 5.2 App Information

1. **App Privacy:**
   - Declare data collection:
     - Calendar data (read/write)
     - User account (email from Google)
   - Select "Data Not Linked to User" for calendar events

2. **Pricing:**
   - Set to Free (or paid)

3. **App Review Information:**
   - Contact info
   - Demo account (if needed)
   - Notes: "Uses Google Calendar API for scheduling"

### 5.3 Screenshots and Description

1. **Screenshots:**
   - Required sizes: 6.5", 6.7", 5.5" displays
   - Take screenshots on simulator or device

2. **Description:**
   - Write compelling app description
   - Keywords for App Store search
   - What's New section

### 5.4 Submit for Review

1. **Upload your build** from Xcode
2. **Complete all required information**
3. **Submit for review**
4. **Wait for Apple's review** (typically 1-3 days)

---

## Step 6: Environment Configuration Summary

### Backend Environment Variables

```bash
OPENAI_API_KEY=sk-...
# Add any other secrets here
```

### iOS App Configuration

**Development:**
- Backend URL: `http://localhost:8000`
- OAuth: Testing mode (test users only)

**Production:**
- Backend URL: `https://your-backend-url.com`
- OAuth: Published/Verified (all users)

### Checklist Before Production

- [ ] Backend deployed and accessible
- [ ] Backend URL updated in iOS app
- [ ] CORS configured correctly
- [ ] Google OAuth app verified or in testing mode
- [ ] App icons and launch screen configured
- [ ] Privacy policy created and linked
- [ ] App Store Connect app created
- [ ] Screenshots prepared
- [ ] App description written
- [ ] Tested on real device
- [ ] All features working end-to-end

---

## Step 7: Testing Production Build

### 7.1 TestFlight (Before App Store)

1. **Upload build to App Store Connect**
2. **Add internal testers** (up to 100)
3. **Add external testers** (up to 10,000)
4. **Test on real devices**

### 7.2 Production Testing Checklist

- [ ] Sign in with Google works
- [ ] Schedule generation works
- [ ] Schedule adjustment works
- [ ] Calendar commit works
- [ ] Today's schedule view works
- [ ] Sign out works
- [ ] Error handling works
- [ ] Network errors handled gracefully

---

## Troubleshooting

### Backend Issues

**CORS errors:**
- Update `allow_origins` in `backend/app.py` with your iOS app's URL schemes

**Environment variables:**
- Make sure `OPENAI_API_KEY` is set in your hosting platform

### iOS App Issues

**Network errors:**
- Check backend URL is correct
- Verify backend is accessible
- Check App Transport Security settings

**OAuth errors:**
- Verify OAuth client is configured correctly
- Check Bundle ID matches Google Cloud Console
- Ensure test users are added (if in testing mode)

### App Store Rejection

**Common reasons:**
- Missing privacy policy
- Incomplete app information
- App crashes during review
- Missing demo account (if login required)

**Solutions:**
- Add comprehensive privacy policy
- Provide demo account credentials
- Test thoroughly before submission
- Include detailed review notes

---

## Quick Reference

### Backend Deployment URLs
- **Railway:** https://railway.app
- **Render:** https://render.com
- **Heroku:** https://heroku.com (deprecated but still works)

### Important Links
- **Google Cloud Console:** https://console.cloud.google.com
- **App Store Connect:** https://appstoreconnect.apple.com
- **Apple Developer:** https://developer.apple.com

### Support
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **SwiftUI Docs:** https://developer.apple.com/xcode/swiftui/
- **Google OAuth:** https://developers.google.com/identity/protocols/oauth2

---

## Next Steps

1. **Start with backend deployment** (Railway is easiest)
2. **Update iOS app with production backend URL**
3. **Test thoroughly on TestFlight**
4. **Submit to App Store when ready**

Good luck! 🚀
