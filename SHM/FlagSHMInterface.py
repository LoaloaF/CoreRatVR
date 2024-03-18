from shm_interface_utils import load_shm_structure_JSON
from shm_interface_utils import access_shm
from CustomLogger import CustomLogger as Logger
import atexit

class FlagSHMInterface:
    def __init__(self, shm_structure_JSON_fname):
        L = Logger()
        L.logger.debug(f"SHM interface created with json {shm_structure_JSON_fname}")
        shm_structure = load_shm_structure_JSON(shm_structure_JSON_fname)

        self._shm_name = shm_structure["shm_name"]
        self._memory = access_shm(self._shm_name)
        atexit.register(self.close_shm)

    @property
    def _state(self) -> bool:
        if (self._memory.buf[0] == 0):#b'\x00'):
            return False
        else: 
            return True
    
    @_state.setter
    def _state(self, state: bool):
        if(state):
            self._memory.buf[0] = 1 # b'\x01'
        else:
            self._memory.buf[0] = 0 #b'\x00'
    
    #Trigger the event
    def set(self):
        self._state = True

    #Check whether event is set    
    def is_set(self):
        return self._state

    #Reset the event to 0
    def reset(self):
        self._state = False

    def close_shm(self):
        L = Logger()
        L.logger.debug(f"Closing SHM interace access `{self._shm_name}`")
        self._memory.close()