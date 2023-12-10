import json
from multiprocessing import shared_memory

def load_shm_structure_JSON(filename):
    with open(filename) as f:
        shm_structure = json.load(f)
    return shm_structure

def access_shm(shm_name):
    return shared_memory.SharedMemory(name=shm_name, create=False)