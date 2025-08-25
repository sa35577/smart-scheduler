import logging
from openai import OpenAI
from calendar_manager import CalendarManager
from prompt_generator import PromptGenerator
from scheduler_pipeline import SchedulerPipeline
from schemas import Task, Schedule


def test_llm_basic():
    """Test basic LLM functionality."""
    client = OpenAI()
    response = client.responses.create(
        model="gpt-4.1",
        input="Write a one-sentence bedtime story about a unicorn."
    )
    print(f"LLM Test Response: {response.output_text}")
    return response.output_text


def test_schema_parsing():
    """Test schema parsing with a predefined prompt."""
    client = OpenAI()
    prompt_generator = PromptGenerator(client)
    
    # Mock data for testing
    mock_events = [
        "test 2 from 12:30 PM to 01:30 PM", 
        "test from 06:30 PM to 07:30 PM"
    ]
    mock_tasks = [
        Task(name="Task 1", description="Description 1", time_estimate=10),
        Task(name="Task 2", description="Description 2", time_estimate=20),
        Task(name="Task 3", description="Description 3", time_estimate=30),
    ]
    
    try:
        schedule = prompt_generator.generate_schedule(mock_events, mock_tasks, "2025-07-07")
        print(f"Schema Test - Found {len(schedule)} scheduled events:")
        for event in schedule:
            print(f"  {event.summary}: {event.start} to {event.end}")
        return schedule
    except Exception as e:
        logging.error(f"Schema parsing test failed: {e}")
        raise


def test_calendar_operations():
    """Test calendar operations without creating real events."""
    try:
        calendar_manager = CalendarManager()
        
        # Test getting current date
        current_date = calendar_manager.get_current_date()
        print(f"Current date: {current_date}")
        
        # Test getting today's events
        events = calendar_manager.get_today_events()
        print(f"Found {len(events)} events today")
        
        return events
    except Exception as e:
        logging.error(f"Calendar operations test failed: {e}")
        raise


def test_pipeline_non_interactive():
    """Test the full pipeline in non-interactive mode."""
    try:
        # Initialize components
        calendar_manager = CalendarManager()
        client = OpenAI()
        prompt_generator = PromptGenerator(client)
        pipeline = SchedulerPipeline(calendar_manager, prompt_generator)
        
        # Test tasks
        tasks = [
            Task(name="Test Task 1", description="Test Description 1", time_estimate=15),
            Task(name="Test Task 2", description="Test Description 2", time_estimate=25),
        ]
        
        # Run pipeline without creating real events
        schedule = pipeline.run(tasks, interactive=False)
        print(f"Pipeline test completed with {len(schedule)} events")
        return schedule
        
    except Exception as e:
        logging.error(f"Pipeline test failed: {e}")
        raise


def run_all_tests():
    """Run all tests and report results."""
    test_results = {}
    
    tests = [
        ("LLM Basic", test_llm_basic),
        ("Calendar Operations", test_calendar_operations),
        ("Schema Parsing", test_schema_parsing),
        ("Pipeline Non-Interactive", test_pipeline_non_interactive),
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            print(f"Running {test_name} test...")
            print(f"{'='*50}")
            
            result = test_func()
            test_results[test_name] = ("PASS", result)
            print(f"✅ {test_name}: PASSED")
            
        except Exception as e:
            test_results[test_name] = ("FAIL", str(e))
            print(f"❌ {test_name}: FAILED - {e}")
            logging.error(f"Test {test_name} failed: {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    passed = sum(1 for status, _ in test_results.values() if status == "PASS")
    total = len(test_results)
    print(f"Passed: {passed}/{total}")
    
    return test_results


if __name__ == "__main__":
    run_all_tests() 