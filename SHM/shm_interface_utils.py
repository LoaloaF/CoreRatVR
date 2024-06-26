import os
import numpy as np
import json

from multiprocessing import shared_memory
from multiprocessing import resource_tracker

from CustomLogger import CustomLogger as Logger

from OSXFileBasedSHM import OSXFileBasedSHM

def remove_shm_from_resource_tracker():
    """Monkey-patch multiprocessing.resource_tracker so SharedMemory won't be tracked

    More details at: https://bugs.python.org/issue38119
    """

    def fix_register(name, rtype):
        if rtype == "shared_memory":
            return
        return resource_tracker._resource_tracker.register(self, name, rtype)
    resource_tracker.register = fix_register

    def fix_unregister(name, rtype):
        if rtype == "shared_memory":
            return
        return resource_tracker._resource_tracker.unregister(self, name, rtype)
    resource_tracker.unregister = fix_unregister

    if "shared_memory" in resource_tracker._CLEANUP_FUNCS:
        del resource_tracker._CLEANUP_FUNCS["shared_memory"]

def load_shm_structure_JSON(filename):
    with open(filename) as f:
        shm_structure = json.load(f)
        shm_structure = parse_str_types(shm_structure)
    return shm_structure

def access_shm(shm_name):
    L = Logger()
    try:
        # disable automatic unlinking (deletion) of shm when an access proc dies
        remove_shm_from_resource_tracker()

        if os.uname().sysname != "Darwin":
            shm = shared_memory.SharedMemory(name=shm_name, create=False)
        else:
            shm = OSXFileBasedSHM(shm_name, create=False)
                    
        L.logger.debug(f"SHM interface (R/W) successfully linked `{shm_name}`")

    except FileNotFoundError:
        L.logger.error(f"Trying to access SHM `{shm_name}` that has not been created.")
        L.spacer()
        exit(1)
    return shm


def extract_packet_data(bytes_packet):
    # encaps name_value with (is a string)
    def wrap_str_values(pack, key):
        name_idx = pack.find(key)+3
        name_value = pack[name_idx:pack.find(",", name_idx)]
        return pack.replace(name_value, f'"{name_value}"', 1)
    L = Logger()    
    
    bytes_packet = bytes_packet[:bytes_packet.find(b"\n")+1]
    pack = bytes_packet.decode("utf-8")[1:-3] # strip < and \r\n>

    # wrap the ball velocity value in " " marks
    if pack[pack.find("N:"):].startswith("N:B"):
        pack = wrap_str_values(pack, key=",V:")
    # wrap the name value in " " marks
    pack = wrap_str_values(pack, key="{N:")

    # insert quotes after { and , and before : to wrap keys in quotes
    json_pack = pack.replace("{", '{"').replace(":", '":').replace(",", ',"')
    # L.logger.debug(json_pack)
    try:
        return json.loads(json_pack)
    except json.JSONDecodeError as e:
        L = Logger()
        pack = {"N":"ER", "V":str(json_pack)}
        L.logger.error(f"Failed JSON parsing package: {pack}")
        return pack
    
def parse_str_types(shm_structure):
    field_types = shm_structure.get("field_types")
    if field_types is None:
        return shm_structure
    
    for key, which_type in field_types.items():
        which_type = which_type.lower()
        
        if which_type in ("str", "string"):
            dtype = str
        
        elif which_type == 'float':
            dtype = float
        
        elif "int" in which_type:
            unsigned = which_type.startswith("u")
            bits = which_type[which_type.find("int")+3:]
            bits = bits if bits else 64
            
            dtype = {
                8: np.uint8 if unsigned else np.int8,
                16: np.uint16 if unsigned else np.int16,
                32: np.uint32 if unsigned else np.int32,
                64: np.uint64 if unsigned else np.int64,
                }.get(int(bits))
            
            if dtype is None:
                print(f"FATAL: Could not parse SHM type {key}:`{which_type}`")
                exit(1)
        shm_structure["field_types"][key] = dtype
    return shm_structure