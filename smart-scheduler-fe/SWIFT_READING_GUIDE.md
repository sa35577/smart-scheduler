# Swift Code Reading Guide for Beginners

This guide will help you understand the Swift code in this project, even if you've never worked with Swift before.

## Table of Contents
1. [Basic Swift Syntax](#basic-swift-syntax)
2. [Key Swift Concepts](#key-swift-concepts)
3. [Reading Your Code Files](#reading-your-code-files)
4. [Common Patterns](#common-patterns)

---

## Basic Swift Syntax

### Variables and Constants

```swift
// Variables (can change)
var name = "John"
var age = 25

// Constants (cannot change - preferred in Swift)
let pi = 3.14159
let clientId = "your-client-id"
```

**In your code:**
- `@State private var isAuthenticating = false` - A variable that can change
- `private let clientId: String = "..."` - A constant that never changes

### Type Annotations

Swift can infer types, but you can also specify them:

```swift
let name: String = "John"        // Explicitly a String
let age: Int = 25                // Explicitly an Int
let price: Double = 19.99         // Explicitly a Double
let isActive: Bool = true         // Explicitly a Bool
```

**In your code:**
- `private let clientId: String` - This is a String type
- `var isAuthenticated: Bool` - This is a Bool (true/false)

### Optionals (?)

Swift has a special type called "Optional" - it means "this value might not exist"

```swift
var name: String? = nil           // name might be nil (nothing)
var age: Int? = 25                // age might be nil or a number

// Unwrapping optionals safely
if let name = name {
    print(name)  // Only runs if name is not nil
}

// Or using guard (common pattern)
guard let name = name else { return }  // Exits if name is nil
print(name)  // name is now guaranteed to exist
```

**In your code:**
- `var errorMessage: String?` - Error message might not exist
- `var scheduleId: String?` - Schedule ID might not exist
- `if let scheduleId = scheduleId { ... }` - Only show button if scheduleId exists

### Functions

```swift
// Simple function
func greet(name: String) {
    print("Hello, \(name)")
}

// Function that returns a value
func add(a: Int, b: Int) -> Int {
    return a + b
}

// Async function (runs in background)
func fetchData() async throws -> String {
    // ... do async work
    return "data"
}
```

**In your code:**
- `func authenticate()` - A function that doesn't return anything
- `func getValidAccessToken() async throws -> String` - An async function that returns a String

---

## Key Swift Concepts

### 1. Classes and Structs

```swift
// Class (reference type - can be inherited)
class GoogleAuthManager {
    var isAuthenticated: Bool = false
    
    func authenticate() {
        // ...
    }
}

// Struct (value type - copied when passed around)
struct CalendarEvent {
    let summary: String
    let start: String
}
```

**In your code:**
- `class GoogleAuthManager` - A class that manages authentication
- `struct CalendarEvent` - A struct representing a calendar event

### 2. Properties

```swift
class MyClass {
    // Stored property
    var name: String = "Default"
    
    // Computed property (calculated on access)
    var fullName: String {
        return "Mr. \(name)"
    }
    
    // Private property (only accessible within this class)
    private let secret: String = "hidden"
}
```

**In your code:**
- `var isAuthenticated: Bool` - A computed property that checks if user is authenticated
- `private let clientId: String` - A private constant only this class can see

### 3. @State and @Observable

These are SwiftUI property wrappers that make UI reactive:

```swift
@State private var count = 0        // When this changes, UI updates
@Observable class MyClass {         // Changes to this class update UI
    var name = "John"
}
```

**In your code:**
- `@State private var isAuthenticating = false` - When this changes, the UI automatically updates
- `@Observable class GoogleAuthManager` - When properties in this class change, any UI using it updates

### 4. Async/Await

Swift's way of handling asynchronous operations (like network requests):

```swift
// Old way (callbacks) - confusing
fetchData { result in
    // Handle result
}

// New way (async/await) - cleaner
let result = try await fetchData()
// Use result immediately
```

**In your code:**
- `try await authManager.authenticate()` - Wait for authentication to complete
- `let response = try await apiService.generateSchedule(...)` - Wait for API call

### 5. Error Handling

```swift
// Function that can throw errors
func riskyOperation() throws -> String {
    if somethingBad {
        throw MyError.badThing
    }
    return "success"
}

// Calling it with error handling
do {
    let result = try riskyOperation()
    print("Success: \(result)")
} catch {
    print("Error: \(error)")
}
```

**In your code:**
- `func authenticate() async throws` - Can throw an error
- `try await authManager.authenticate()` - Must handle the error
- `do { ... } catch { ... }` - Catches and handles errors

### 6. Closures (Functions as Values)

```swift
// Closure syntax
let add = { (a: Int, b: Int) -> Int in
    return a + b
}

// Trailing closure (common pattern)
button.onTap {
    print("Button tapped")
}

// Closure with parameters
session.onComplete { url, error in
    if let error = error {
        print("Error: \(error)")
    }
}
```

**In your code:**
- `Button(action: authenticate)` - Passes function as closure
- `ASWebAuthenticationSession(...) { callbackURL, error in ... }` - Closure that handles callback

---

## Reading Your Code Files

### ContentView.swift - The Main UI

This is your main user interface file using SwiftUI.

```swift
struct ContentView: View {
    // Properties (state variables)
    @State private var isAuthenticating = false
    @State private var errorMessage: String?
    
    // The UI body
    var body: some View {
        // UI code here
    }
    
    // Functions (actions)
    func authenticate() {
        // What happens when user taps button
    }
}
```

**Key parts:**
1. **`struct ContentView: View`** - This is a SwiftUI view (like a React component)
2. **`var body: some View`** - This defines what the UI looks like
3. **`@State`** - Variables that, when changed, update the UI
4. **`if !authManager.isAuthenticated { ... }`** - Conditional UI (only shows if not authenticated)
5. **`Button(action: authenticate)`** - Button that calls the `authenticate()` function

**Flow:**
```
User taps button
    ↓
Button calls authenticate() function
    ↓
authenticate() calls authManager.authenticate()
    ↓
UI updates based on @State variables
```

### GoogleAuthManager.swift - Authentication Logic

This class handles all Google OAuth authentication.

```swift
@Observable
class GoogleAuthManager: NSObject {
    // Configuration (constants)
    private let clientId: String = "..."
    private let redirectURI: String = "..."
    
    // Properties
    var isAuthenticated: Bool {
        return accessToken != nil && !isTokenExpired
    }
    
    // Methods
    func authenticate() async throws {
        // OAuth flow here
    }
}
```

**Key parts:**
1. **`@Observable`** - Makes this class reactive (UI updates when it changes)
2. **`private let`** - Constants only this class can see
3. **`var isAuthenticated: Bool`** - Computed property (calculated when accessed)
4. **`func authenticate() async throws`** - Async function that can throw errors
5. **`guard let ... else { throw ... }`** - Early exit if something is wrong

**Flow:**
```
authenticate() called
    ↓
Generate PKCE parameters
    ↓
Build Google auth URL
    ↓
Open ASWebAuthenticationSession (popup)
    ↓
User authorizes
    ↓
Receive callback with code
    ↓
Exchange code for tokens
    ↓
Store tokens in Keychain
```

### APIService.swift - Backend Communication

This class handles all API calls to your backend.

```swift
@Observable
class APIService {
    private let baseURL: String
    private let authManager: GoogleAuthManager
    
    func generateSchedule(rant: String) async throws -> ScheduleResponse {
        let accessToken = try await authManager.getValidAccessToken()
        let request = ScheduleRequest(rant: rant, access_token: accessToken)
        return try await post("/schedule/generate", body: request)
    }
}
```

**Key parts:**
1. **`init(baseURL:authManager:)`** - Constructor (called when creating instance)
2. **`async throws -> ScheduleResponse`** - Returns a ScheduleResponse asynchronously
3. **`try await`** - Waits for async operation and handles errors
4. **`private func post`** - Private helper function (only used internally)

---

## Common Patterns

### 1. Optional Binding

```swift
// Pattern: if let (unwrap optional safely)
if let errorMessage = errorMessage {
    Text(errorMessage)  // Only shows if errorMessage exists
}

// Pattern: guard let (early exit)
guard let scheduleId = scheduleId else { return }
// scheduleId is now guaranteed to exist
```

### 2. Task for Async Work

```swift
Task {
    do {
        let result = try await someAsyncFunction()
        await MainActor.run {
            // Update UI on main thread
            self.isLoading = false
        }
    } catch {
        await MainActor.run {
            self.errorMessage = "Error occurred"
        }
    }
}
```

**Why `MainActor.run`?** - UI updates must happen on the main thread. `MainActor.run` ensures this.

### 3. Property Wrappers

```swift
@State private var count = 0           // UI state
@Observable class MyClass { }          // Observable class
private let constant = "value"         // Private constant
```

### 4. String Interpolation

```swift
let name = "John"
let message = "Hello, \(name)"  // "Hello, John"

// In your code:
print("✅ Found authorization code: \(code.prefix(20))...")
```

### 5. Array Operations

```swift
let scopes = ["scope1", "scope2"]
scopes.joined(separator: " ")  // "scope1 scope2"

let events: [CalendarEvent] = []
events.isEmpty  // true if empty
```

---

## How to Read Code Flow

### Example: User Taps "Sign in with Google"

1. **ContentView.swift** - Button is tapped
   ```swift
   Button(action: authenticate) { ... }
   ```

2. **ContentView.swift** - `authenticate()` function called
   ```swift
   func authenticate() {
       Task {
           try await authManager.authenticate()
       }
   }
   ```

3. **GoogleAuthManager.swift** - `authenticate()` starts OAuth flow
   ```swift
   func authenticate() async throws {
       // Build auth URL
       // Open popup
       // Wait for callback
   }
   ```

4. **GoogleAuthManager.swift** - Callback received, exchange code for token
   ```swift
   func handleOAuthCallback(code: String, codeVerifier: String) async throws {
       // Exchange code for tokens
       // Store in Keychain
   }
   ```

5. **ContentView.swift** - UI updates automatically (because `@Observable`)
   ```swift
   if !authManager.isAuthenticated { ... }  // This condition changes
   ```

---

## Quick Reference

| Swift Syntax | Meaning |
|-------------|---------|
| `let` | Constant (cannot change) |
| `var` | Variable (can change) |
| `?` | Optional (might be nil) |
| `!` | Force unwrap (dangerous - crashes if nil) |
| `if let` | Safely unwrap optional |
| `guard let` | Unwrap or exit early |
| `async` | Asynchronous function |
| `await` | Wait for async operation |
| `throws` | Function can throw error |
| `try` | Call function that can throw |
| `do/catch` | Handle errors |
| `private` | Only accessible in this file/class |
| `@State` | SwiftUI state variable |
| `@Observable` | Class that updates UI when changed |
| `func` | Function |
| `class` | Reference type |
| `struct` | Value type |
| `->` | Returns (function return type) |

---

## Tips for Reading Swift Code

1. **Start with the entry point** - Usually `ContentView` or the main view
2. **Follow the flow** - When a button is tapped, find the function it calls
3. **Look for `@State` and `@Observable`** - These control UI updates
4. **Understand optionals** - `?` means "might not exist", handle with `if let` or `guard let`
5. **Async/await is linear** - Read top to bottom, even with async code
6. **Error handling** - Look for `do/catch` blocks to see error paths
7. **Private vs public** - `private` means "only this class can see it"

---

## Next Steps

1. Try modifying `ContentView.swift` - Change button text or colors
2. Add print statements - See what values variables have
3. Read Swift documentation - [swift.org](https://swift.org/documentation/)
4. Practice with simple examples - Create a new Swift file and experiment

Good luck! 🚀

