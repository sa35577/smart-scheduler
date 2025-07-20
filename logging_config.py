import logging
import os
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_file: str = "llm.log"):
    """Setup logging configuration for the application."""
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            # File handler only - no console output
            logging.FileHandler(f"logs/{log_file}")
        ]
    )
    
    # Set specific loggers
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logging.info(f"Logging configured with level: {log_level}")


def get_log_summary():
    """Get a summary of recent log entries."""
    try:
        with open("logs/llm.log", "r") as f:
            lines = f.readlines()
        
        # Get last 20 lines
        recent_lines = lines[-20:] if len(lines) > 20 else lines
        
        print("Recent Log Entries:")
        print("=" * 50)
        for line in recent_lines:
            print(line.strip())
            
    except FileNotFoundError:
        print("No log file found.")
    except Exception as e:
        print(f"Error reading log file: {e}")


def clear_logs():
    """Clear all log files."""
    try:
        if os.path.exists("logs/llm.log"):
            os.remove("logs/llm.log")
            print("Logs cleared.")
        else:
            print("No log file to clear.")
    except Exception as e:
        print(f"Error clearing logs: {e}") 