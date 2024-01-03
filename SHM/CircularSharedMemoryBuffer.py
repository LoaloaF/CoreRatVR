import atexit
import typing
from math import log
from multiprocessing import shared_memory
from utils import shm_buffer_errors

# max characters per line 80
# use return types everywhere if you use them once
# redundance with camera SHM creating. isolate 
# again create/ no create confusion


def _bytes_needed(n: int) -> int: #How many bytes are needed for address pointers
    return 1 if n == 0 else int(log(n, 256)) + 1

class CircularSharedMemoryBuffer:

    def __init__(self, name:str, create:bool = False, writeable:bool = False, item_size: int = 256, length: int = 1024 ):
            self.shm_name = name
            self.shm_item_size = item_size
            self.shm_buffer_length = length

            #How many bytes are needed to store current head of the queue
            self._write_pointer_byte_length = _bytes_needed(self.shm_item_size * self.shm_buffer_length) 
            self._shm_memory_size = (self.shm_item_size *self.shm_buffer_length) + self._write_pointer_byte_length
            
            self._writeable = writeable #We should only define one writer -> This can be different than creator
            self._create = create
            
            if create:
                try:
                    self._memory = shared_memory.SharedMemory(
                        name = self.shm_name, create=True, size=self._shm_memory_size
                    )
                except FileExistsError as e:
                    raise shm_buffer_errors.BufferAlreadyCreated(
                        "Buffer with that name already exists"
                    ) from e
            else:
                self._memory = shared_memory.SharedMemory(
                        name = self.shm_name, create = False
                    )
            
            self._internal_write_pointer = 0
            self._read_pointer = 0

            atexit.register(self.cleanup)

    def push(self, item: str) -> None:
        """
        Pushes an item to the buffer.

        Args:
            item (:obj:`str`): The item to put into the buffer.

        Returns:
            ``None``

        Raises:
            :obj:`~.errors.WriteOperationsForbidden`: The buffer cannot be written to by this instance.
        """
        if not self._writeable:
            raise shm_buffer_errors.WriteOperationsForbidden("Buffer is not writeable")
        
        byte_encoded_array = bytearray(self.shm_item_size)
        encoded_item = bytes(item, 'utf-8')
        if len(encoded_item) < self.shm_item_size :
            byte_encoded_array[0:len(encoded_item)] = encoded_item
        else:
            raise shm_buffer_errors.ItemLengthExceededError("Max Length available for single item is exceeded")
        
        self._next_write_pointer()
        temp_w_pointer = self._internal_write_pointer or (self.shm_item_size * self.shm_buffer_length)
        self._memory.buf[
            temp_w_pointer - self.shm_item_size : temp_w_pointer
        ] = byte_encoded_array

    def popitem(self) -> typing.Optional[str]:
        """
        Pops an item from the buffer.

        Returns:
            Optional[ :obj:`str` ]: Item removed from the buffer, or ``None`` if there is nothing to read.

        Raises:
            :obj:`~.errors.ReadOperationsForbidden`: The buffer cannot be read from by this instance.
        """
        if self._writeable:
            raise shm_buffer_errors.ReadOperationsForbidden("Buffer is not readable")

        if (read_addr := self._next_read_pointer()) is not None:
            temp_r_pointer = read_addr or (self.shm_item_size * self.shm_buffer_length)
            tmp_val = bytearray(self._memory.buf[temp_r_pointer - self.shm_item_size : temp_r_pointer])
            return tmp_val.decode('utf-8')
        return None
    
    @property
    def usage(self) -> int:
        """
        The number of elements currently in the buffer. This can be used to figure out how
        full or empty the buffer is at any time.

        Returns:
            :obj:`int`: Number of items in the buffer
        """
        if self._read_pointer > self._stored_write_pointer:
            return (
                self.shm_buffer_length
                - (self._read_pointer // self.shm_item_size)
                + (self._stored_write_pointer // self.shm_item_size)
            )
        return (self._stored_write_pointer - self._read_pointer) // self.shm_item_size
    
    def _next_write_pointer(self) -> None:
        self._internal_write_pointer += self.shm_item_size
        self._internal_write_pointer %= self.shm_buffer_length * self.shm_item_size

        self._stored_write_pointer = self._internal_write_pointer

    def _next_read_pointer(self) -> typing.Optional[int]:
        if self._read_pointer == self._stored_write_pointer:
            return None
        self._read_pointer += self.shm_item_size
        self._read_pointer %= self.shm_buffer_length * self.shm_item_size
        return self._read_pointer 
    
    @property #this return final chunk in our case this is 256byte long not a write pointer
    def _stored_write_pointer(self) -> int:
        return int.from_bytes(
            self._memory.buf[
                self._shm_memory_size
    
                 - self._write_pointer_byte_length : self._shm_memory_size
           ],
           byteorder="big",
       )
    
    @_stored_write_pointer.setter
    def _stored_write_pointer(self, n: int) -> None:
        self._memory.buf[
            self._shm_memory_size
            - self._write_pointer_byte_length : self._shm_memory_size
        ] = n.to_bytes(self._write_pointer_byte_length, byteorder="big")

    def __str__(self) -> str:
        if self._writeable:
            return f"{self.__class__.__name__}({self.shm_name})->buffer_length:{self.shm_buffer_length}"
        else:
            return f"{self.__class__.__name__}({self.shm_name})({(self.usage / self.shm_buffer_length) * 100:.2f}% full)"

    def cleanup(self) -> None:
        """
        Closes the connection to the :obj:`~multiprocessing.shared_memory.SharedMemory` block and
        unlinks it if this class was the writer to the buffer.

        This method is automatically called before the program exits.

        Returns:
            ``None``
        """
        self._memory.close()
        if self._create:
            self._memory.unlink()
    
    




#This is not shared memory but a normal circular buffer
class CircularQueue:

    def __init__(self, capacity):
        self.capacity = capacity
        self.queue = [None] * capacity
        self.tail = -1
        self.head = 0
        self.size = 0

    def enqueue(self, item):

        if self.size == self.capacity:
            print("Error : Queue is FUll")
        else:
            self.tail = (self.tail +1 ) % self.capacity #cyclic buffer
            self.queue[self.tail] = item
            self.size = self.size + 1 #increase size since new element is added

    def dequeue(self):

        if self.size == 0:
            print("Error: Queue is empty")
            return
        else:
            tmp = self.queue[self.head]
            self.head = (self.head + 1 ) % self.capacity
        
        self.size = self.size - 1
        return tmp
    
    def display(self):
        if self.size == 0:
            print("Queue is Empty")
        else:
            index = self.head
            for ii in range(self.size):
                print(self.queue[index])
                index = (index + 1) % self.capacity
    
    