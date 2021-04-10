import random
from buffer import Buffer, BufferException
from component import ComponentType, ProductType
from event import EndAssemblyEvent
from rng import generate_exp


class Workstation:
    def __init__(self, parent, id, lam, inputs: list, output: ProductType):
        # ID string
        self.id = id
        # busy or idle state LBS ADD
        self.busy = False
        # Reference to system
        self.parent = parent
        # Lambda of exponential distribution associated with this inspector
        self.lam = lam
        # Individual RNG stream for this workstation
        self.rng = random.Random()

        # Type of product this station assembles
        self.output_type = output

        self.buffers = dict()
        self.ready_components = dict()  # LBS: not used
        for comp in inputs:
            self.buffers[comp] = Buffer(comp)

    def generate_time(self, base_time):
        """
        Calculate a time for the next assembly event.
        """
        return base_time + generate_exp(self.lam, self.rng)

    def can_accept(self, input: ComponentType):
        """
        Check to see if this station can accept a component passed to it.
        This requires a Buffer of the correct type, that is not full.
        """

        if input in self.buffers.keys():
            if not self.buffers[input].is_full():
                return True
        return False

    def get_buffer(self, input: ComponentType):
        """
        Get the buffer associated with the given component, or None.
        """
        if input in self.buffers.keys():
            return self.buffers[input]
        return None

    def enqueue_component(self, input: ComponentType):
        """
        Take a component provided by an inspector and put it in the appropriate
        buffer.
        """
        try:
            self.buffers[input].enqueue(input)
        except BufferException as e:
            raise (e)

    # used in inspector.output_component()
    def accept_component(self, input: ComponentType):
        """
        Recieve a component from an inspector. If this new component's arrival
        means that this workstation has the parts it needs to perform an
        assembly, notify the system of this.
        """
        self.enqueue_component(input)
        if self.all_components_ready():
            self.notify_ready()

    def notify_ready(self):
        """
        Notify the system that this workstation has all the parts it needs to
        begin assembly, generate the endassembly event
        """
        time = self.generate_time(self.parent.clock)
        self.parent.schedule_workstation(
            self, time)  # generate endassembly event
        self.busy = True

    def assemble(self):  # LBS: what function does assemble do, start to assemble, or assemble finished?
        """
        Take the required components from the buffers and return True if successful.
        If not, do nothing and return False.
        LBS: assembling takes time. here the function assemble() denotes the completion of assemble, not the start of assemble
        required components from the buffers should be taken when the EndAssemble event is identified.
        """
        self.busy = False

        if self.all_components_ready():
            self.notify_ready()

        return True

    def all_components_ready(self):
        """
        Return True if this workstation's buffers each have at least one of
        the components necessary for assembly, False otherwise.
        """
        for k in self.buffers.keys():
            if self.comp_ready(k) == False:
                return False
        return True

    def find_missing_components(self):
        """
        Determine which component types are missing, preventing the workstation
        from performing an assembly.
        """
        missing = list()
        types = self.buffers.keys()
        for t in types:
            if self.is_ready(t) == False:
                missing.append(t)

        return missing

    def comp_ready(self, component):
        """
        Return True if the buffer handling the given component type contains at
        least one item.
        """
        return not self.get_buffer(component).is_empty()
