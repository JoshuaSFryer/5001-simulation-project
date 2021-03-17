from buffer import Buffer, BufferException
from component import ComponentType, ProductType


class Workstation:
    def __init__(self, inputs:list, output:ProductType, 
                priority:int):
        # Type of product this station assembles
        self.output_type = output

        self.buffers = dict()
        for comp in inputs:
            self.buffers[comp] = Buffer(comp)

        # This station's priority in the case of a tie
        self.priority = priority

    
    def can_accept(self, input:ComponentType):
        """
        Check to see if this station can accept a component passed to it.
        This requires a Buffer of the correct type, that is not full.
        """

        if input in self.buffers:
            if not self.buffers[input].is_full():
                return True
        return False
        

    def get_buffer(self, input:ComponentType):
        """
        Get the buffer associated with the given component, or None.
        """
        if input in self.buffers:
            return self.buffers[input]
        return None

    
    def accept_component(self, input:ComponentType):
        """
        Take a component provided by an inspector and put it in the appropriate
        buffer.
        """
        try:
            self.buffers[input].enqueue(input)
        except BufferException as e:
            print(e)

    
    def get_components(self):
        """
        Pull the components this Workstation requires to assemble from its
        buffers.
        """
        ...
    

    def assemble(self):
        """
        Take needed components from buffers and output a product.
        """
        ...
        