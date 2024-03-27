import numpy as np
import atexit
import typing

from CustomLogger import CustomLogger as Logger

from shm_interface_utils import load_shm_structure_JSON
from shm_interface_utils import access_shm
from shm_interface_utils import extract_packet_data

class CyclicPackagesSHMInterface:
    def __init__(self, shm_structure_JSON_fname):
        self.L = Logger()
        msg = f"SHM interface created with json {shm_structure_JSON_fname}"
        self.L.logger.debug(msg)
        shm_structure = load_shm_structure_JSON(shm_structure_JSON_fname)

        self._shm_name = shm_structure["shm_name"]
        self._total_nbytes = shm_structure["total_nbytes"]

        self._shm_packages_nbytes = shm_structure["fields"]["shm_packages_nbytes"]
        self._write_pntr_nbytes = shm_structure["fields"]["write_pntr_nbytes"]
        self._npackages = shm_structure["metadata"]["npackages"]   
        self._package_nbytes = shm_structure["metadata"]["package_nbytes"] 
        
        self._internal_w_pointer = 0
        self._read_pointer = 0
        
        self._memory = access_shm(self._shm_name)
        atexit.register(self.close_shm)

    def push(self, item: bytearray) -> None:
        if len(item) > self._package_nbytes:
            self.L.logger.debug((f"Item {item} of size {len(item)} > SHM size "
                                f"{self._package_nbytes}. Skipping."))
            return

        byte_encoded_array = bytearray(self._package_nbytes)
        byte_encoded_array[0:len(item)] = item
        
        self._next_internal_w_pointer()
        temp_w_pointer = self._internal_w_pointer 
        # if the write pointer is 0, we have to write to the last package
        if temp_w_pointer == 0:
            temp_w_pointer = self._npackages*self._package_nbytes
        package_start_idx = temp_w_pointer - self._package_nbytes

        self.L.logger.debug((f"Writing to SHM {package_start_idx}:"
                             f"{temp_w_pointer} - {byte_encoded_array}" ))
        self._memory.buf[package_start_idx:temp_w_pointer] = byte_encoded_array
        # write the internal write pointer to SHM so reader procs can read new pack
        self._update_stored_write_pointer()
        
    def popitem(self, return_type=bytearray
        ) -> typing.Optional[typing.Union[bytearray, str, dict]]:
        if (read_addr := self._next_read_pointer()) is not None:
            temp_r_pointer = read_addr 
            # if the read pointer is 0, we have to read to the last package
            if temp_r_pointer == 0:
                temp_r_pointer = self._package_nbytes*self._npackages
            package_start_idx = temp_r_pointer - self._package_nbytes
            
            self.L.logger.debug((f"Reading from SHM {package_start_idx}:"
                                f"{temp_r_pointer}, WPointer at "
                                f"{self._stored_write_pointer}"))
            item = bytearray(self._memory.buf[package_start_idx : temp_r_pointer])
            # self.L.logger.debug(f"All: {bytearray(self._memory.buf[0:self._total_nbytes])}")

            if return_type == bytearray:
                pass
            elif return_type == str:
                item = item.decode('utf-8')
            elif return_type == dict:
                item = extract_packet_data(item)
            
            if not item:
                L = Logger()
                L.logger.error(f"Empty packet from SHM: {item}")
            return item
        return None

    @property
    def usage(self) -> int:
        if self._read_pointer > self._stored_write_pointer:
            return (
                self._npackages
                - (self._read_pointer // self._package_nbytes)
                + (self._stored_write_pointer // self._package_nbytes)
            )
        rw_diff = self._stored_write_pointer-self._read_pointer
        return rw_diff // self._package_nbytes
    
    def _next_internal_w_pointer(self) -> None:
        self._internal_w_pointer += self._package_nbytes
        self._internal_w_pointer %= self._npackages * self._package_nbytes
        
        if self._internal_w_pointer == 0:
            self.L.logger.debug("Cycle completed")

    def _update_stored_write_pointer(self) -> None:
        self._stored_write_pointer = self._internal_w_pointer


    def _next_read_pointer(self) -> typing.Optional[int]:
        if self._read_pointer == self._stored_write_pointer:
            return None
        self._read_pointer += self._package_nbytes
        self._read_pointer %= self._npackages * self._package_nbytes
        return self._read_pointer 
    
    @property
    def _stored_write_pointer(self) -> int:
        w_pointer_start_idx = self._total_nbytes - self._write_pntr_nbytes
        raw_write_pointer = self._memory.buf[w_pointer_start_idx:self._total_nbytes]
        return int.from_bytes(raw_write_pointer, byteorder="big")
    
    @_stored_write_pointer.setter
    def _stored_write_pointer(self, new_w_pointer: int) -> None:
        w_pointer_start_idx = self._total_nbytes - self._write_pntr_nbytes
        raw_new_w_pointer = new_w_pointer.to_bytes(self._write_pntr_nbytes, 
                                                   byteorder="big")
        self._memory.buf[w_pointer_start_idx:self._total_nbytes] = raw_new_w_pointer

    def close_shm(self):
        L = Logger()
        L.logger.debug(f"Closing SHM interace access `{self._shm_name}`")
        self._memory.close()