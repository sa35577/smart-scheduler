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
    already_in_calendar: Optional[bool] = True

    def __str__(self):
        return f"{self.summary} from {self.start} to {self.end}. Already in calendar: {self.already_in_calendar}"
    
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
        base = f"Name: '{self.name}' Description: '{self.description}' Time Estimate: {self.time_estimate} minutes."
        if self.preferred_time_of_day:
            base += f" Ideally, I would like to do this task at {self.preferred_time_of_day}."
        return base
    
    # to do print(tasks)
    def __repr__(self):
        return self.__str__()
    
class Schedule(BaseModel):
    '''
    A schedule is a list of events.
    '''
    events: list[Event]

    def __str__(self):
        return f"Schedule: {self.events}"
    
    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        return iter(self.events)

    def __getitem__(self, index):
        return self.events[index]

    def __len__(self):
        return len(self.events)
    
    