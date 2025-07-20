import datetime
import logging
from typing import List
from openai import OpenAI
from schemas import Event, Task, Schedule


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
I have {len(events)} following events today:
{events}
Today is {current_date}.
I have a list of tasks that I need to complete today.
I have {len(tasks)} tasks to complete today:
{tasks}

Please build a schedule that lets me finish all my tasks around my existing events.
Return **only** a JSON object matching the schema I provided.
Also, for each event, set the already_in_calendar field to True if it is already in the calendar (as in, its already an event in the calendar), and False if it is not.
            """
            logging.debug(f"Generated prompt for {len(events)} events and {len(tasks)} tasks")
            return prompt
        except Exception as e:
            logging.error(f"Failed to generate scheduling prompt: {e}")
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