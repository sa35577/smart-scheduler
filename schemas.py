class Event:
    def __init__(self, summary, start, end, location=None, description=None):
        self.summary = summary
        self.start = start
        self.end = end
        self.location = location
        self.description = description

    def __str__(self):
        return f"{self.summary} from {self.start} to {self.end}"