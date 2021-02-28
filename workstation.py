from buffer import Buffer, BufferException
from component import ComponentType, ProductType


class Workstation:
    def __init__(self, inputs:list[ComponentType], output:ProductType):
        # Type of product this station assembles
        self.output_type = output

        self.buffers = None
        for comp in inputs:
            self.buffers.append(Buffer(comp))

    
    def can_accept(self, input:ComponentType):
        """
        Check to see if this station can accept a component passed to it.
        This requires a Buffer of the correct type, that is not full.
        """

        for b in self.buffers:
            if b.component_type == input and not b.is_full():
                return True

    
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
        