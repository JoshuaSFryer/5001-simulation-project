
from buffer import Buffer
from fel import FutureEventList
from inspector import Inspector
from workstation import Workstation


class System():
    def __init__(self):
        self.clock = 0
        # Track number of products output in order to calculate throughput
        self.num_outputs = 0
        # Track time inspectors (either, or both) spend blocked
        self.blocked_time = 0

        self.event_list = FutureEventList()

        # Create inspectors
        ...

        # Create workstations
        ...

        # Generate initial events
        ...

    
    def time_advance(self):
        """
        Find the next event in the event list and advance clock to its time.
        """
        ...

    
    def next_event(self):
        ...

    
    def event_inspection(self):
        """
        Event subroutine for an end-of-inspection event.
        """
        ...


    def event_assembly(self):
        """
        Event subroutine for an end-of-assembly event.
        """
        ...

    
    def event_end(self):
        """
        Event subroutine for an end-of-simulation event.
        """
        ...


    def generate_statistics(self):
        """
        Calculate important statistics and output them to file.
        """
        ...




if __name__ == '__main__':
    # Initialize a system
    ...