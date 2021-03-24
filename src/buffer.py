from component import ComponentType

BUFFER_MAX_SIZE = 2

class Buffer:
    """
    Queue-like buffer that stores components.
    """
    def __init__(self, type:ComponentType):
        self.component_type = type
        self.contents = list()


    def enqueue(self, type:ComponentType):
        if not type == self.component_type:
            raise BufferException('Incorrect component type')

        if self.is_full():
            raise BufferException('Cannot push to a full buffer')

        self.contents.append(type)


    def dequeue(self):
        if self.is_empty():
            raise BufferException('Cannot pop from empty buffer')
        else:
            # Get the oldest element
            return self.contents.pop(0)


    def is_full(self):
        return len(self.contents) == BUFFER_MAX_SIZE
    

    def is_empty(self):
        return len(self.contents) == 0


    def get_length(self):
        return len(self.contents)


class BufferException(Exception):
    pass