
class Event():
    def __init__(self, time):
        self.time = time

    # Custom comparison operators to allow sorting events based on their time
    # This makes it easy to use them in a PriorityQueue
    def __eq__(self, other):
        return self.time == other.time

    def __lt__(self, other):
        return self.time < other.time

    def __gt__(self, other):
        return self.time > other.time



class EndInspectionEvent(Event):
    def __init__(self, time, id):
        super().__init__(time)
        self.id = id



class EndAssemblyEvent(Event):
    def __init__(self, time, id):
        super().__init__(time)
        self.id = id


    
class EndSimulationEvent(Event):
    def __init__(self, time):
        super().__init__(time)
        self.id = 'END'