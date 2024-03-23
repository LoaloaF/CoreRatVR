import numpy as np
import typing
import atexit
import time

from shm_interface_utils import load_shm_structure_JSON
from shm_interface_utils import access_shm
from shm_interface_utils import extract_packet_data

from CustomLogger import CustomLogger as Logger

class VideoFrameSHMInterface:
    def __init__(self, shm_structure_JSON_fname):
        L = Logger()
        L.logger.debug(f"SHM interface created with json {shm_structure_JSON_fname}")
        shm_structure = load_shm_structure_JSON(shm_structure_JSON_fname)
            
        self._shm_name = shm_structure["shm_name"]
        self._total_nbytes = shm_structure["total_nbytes"]
        self._package_nbytes = shm_structure["fields"]["package_nbytes"]
        self._frame_type = shm_structure["field_types"]["frame_type"]
        # self.framecount_bytes = shm_structure["fields"]["framecount_bytes"] 
        
        self.x_res = shm_structure["metadata"]["x_resolution"]
        self.y_res = shm_structure["metadata"]["y_resolution"]
        self.nchannels = shm_structure["metadata"]["nchannels"]

        self._memory = access_shm(self._shm_name)
        atexit.register(self.close_shm)

    @property
    def _frame(self) -> np.ndarray:
        raw_frame = self._memory.buf[self._package_nbytes:self._total_nbytes]
        np_frame = np.asarray(np.frombuffer(raw_frame, dtype=self._frame_type))
        return np_frame.reshape([self.y_res, self.x_res, self.nchannels])
    
    @_frame.setter
    def _frame(self, img: np.ndarray):
        # swapaxes is used to convert from opencv format to numpy format (y-x-c)
        t0 = time.time()
        frame_raw = bytearray(np.swapaxes(img,0,1))
        self._memory.buf[self._package_nbytes:self._total_nbytes] = frame_raw
        Logger().logger.debug(f"SHM write in {time.time()-t0:.6f} s")
    
    #Trigger the event
    def add_frame(self, img, package):
        self._frame = img
        self._package = package

    def get_frame(self):
        return self._frame
    
    def get_package(self, return_type=bytearray
        ) -> typing.Optional[typing.Union[bytearray, str, dict]]:
        pack = self._package
        if return_type == bytearray:
            pass
        elif return_type == str:
            pack = pack.decode('utf-8')
        elif return_type == dict:
            pack = extract_packet_data(pack)
            pack = pack if pack else {}
        return pack
    
    @property
    def _package(self):
        return bytearray(self._memory.buf[0:self._package_nbytes])
    
    @_package.setter
    def _package(self, pack: bytearray):
        package = bytearray(self._package_nbytes)
        package[0:len(pack)] = pack
        self._memory.buf[0:self._package_nbytes] = package

    def close_shm(self):
        L = Logger()
        L.logger.debug(f"Closing SHM interace access `{self._shm_name}`")
        self._memory.close()