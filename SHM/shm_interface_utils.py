import numpy as np
import json
from multiprocessing import shared_memory

def load_shm_structure_JSON(filename):
    with open(filename) as f:
        shm_structure = json.load(f)
        shm_structure = parse_str_types(shm_structure)
    return shm_structure

def access_shm(shm_name):
    try:
        shm = shared_memory.SharedMemory(name=shm_name, create=False)
    except FileNotFoundError:
        print(f"Trying to access SHM `{shm_name}` that has not been created.")
        exit(1)
    return shm

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