# Smart Scheduler App

The goal of this app is to be able to interact with the application, 
either through some voice assistant or some other means to create 
your itinerary for the day. 

## Roadmap:
### Basic functionality:
- [x] Get calendar API to be able to read events for the day
- [x] Get calendar API to be able to create an event for a specific time
- [x] Get the LLM to do a simple prompt
- [x] Integrate a flow to read events for the day -> put that in LLM context to generate some output
- [x] Put some sample tasks in and put that into the LLM context
- [ ] Get this flow to create tasks according to some JSON schema
- [ ] Insert events from this day into the calendar, if they're not already there

### Following:
- [ ] Build a UI to enter tasks (what type? app, web, desktop/mobile)
- [ ] Deploy & test
