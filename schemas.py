from pydantic import BaseModel
from typing import Optional

class Event(BaseModel):
    '''
    An event is a single item that is in a calendar,
    or a single item that I want to add to a calendar.
    '''
    summary: str
    start: str
    end: str
    location: Optional[str] = None
    description: Optional[str] = None

    def __str__(self):
        return f"{self.summary} from {self.start} to {self.end}"
    
    def __repr__(self):
        return self.__str__()
    
class Task(BaseModel):
    '''
    A task is a single item that I need to complete today.
    It has a name, a description, and an amount of time it will take,
    and an optional preference for what time of day it should be completed.
    '''
    name: str
    description: str
    time_estimate: int
    preferred_time_of_day: Optional[str] = None

    # to do print(task)
    def __str__(self):
        base = f"{self.name}: {self.description} that should take {self.time_estimate} minutes."
        if self.preferred_time_of_day:
            base += f" Ideally, I would like to do this task at {self.preferred_time_of_day}."
        return base
    
    # to do print(tasks)
    def __repr__(self):
        return self.__str__()