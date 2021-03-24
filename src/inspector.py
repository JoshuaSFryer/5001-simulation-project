from enum import Enum, auto
import random

from buffer import Buffer
from component import ComponentType
from event import EndInspectionEvent
from rng import generate_exp
from workstation import Workstation

class Inspector:
    """

    """
    def __init__(self, parent, id, lam, types:list, stations:list, out_routing):
        self.id = id

        self.parent = parent
        # Lambda of exponential distribution associated with this inspector
        # For inspectors, this is a dict mapping component types to lambdas
        self.lam = lam
        # Types of components this inspector handles
        self.input_types = types
        # Workstations this inspector can output to
        self.workstations = stations
        # How this inspector routes its outputs
        self.routing = out_routing
        # Currently-held component
        self.component = self.choose_input()
        
        self.last_event_time = 0
        self.time_blocked = 0
    

    def choose_input(self):
        """
        Get the next component 
        """
        return random.choice(self.input_types)

    
    def generate_time(self, base_time, input_type):
        return base_time + generate_exp(self.lam[input_type])


    def choose_output(self):
        chosen_workstation = None
        if self.routing == OutputPolicy.NAIVE:
            # Check all the workstations this inspector can push to, and put the 
            # component in the first (only) available one.

            # N.B. in the current system configuration, Inspector 2 only outputs
            # C2 to WS2 and C3 to WS3, so this works. This would cause 
            # unevenly distributed outputs if another buffer of either 
            # component type was introduced.
            for w in self.workstations:
                if w.can_accept(self.component):
                    chosen_workstation = w

        elif self.routing == OutputPolicy.SHORTEST_QUEUE:
            # Check all the workstations this inspector can push to, and put the
            # component in the one with the shortest queue.

            # List of eligible workstations
            candidates = list()
            for w in self.workstations:
                buf = w.get_buffer(self.component)
                if buf is not None:
                    candidates.append(w)
            
            # Find shortest queue among candidates
            # Sort list from shortest to longest buffer fullness
            candidates.sort(key=lambda w: w.get_buffer(self.component).get_length())


            # Check for ties
            # First element is the shortest length (because the list is sorted).
            # Compare it to the next shortest length.
            # If tied for 1st and 2nd, check also for 3rd, and so on...
            tied_stations = list()
            shortest_value = candidates[0].get_buffer(self.component).get_length()
            tied_stations.append(candidates[0])

            for w in candidates[1:]:
                # Stop checking, there are no more ties
                if not w.get_buffer(self.component).get_length() == shortest_value:
                    break
                tied_stations.append(w)

            # If list length is 1 there were no ties, it only contains the 
            # first station
            if len(tied_stations) == 1:
                chosen_workstation = tied_stations[0]
            else:
                # If there's a tie, get the highest-priority station
                tied_stations.sort(key=lambda w: w.id)
                chosen_workstation = tied_stations[0]

            if not chosen_workstation.can_accept(self.component):
                chosen_workstation = None

        return chosen_workstation


    def output_component(self):
        w = self.choose_output()
        # Give the component to the workstation
        if w is not None:
            w.accept_component(self.component)
            # Grab a new component
            self.component = self.choose_input()


    def is_blocked(self):
        return (self.choose_output() is None)
        

class OutputPolicy(Enum):
    NAIVE = auto()
    SHORTEST_QUEUE = auto()