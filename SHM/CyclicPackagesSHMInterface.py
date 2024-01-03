import numpy as np
import struct
import typing

from shm_interface_utils import load_shm_structure_JSON
from shm_interface_utils import access_shm
from shm_interface_utils import parseJSON

class CyclicPackagesSHMInterface:
    def __init__(self, shm_structure_JSON_fname):
        shm_structure = load_shm_structure_JSON(shm_structure_JSON_fname)

        self._shm_name = shm_structure["shm_name"]
        self._total_nbytes = shm_structure["total_nbytes"]

        self._shm_packages_nbytes = shm_structure["field"]["shm_packages_nbytes"]
        self._write_pntr_nbytes = shm_structure["field"]["write_pntr_nbytes"]
        self._npackages = shm_structure["metadata"]["npackages"]
        self._package_nbytes = shm_structure["metadata"]["package_nbytes"]

        self._memory = access_shm(self._shm_name)
        
        self._internal_write_pointer = 0
        self._read_pointer = 0
        
    # def __str__(self) -> str:
    #     if self._writeable:
    #         return f"SharedCircularBuffer ({self.name})"
    #     return f"SharedCircularBuffer ({self.name}) ({(self.usage / self._npackages) * 100:.2f}% full)"

    @property
    def _stored_write_pointer(self) -> int:
        return int.from_bytes(
            self._memory.buf[
                self._total_nbytes
                - self._write_pntr_nbytes : self._total_nbytes
            ], byteorder="big",
        )
        # raw_pntr = self._memory.buf[self._shm_packages_nbytes:self._total_nbytes]
        # return int.from_bytes(raw_pntr, byteorder="big")

    @_stored_write_pointer.setter
    def _stored_write_pointer(self, n: int) -> None:
        self._memory.buf[
            self._total_nbytes
            - self._write_pntr_nbytes : self._total_nbytes
        ] = n.to_bytes(self._write_pntr_nbytes, byteorder="big")

    def _next_write_pointer(self) -> None:
        self._internal_write_pointer += self._package_nbytes
        self._internal_write_pointer %= self._npackages * self._package_nbytes

        self._stored_write_pointer = self._internal_write_pointer

    def _next_read_pointer(self) -> typing.Optional[int]:
        if self._read_pointer == self._stored_write_pointer:
            return None
        self._read_pointer += self._package_nbytes
        self._read_pointer %= self._npackages * self._package_nbytes
        return self._read_pointer

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

    def push(self, item: int) -> None:
        """
        Pushes an item to the buffer.

        Args:
            item (:obj:`int`): The item to put into the buffer.

        Returns:
            ``None``

        Raises:
            :obj:`~.errors.WriteOperationsForbidden`: The buffer cannot be written to by this instance.
        """
        # if not self._writeable:
        #     raise errors.WriteOperationsForbidden("Buffer is not writeable")

        self._next_write_pointer()
        temp_w_pointer = self._internal_write_pointer or (self._package_nbytes * self._npackages)
        self._memory.buf[
            temp_w_pointer - self._package_nbytes : temp_w_pointer
        ] = item.to_bytes(self._package_nbytes, byteorder="big")

    def popitem(self) -> typing.Optional[int]:
        """
        Pops an item from the buffer.

        Returns:
            Optional[ :obj:`int` ]: Item removed from the buffer, or ``None`` if there is nothing to read.

        Raises:
            :obj:`~.errors.ReadOperationsForbidden`: The buffer cannot be read from by this instance.
        """
        # if self._writeable:
        #     raise errors.ReadOperationsForbidden("Buffer is not readable")

        if (read_addr := self._next_read_pointer()) is not None:
            temp_r_pointer = read_addr or (self._package_nbytes * self._npackages)
            return int.from_bytes(
                self._memory.buf[temp_r_pointer - self._package_nbytes : temp_r_pointer],
                byteorder="big",
            )
        return None

    def popmany(self, n: int) -> typing.Sequence[int]:
        """
        Pops up to a maximum of ``n`` items from the buffer.

        Returns:
            Sequence[ :obj:`int` ]: Items removed from the buffer.

        Raises:
            :obj:`~.errors.ReadOperationsForbidden`: The buffer cannot be read from by this instance.
        """
        # if self._writeable:
        #     raise errors.ReadOperationsForbidden("Buffer is not readable")

        items = []
        for _ in range(n):
            if (item := self.popitem()) is not None:
                items.append(item)
            else:
                break
        return items