import random

from buffer import Buffer
from component import ComponentType, ProductType
from fel import FutureEventList
from inspector import Inspector, OutputPolicy
from workstation import Workstation

rng_seed = None

class System():
    def __init__(self):
        self.clock = 0
        # Track number of products output in order to calculate throughput
        self.num_outputs = 0
        # Track time inspectors (either, or both) spend blocked
        self.blocked_time = 0

        # Seed RNG if desired
        if not rng_seed is None:
            random.seed(rng_seed)

        # Setup FEL
        self.event_list = FutureEventList()

        # Create workstations
        ws_1 = Workstation([ComponentType.C1], ProductType.P1, 1)
        ws_2 = Workstation([ComponentType.C1, ComponentType.C2], ProductType.P2, 2)
        ws_3 = Workstation([ComponentType.C1, ComponentType.C2], ProductType.P3, 3)

        # Create inspectors
        ins_1 = Inspector([ComponentType.C1], [ws_1, ws_2, ws_3], 
                            OutputPolicy.SHORTEST_QUEUE)

        ins_2 = Inspector([ComponentType.C1, ComponentType.C2], [ws_2, ws_3],
                          OutputPolicy.NAIVE)

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
    sys = System()
