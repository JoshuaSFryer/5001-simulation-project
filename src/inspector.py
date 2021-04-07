from enum import Enum, auto
import random

from buffer import Buffer
from component import ComponentType
from event import EndInspectionEvent
from itertools import cycle
from rng import generate_exp
from workstation import Workstation


class Inspector:
    """

    """

    def __init__(self, parent, id, lam, types: list, stations: list, out_routing):
        self.id = id

        self.parent = parent
        # Lambda of exponential distribution associated with this inspector
        # For inspectors, this is a dict mapping component types to lambdas
        self.lam = lam
        # Individual RNG stream for this inspector
        self.rng = random.Random()
        # Types of components this inspector handles
        self.input_types = types
        # Workstations this inspector can output to
        self.workstations = stations
        # Cyclic iterator of workstations (used in Round Robin policy)
        self.ws_cycle = cycle(self.workstations)
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
        # Pick an element at random from the types this inspector can uses
        # LBS: see above:  elf.input_types = types
        return random.choice(self.input_types)

    def generate_time(self, base_time, input_type):
        """
        Calculate a time for the next inspection event.
        Inspector 2 has a different distribution for each of its types, so
        the component type must be specified.
        """
        return base_time + generate_exp(self.lam[input_type], self.rng)

    def choose_output(self):
        """
        Choose which workstation to output this inspector's currently held 
        component to.
        Returns None if there is no eligible workstation (so this inspector is
        blocked).
        """
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
                    break

        elif self.routing == OutputPolicy.SHORTEST_QUEUE:
            # Check all the workstations this inspector can push to, and put the
            # component in the one with the shortest queue.

            # List of eligible workstations
            # LBS: declare candidates instantly, put station name in it.
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

        elif self.routing == OutputPolicy.ROUND_ROBIN:
            # Cycle through WS1, WS2, WS3.
            # If any workstation is blocked, DO NOT move on to trying another
            # station. Instead, return None and wait for the current one to
            # have an opening in its buffer.
            w = next(self.ws_cycle)
            if w.can_accept(self.component):
                chosen_workstation = w
            else:
                chosen_workstation = None

        return chosen_workstation

    def get_id(self):
        """
        Get inspector Id
        """
        return self.id

    def output_component(self):
        """
        Push the currently held component to a workstation chosen by this 
        inspector's output policy.
        """
        w = self.choose_output()

        # LBS ADD: Only if w != none that station can accept component & inspector can take new component
        if w == None:
            return False
        else:
            # Give the component to the workstation
            w.accept_component(self.component)
            # Grab a new component
            self.component = self.choose_input()
            return True

    def is_blocked(self):
        """
        Return True if this inspector is blocked.
        """
        return (self.choose_output() is None)


class OutputPolicy(Enum):
    NAIVE = auto()
    SHORTEST_QUEUE = auto()
    ROUND_ROBIN = auto()
