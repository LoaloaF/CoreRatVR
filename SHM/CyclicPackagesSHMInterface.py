import numpy as np
import struct
import typing

from CustomLogger import CustomLogger as Logger

from shm_interface_utils import load_shm_structure_JSON
from shm_interface_utils import access_shm
from shm_interface_utils import extract_packet_data
import  shm_buffer_errors

class CyclicPackagesSHMInterface:
    def __init__(self, shm_structure_JSON_fname):
        self.L = Logger()
        self.L.logger.debug(f"SHM interface created with json {shm_structure_JSON_fname}")
        shm_structure = load_shm_structure_JSON(shm_structure_JSON_fname)

        self._shm_name = shm_structure["shm_name"] #old: shm_name
        self._total_nbytes = shm_structure["total_nbytes"] # old: _shm_memoery_size

        self._shm_packages_nbytes = shm_structure["fields"]["shm_packages_nbytes"]  # old: didn't exist
        self._write_pntr_nbytes = shm_structure["fields"]["write_pntr_nbytes"] # old: _write_pointer_byte_lengthh
        self._npackages = shm_structure["metadata"]["npackages"]    # old: shm_buffer_lengthh
        self._package_nbytes = shm_structure["metadata"]["package_nbytes"]  # old: item_sizee

        self._memory = access_shm(self._shm_name)
        
        self._internal_write_pointer = 0
        self._read_pointer = 0

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
        # if not self._writeable:
        #     raise shm_buffer_errors.WriteOperationsForbidden("Buffer is not writeable")
        
        byte_encoded_array = bytearray(self._package_nbytes)
        encoded_item = bytes(item, 'utf-8')
        if len(encoded_item) < self._package_nbytes :
            byte_encoded_array[0:len(encoded_item)] = encoded_item
        else:
            raise shm_buffer_errors.ItemLengthExceededError("Max Length available for single item is exceeded")
        
        self._next_write_pointer()
        temp_w_pointer = self._internal_write_pointer or (self._package_nbytes * self._npackages)
        self._memory.buf[
            temp_w_pointer - self._package_nbytes : temp_w_pointer
        ] = byte_encoded_array

    def popitem(self) -> typing.Optional[str]:
        """
        Pops an item from the buffer.

        Returns:
            Optional[ :obj:`str` ]: Item removed from the buffer, or ``None`` if there is nothing to read.

        Raises:
            :obj:`~.errors.ReadOperationsForbidden`: The buffer cannot be read from by this instance.
        """
        # if self._writeable:
        #     raise shm_buffer_errors.ReadOperationsForbidden("Buffer is not readable")

        if (read_addr := self._next_read_pointer()) is not None:
            temp_r_pointer = read_addr or (self._package_nbytes * self._npackages)
            tmp_val = bytearray(self._memory.buf[temp_r_pointer - self._package_nbytes : temp_r_pointer])
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
                self._npackages
                - (self._read_pointer // self._package_nbytes)
                + (self._stored_write_pointer // self._package_nbytes)
            )
        return (self._stored_write_pointer - self._read_pointer) // self._package_nbytes
    
    def _next_write_pointer(self) -> None:
        self._internal_write_pointer += self._package_nbytes
        self._internal_write_pointer %= self._npackages * self._package_nbytes

        self._stored_write_pointer = self._internal_write_pointer

    def _next_read_pointer(self) -> typing.Optional[int]:
        if self._read_pointer == self._stored_write_pointer:
            self.L.logger.debug("read pointer == write pointer")
            return None
        self._read_pointer += self._package_nbytes
        self._read_pointer %= self._npackages * self._package_nbytes
        return self._read_pointer 
    
    @property #this return final chunk in our case this is 256byte long not a write pointer
    def _stored_write_pointer(self) -> int:
        return int.from_bytes(
            self._memory.buf[
                self._total_nbytes
    
                 - self._write_pntr_nbytes : self._total_nbytes
           ],
           byteorder="big",
       )
    
    @_stored_write_pointer.setter
    def _stored_write_pointer(self, n: int) -> None:
        self._memory.buf[
            self._total_nbytes
            - self._write_pntr_nbytes : self._total_nbytes
        ] = n.to_bytes(self._write_pntr_nbytes, byteorder="big")

    def bpush(self, item: bytearray) -> None:
        """
        Pushes an item to the buffer.

        Args:
            item (:obj:`bytearray`): The item to put into the buffer.

        Returns:
            ``None``

        Raises:
            :obj:`~.errors.WriteOperationsForbidden`: The buffer cannot be written to by this instance.
        """
        # if not self._writeable:
        #     raise shm_buffer_errors.WriteOperationsForbidden("Buffer is not writeable")
        
        byte_encoded_array = bytearray(self._package_nbytes)
        if len(item) < self._package_nbytes :
            byte_encoded_array[0:len(item)] = item
        else:
            raise shm_buffer_errors.ItemLengthExceededError("Max Length available for single item is exceeded")
        
        
        self._next_write_pointer()
        temp_w_pointer = self._internal_write_pointer or (self._package_nbytes * self._npackages)
        package_start_idx = temp_w_pointer - self._package_nbytes
        
        self.L.logger.debug((f"writing to SHM {package_start_idx}:{temp_w_pointer} - {byte_encoded_array}" ))
        self._memory.buf[package_start_idx:temp_w_pointer] = byte_encoded_array

    def bpopitem(self, str2dict=True) -> typing.Optional[str]:
        """
        Pops an item from the buffer.

        Returns:
            Optional[ :obj:`str` ]: Item removed from the buffer, or ``None`` if there is nothing to read.

        Raises:
            :obj:`~.errors.ReadOperationsForbidden`: The buffer cannot be read from by this instance.
        """
        # if self._writeable:
        #     raise shm_buffer_errors.ReadOperationsForbidden("Buffer is not readable")

        if (read_addr := self._next_read_pointer()) is not None:
            temp_r_pointer = read_addr or (self._package_nbytes * self._npackages)
            package_start_idx = temp_r_pointer-self._package_nbytes
            tmp_val = bytearray(self._memory.buf[package_start_idx : temp_r_pointer])
            
            self.L.logger.debug((f"reading from SHM {package_start_idx}:{temp_r_pointer} - {tmp_val}" ))

            if str2dict:
                val = extract_packet_data(tmp_val)
                # print(val)
                return val
            return tmp_val.decode('utf-8')
        return None