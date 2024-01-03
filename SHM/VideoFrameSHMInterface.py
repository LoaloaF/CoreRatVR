import numpy as np
import struct

from shm_interface_utils import load_shm_structure_JSON
from shm_interface_utils import access_shm

# use return types everywhere if you use them once

class VideoFrameSHMInterface:
    def __init__(self, shm_structure_JSON_fname):
        shm_structure = load_shm_structure_JSON(shm_structure_JSON_fname)
            
        self._shm_name = shm_structure["shm_name"]
        self._total_nbytes = shm_structure["total_nbytes"]
        self.tstamp_nbytes = shm_structure["fields"]["tstamp_nbytes"]
        self._frame_type = shm_structure["field_types"]["frame_type"]
        # self.framecount_bytes = shm_structure["fields"]["framecount_bytes"] 
        
        self.x_res = shm_structure["metadata"]["x_resolution"]
        self.y_res = shm_structure["metadata"]["y_resolution"]
        self.nchannels = shm_structure["metadata"]["nchannels"]

        self._memory = access_shm(self._shm_name)

    @property
    def _frame(self) -> np.ndarray:
        # return np.asarray(np.frombuffer(self._memory.buf[self.tstamp_nbytes:self._total_nbytes], dtype= np.uint8)).reshape( [ self._res[1], self._res[0], self._res[2] ])
        raw_frame = self._memory.buf[self.tstamp_nbytes:self._total_nbytes]
        np_frame = np.asarray(np.frombuffer(raw_frame, dtype=self._frame_type))
        return np_frame.reshape([self.x_res, self.y_res, self.nchannels])
    
    @_frame.setter
    def _frame(self, img: np.ndarray):
        self._memory.buf[self.tstamp_nbytes:self._total_nbytes] = bytearray(img[:])
    
    @property
    def _timestamp(self):
        [t]= struct.unpack("d",self._memory.buf[0:self.tstamp_nbytes])
        return t
    
    @_timestamp.setter
    def _timestamp(self, t):
        self._memory.buf[0:self.tstamp_nbytes] = struct.pack("d", t)

    #Trigger the event
    def add_frame(self, img, t):
        self._frame = img
        self._timestamp = t

    #Check whether event is set    
    def get_frame(self):
        return self._frame, self._timestamp

    #returns true if difference is larger than 1ms
    def compare_timestamps(self, t):
        # compares timestamp with the most recent frames
        return np.abs(self._timestamp - t) > 0.001 
    
    #Reset the event to 0
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self._shm_name}):lastframe->{self._timestamp}"