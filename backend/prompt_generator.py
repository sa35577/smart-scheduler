import logging
from typing import List
from openai import OpenAI
from schemas import Event, Task, Schedule, Tasks


class PromptGenerator:
    """Handles prompt generation and LLM interactions for scheduling."""
    
    def __init__(self, client: OpenAI):
        self.client = client
        logging.info("PromptGenerator initialized")
    
    def generate_scheduling_prompt(self, events: List[Event], tasks: List[Task], current_date: str) -> str:
        """Generate the prompt for the LLM to create a schedule."""
        try:
            prompt = f"""
You are a helpful assistant that helps me manage my calendar.
Today is {current_date}.

I have the following {len(events)} events already in my calendar:
{events}

I have identified the following {len(tasks)} tasks from my rant that I want to schedule:
{tasks}

CRITICAL RULES:
1. DEDUPLICATION: Check if any "task" is already represented by an "existing event". For example, if there is a task "walk dog" and an existing event "Walk the dog", they are the same. DO NOT create a new event for it. Instead, just keep or move the existing event.
2. DO NOT move, delete, or modify existing events unless it's necessary to fit a task or the user explicitly asked.
3. Schedule new tasks AROUND existing events - find gaps in the schedule.
4. For each event in your response:
   - Set already_in_calendar=True if it's an existing event (keep the same summary if possible).
   - Set already_in_calendar=False if it's a completely new task.
   - If you move an existing event, set is_modified=True and include original_start/original_end.
   - ALWAYS preserve the event_id for existing events.

Return **only** a JSON object matching the schema.
            """
            logging.debug(f"Generated prompt for {len(events)} events and {len(tasks)} tasks")
            return prompt
        except Exception as e:
            logging.error(f"Failed to generate scheduling prompt: {e}")
            raise

    def generate_task_prompt(self, rant: str) -> str:
        """Generate tasks from a rant."""
        try:
            prompt = f"""
You are a helpful assistant that helps me manage my calendar.
I need to convert this rant into a list of tasks:
{rant}

Return **only** a JSON object matching the schema I provided.
"""
            logging.debug(f"Generated prompt for {rant}")
            return prompt
        except Exception as e:
            logging.error(f"Failed to generate tasks: {e}")
            raise

    def generate_tasks(self, rant: str) -> Tasks:
        """Generate tasks from a rant."""
        try:
            prompt = self.generate_task_prompt(rant)
            response = self.client.responses.parse(
                model="gpt-4.1",
                input=prompt,
                text_format=Tasks
            )
            tasks = response.output_parsed
            logging.info(f"Generated {len(tasks)} tasks")
            return tasks
        except Exception as e:
            logging.error(f"Failed to generate tasks: {e}")
            raise

    def generate_schedule(self, events: List[Event], tasks: List[Task], current_date: str) -> Schedule:
        """Generate a schedule using the LLM."""
        try:
            logging.info(f"Generating schedule with {len(events)} events and {len(tasks)} tasks")
            prompt = self.generate_scheduling_prompt(events, tasks, current_date)
            
            response = self.client.responses.parse(
                model="gpt-4.1",
                input=prompt,
                text_format=Schedule
            )
            
            schedule = response.output_parsed
            logging.info(f"Generated schedule with {len(schedule)} events")
            return schedule
        except Exception as e:
            logging.error(f"Failed to generate schedule: {e}")
            raise 

    def adjust_schedule_with_feedback(self, schedule: Schedule, feedback: str) -> Schedule:
        """Adjust the schedule using LLM based on user feedback."""
        try:
            # Format schedule for prompt with all relevant details
            schedule_str = "\n".join([
                f"- {e.summary}: {e.start} → {e.end} "
                f"(already_in_calendar={e.already_in_calendar}, "
                f"event_id={e.event_id if e.event_id else 'None'}, "
                f"is_modified={getattr(e, 'is_modified', False)})"
                for e in schedule
            ])
            
            prompt = f"""
Here is the current proposed schedule:
{schedule_str}

User Feedback:
"{feedback}"

CRITICAL RULES:
1. DEDUPLICATION: If the user feedback implies that a 'new' event (already_in_calendar=False) is actually a modification of an 'existing' event (already_in_calendar=True), MERGE THEM. Keep the existing event's ID and set is_modified=True.
2. DO NOT create duplicate events for the same activity.
3. If moving an existing event:
   - Keep already_in_calendar=True
   - Keep the original event_id
   - Set is_modified=True
   - Provide original_start/original_end
4. If the user says "move X to 1pm", and X exists as an 'existing' event, change its time. Do not add a new one.

Return only the updated schedule as JSON.
"""
            logging.info("=" * 80)
            logging.info("📤 SENDING PROMPT TO LLM:")
            logging.info(prompt)
            logging.info("=" * 80)
            
            response = self.client.responses.parse(
                model="gpt-4.1",
                input=prompt,
                text_format=Schedule
            )
            adjusted_schedule = response.output_parsed
            
            logging.info("=" * 80)
            logging.info(f"📥 LLM RETURNED {len(adjusted_schedule)} EVENTS:")
            for i, event in enumerate(adjusted_schedule, 1):
                logging.info(f"  [{i}] {event.summary}")
                logging.info(f"      start: {event.start}, end: {event.end}")
                logging.info(f"      already_in_calendar: {event.already_in_calendar}")
                logging.info(f"      event_id: {event.event_id}")
                logging.info(f"      is_modified: {getattr(event, 'is_modified', 'NOT SET')}")
                if hasattr(event, 'original_start') and event.original_start:
                    logging.info(f"      original_start: {event.original_start}")
                    logging.info(f"      original_end: {event.original_end}")
            logging.info("=" * 80)
            
            return adjusted_schedule
        except Exception as e:
            logging.error(f"Failed to adjust schedule with feedback: {e}")
            raise 