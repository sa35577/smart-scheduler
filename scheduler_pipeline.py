import logging
from typing import List
from calendar_manager import CalendarManager
from prompt_generator import PromptGenerator
from schemas import Task, Schedule


class SchedulerPipeline:
    """Orchestrates the entire scheduling pipeline."""
    
    def __init__(self, calendar_manager: CalendarManager, prompt_generator: PromptGenerator):
        self.calendar_manager = calendar_manager
        self.prompt_generator = prompt_generator
        logging.info("SchedulerPipeline initialized")
    
    def run(self, tasks: List[Task], interactive: bool = True) -> Schedule:
        """Run the complete scheduling pipeline."""
        try:
            logging.info(f"Starting scheduler pipeline with {len(tasks)} tasks")
            
            # Step 1: Get existing events
            events = self._get_existing_events()
            
            # Step 2: Create test event if needed
            if len(events) == 0:
                events = self._create_test_event_if_needed()
            
            if interactive:
                input("Press Enter to continue...")
            
            # Step 3: Generate schedule
            schedule = self._generate_schedule(events, tasks)

            # Feedback loop
            while interactive:
                print("\nHere is your generated schedule:")
                for event in schedule:
                    print(f"Event: {event.summary}: {event.start} to {event.end}")
                    if event.description:
                        print(f"    Description: {event.description}")
                feedback = input("\nWould you like to make any changes? (Describe in plain English, or press Enter to accept): ")
                if not feedback.strip():
                    break
                schedule = self.prompt_generator.adjust_schedule_with_feedback(schedule, feedback)

            if interactive:
                input("Press Enter to add events to calendar...")
            
            # Step 4: Add events to calendar
            self._add_events_to_calendar(schedule)
            
            logging.info("Scheduler pipeline completed successfully")
            return schedule
            
        except Exception as e:
            logging.error(f"Scheduler pipeline failed: {e}")
            raise
    
    def _get_existing_events(self) -> List:
        """Get existing events from calendar."""
        events = self.calendar_manager.get_today_events()
        print(f"Found {len(events)} events today.")
        for event in events:
            print(event)
        return events
    
    def _create_test_event_if_needed(self) -> List:
        """Create a test event if no events exist."""
        print("No events found. Creating test event...")
        test_event = self.calendar_manager.create_test_event()
        print(f"Added test event: {test_event}")
        
        events = self.calendar_manager.get_today_events()
        print(f"Found {len(events)} events today.")
        for event in events:
            print(event)
        return events
    
    def _generate_schedule(self, events: List, tasks: List[Task]) -> Schedule:
        """Generate schedule using LLM."""
        current_date = self.calendar_manager.get_current_date()
        schedule = self.prompt_generator.generate_schedule(events, tasks, current_date)
        
        print(f"Found {len(schedule)} scheduled events:")
        for event in schedule:
            print(f"Event: {event.summary}: {event.start} to {event.end}")
            if event.description:
                print(f"    Description: {event.description}")
        
        return schedule
    
    def _add_events_to_calendar(self, schedule: Schedule) -> None:
        """Add generated events to calendar."""
        # TODO: Filter out events that are already in calendar
        self.calendar_manager.add_events_to_calendar(schedule) 