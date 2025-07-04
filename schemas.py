class Event:
    def __init__(self, summary, start, end, location=None, description=None):
        self.summary = summary
        self.start = start
        self.end = end
        self.location = location
        self.description = description

    def __str__(self):
        return f"{self.summary} from {self.start} to {self.end}"
    
    def __repr__(self):
        return self.__str__()
    
class Task:
    # a task is a single item that I need to complete today
    # it has a name, a description, and an amount of time it will take,
    # and an optional preference for what time of day it should be completed
    def __init__(self, name, description, time_estimate, preferred_time_of_day=None):
        self.name = name
        self.description = description
        self.time_estimate = time_estimate
        self.preferred_time_of_day = preferred_time_of_day

    # to do print(task)
    def __str__(self):
        base = f"{self.name}: {self.description} that should take {self.time_estimate} minutes."
        if self.preferred_time_of_day:
            base += f" Ideally, I would like to do this task at {self.preferred_time_of_day}."
        return base
    
    # to do print(tasks)
    def __repr__(self):
        return self.__str__()