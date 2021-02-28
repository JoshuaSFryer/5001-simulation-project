from enum import Enum, auto
import random

from component import ComponentType
from buffer import Buffer
from workstation import Workstation

class Inspector:
    """

    """
    def __init__(self, types:list[ComponentType], stations:list[Workstation],
                    out_routing:OutputPolicy):
        # Types of components this inspector handles
        self.input_types = types
        # Workstations this inspector can output to
        self.workstations = stations
        # How this inspector routes its outputs
        self.routing = out_routing
        # Currently-held component
        self.curr_component = None
    

    def pick_input(self):
        """
        Get the next component 
        """
        return random.choice(self.input_types)


    def pick_output(self):
        if self.output_routing == OutputPolicy.DEFAULT:
            # Check all the buffers this inspector can push to, and put the 
            # component in the first available one.
            for b in self.output_buffers:
                if self.curr_component in b.allowed_components:
                    # Push the component into the buffer
                    ...

        elif self.output_routing == OutputPolicy.SHORTEST_QUEUE:
            # Check all the buffers this inspector can push to, and put the
            # component in the one with the shortest queue.
            ...


class OutputPolicy(Enum):
    DEFAULT = auto()
    SHORTEST_QUEUE = auto()