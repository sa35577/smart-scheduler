# import os
from dotenv import load_dotenv
from openai import OpenAI
from list_today import list_today_events
import logging
from schemas import Event, Task
import datetime

logging.basicConfig(
    filename='llm.log',
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load environment variables from .env file
load_dotenv()

client = OpenAI()

def test_llm():
    response = client.responses.create(
        model="gpt-4.1",
        input="Write a one-sentence bedtime story about a unicorn."
    )

    print(response.output_text)

def generate_prompt(events: list[Event], tasks: list[Task]) -> str:
    prompt = f"""
    You are a helpful assistant that helps me manage my calendar.
    I have {len(events)} following events today:
    {events}
    Today is {datetime.datetime.now().strftime("%Y-%m-%d")}.
    I have a list of tasks that I need to complete today.
    I have {len(tasks)} tasks to complete today:
    {tasks}

    I need to schedule my tasks around my events.
    I need to complete all of my tasks.
    Help me build a schedule that will allow me to complete all of my tasks.
    Return the schedule in a JSON format.
    The schedule should be a list of events.
    Each event should have a start time, an end time, and a summary.
    The start time and end time should be in the format of "HH:MM".
    The schedule should be sorted by the start time.
    """
    return prompt

def interface(tasks: list[Task]):
    events = list_today_events()
    # print(f"Found {len(events)} events today.")
    # for event in events:
    #     print(event)

    prompt = generate_prompt(events, tasks)
    print(prompt)

    input("Press Enter to continue prompting...")

    response = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )
    print(response.output_text)

if __name__ == "__main__":
    tasks = [
        Task("Task 1", "Description 1", 10),
        Task("Task 2", "Description 2", 20),
        Task("Task 3", "Description 3", 30),
    ]
    interface(tasks)
