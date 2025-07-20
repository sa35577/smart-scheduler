import logging
import pdb
from dotenv import load_dotenv
from openai import OpenAI

from calendar_manager import CalendarManager
from prompt_generator import PromptGenerator
from scheduler_pipeline import SchedulerPipeline
from schemas import Task
from logging_config import setup_logging

# Load environment variables from .env file
load_dotenv()

# Setup logging
setup_logging()

client = OpenAI()

def main():
    """Main entry point for the scheduling application."""
    try:
        # Initialize components
        calendar_manager = CalendarManager()
        prompt_generator = PromptGenerator(client)
        scheduler_pipeline = SchedulerPipeline(calendar_manager, prompt_generator)
        
        # Define tasks
        tasks = [
            Task(name="Task 1", description="Description 1", time_estimate=10),
            Task(name="Task 2", description="Description 2", time_estimate=20),
            Task(name="Task 3", description="Description 3", time_estimate=30),
        ]
        
        # Run the pipeline
        schedule = scheduler_pipeline.run(tasks)
        return schedule
        
    except Exception as e:
        logging.error(f"Main application failed: {e}")
        raise


def run_tests():
    """Run the test suite."""
    from test_scheduler import run_all_tests
    return run_all_tests()


if __name__ == "__main__":
    import sys
    from logging_config import get_log_summary, clear_logs
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            print("Running test suite...")
            run_tests()
        elif sys.argv[1] == "--logs":
            get_log_summary()
        elif sys.argv[1] == "--clear-logs":
            clear_logs()
        else:
            print("Usage: python llm.py [--test|--logs|--clear-logs]")
    else:
        main()
