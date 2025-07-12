import pdb
import datetime
import logging
import json

from dotenv import load_dotenv
from openai import OpenAI

from list_today import list_today_events
from schemas import Event, Task, Schedule

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
Today is {datetime.datetime.now():%Y-%m-%d}.
I have a list of tasks that I need to complete today.
I have {len(tasks)} tasks to complete today:
{tasks}

Please build a schedule that lets me finish all my tasks around my existing events.
Return **only** a JSON object matching the schema I provided.
    """
    return prompt

def interface(tasks: list[Task]):
    events = list_today_events()
    print(f"Found {len(events)} events today.")
    for event in events:
        print(event)

    input("Press Enter to continue...")

    prompt = generate_prompt(events, tasks)
    print(prompt)

    input("Press Enter to continue prompting...")

    response = client.responses.parse(
        model="gpt-4.1",
        input=prompt,
        text_format=Schedule
    )
    
    schedule = response.output_parsed
    print(f"Found {len(schedule)} scheduled events:")
    for event in schedule:
        print(f"Event: {event.summary}: {event.start} to {event.end}")
        if event.description:
            print(f"    Description: {event.description}")

    print("Press enter to add events to calendar...")
    
    return schedule


def test_schema():
    prompt = """
You are a helpful assistant that helps me manage my calendar.
I have 2 following events today:
[test 2 from 12:30 PM to 01:30 PM, test from 06:30 PM to 07:30 PM]
Today is 2025-07-07.
I have a list of tasks that I need to complete today.
I have 3 tasks to complete today:
[Name: 'Task 1' Description: 'Description 1' Time Estimate: 10 minutes., Name: 'Task 2' Description: 'Description 2' Time Estimate: 20 minutes., Name: 'Task 3' Description: 'Description 3' Time Estimate: 30 minutes.]

Please build a schedule that lets me finish all my tasks around my existing events.
Return **only** a JSON object matching the schema I provided.
"""
    response = client.responses.parse(
        model="gpt-4.1",
        input=prompt,
        text_format=Schedule
    )
    
    schedule = response.output_parsed
    print(f"Found {len(schedule)} scheduled events:")
    for event in schedule:
        print(f"HI  {event.summary}: {event.start} to {event.end}")
        if event.description:
            print(f"    Description: {event.description}")
    
    return schedule


if __name__ == "__main__":
    tasks = [
        Task(name="Task 1", description="Description 1", time_estimate=10),
        Task(name="Task 2", description="Description 2", time_estimate=20),
        Task(name="Task 3", description="Description 3", time_estimate=30),
    ]
    interface(tasks)
    # test_schema()
