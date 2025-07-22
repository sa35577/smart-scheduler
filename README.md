# Smart Scheduler

Smart Scheduler is your AI-powered, conversational day planner—just tell it what you want to do, and it handles the rest, right down to syncing with your calendar.

## 🎥 Demo

Check out the demo video on [YouTube](https://youtu.be/5lxNRZoPjZU). It is based on the CLI version currently.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Google Calendar API credentials
- OpenAI API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sa35577/smart-scheduler.git
   cd smart-scheduler
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install openai python-dotenv google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```bash
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```
   Replace `your_openai_api_key_here` with your actual OpenAI API key.

5. **Set up Google Calendar API:**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Calendar API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials file and rename it to `credentials.json`
   - Place `credentials.json` in the project root directory

### Running the Application

1. **Activate your virtual environment (if not already active):**
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the main application:**
   ```bash
   python llm.py
   ```

3. **First-time setup:**
   - The first time you run the app, it will open a browser window for Google Calendar authorization
   - Follow the prompts to authorize the application
   - A `token.json` file will be created automatically

### Testing & Debugging

1. **Run the test suite:**
   ```bash
   python llm.py --test
   ```
   This will run comprehensive tests for all components including:
   - LLM functionality
   - Calendar operations
   - Schema parsing
   - Full pipeline testing

2. **View application logs:**
   ```bash
   python llm.py --logs
   ```
   Shows recent log entries for debugging and monitoring.

3. **Clear log files:**
   ```bash
   python llm.py --clear-logs
   ```
   Removes all log files to start fresh.

4. **Run individual test file:**
   ```bash
   python test_scheduler.py
   ```

### Project Structure

#### Core Application Files
- `llm.py` - Main application entry point with CLI interface
- `calendar_manager.py` - Handles all calendar operations (read/write/timezone)
- `prompt_generator.py` - Manages LLM interactions and prompt creation
- `scheduler_pipeline.py` - Orchestrates the entire scheduling workflow

#### Supporting Files
- `list_today.py` - Calendar event retrieval functionality
- `create_event.py` - Calendar event creation functionality
- `service_helper.py` - Google Calendar API service helper
- `schemas.py` - Data models for events and tasks
- `llm.log` - Application logs (created automatically)

## Roadmap:
### Basic functionality:
- [x] Get calendar API to be able to read events for the day
- [x] Get calendar API to be able to create an event for a specific time
- [x] Get the LLM to do a simple prompt
- [x] Integrate a flow to read events for the day -> put that in LLM context to generate some output
- [x] Put some sample tasks in and put that into the LLM context
- [x] Get this flow to create tasks according to the Event schema
- [x] Insert events from this day into the calendar
- [x] Only insert events that aren't in the calendar

### Following:
- [x] Get all access once to Google Calendar API
- [x] Develop a pipline for being able to revise events in the planning and post fix phase
- [ ] Build a UI to enter tasks (what type? app, web, desktop/mobile)
- [ ] Deploy & test
