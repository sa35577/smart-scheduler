# import os
from dotenv import load_dotenv
from openai import OpenAI
from list_today import list_today_events
import logging

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


def interface():
    events = list_today_events()
    for event in events:
        print(event)

if __name__ == "__main__":
    interface()
