import atexit
from multiprocessing import shared_memory
import json
import os

from shm_buffer_errors import BufferAlreadyCreated
from constants import SHM_STRUCTURE_DIRECTORY

# framecount isn't used right now, structure in general needs to be reconsiderd

def create_video_frame_shm(shm_name, x_resolution, y_resolution, n_channels):
    tstamp_bytes = 8
    framecount_bytes = 0
    frame_bytes = x_resolution * y_resolution * n_channels
    total_bytes = tstamp_bytes + framecount_bytes + frame_bytes

    _create_shm(shm_name=shm_name, total_bytes=total_bytes)
    
    shm_structure = {
        "shm_name": shm_name,
        "total_bytes": total_bytes,
        "field_types": {},
        "metadata": {"x_resolution": x_resolution, 
                     "y_resolution": y_resolution, 
                     "n_channels": n_channels,
                     },
        "fields": {"tstamp_bytes": tstamp_bytes,
                   "framecount_bytes": framecount_bytes,
                   "frame_bytes":frame_bytes}
    }
    return _write_json(shm_structure, shm_name)

def create_singlebyte_shm(shm_name): # flags
    _create_shm(shm_name=shm_name, total_bytes=1)
    shm_structure = {
        "shm_name": shm_name,
        "total_bytes": 1,
    }
    return _write_json(shm_structure, shm_name)

def create_cyclic_structure_shm(shm_name,    ): # sensors
    pass

def create_cyclic_bytes_shm(shm_name,    ): # audio
    pass

def _create_shm(shm_name, total_bytes):
    try:
        shm_mem = shared_memory.SharedMemory(name=shm_name, create=True, 
                                             size=total_bytes)
        shm_mem.buf[:] = bytearray(total_bytes)
    
    except FileExistsError as e:
        raise BufferAlreadyCreated(
            "Buffer with that name already exists"
        ) from e

    atexit.register(_cleanup, shm_mem, shm_name)

def _cleanup(shm_mem, shm_name):
    print("cleanin uppp ", shm_name, "SHM")
    shm_mem.close()
    shm_mem.unlink()
    fname = f"{shm_name}_shmstruct.json"
    full_fname = os.path.join(SHM_STRUCTURE_DIRECTORY, fname)
    os.remove(full_fname)

def _write_json(shm_structure, shm_name):
    fname = f"{shm_name}_shmstruct.json"
    full_fname = os.path.join(SHM_STRUCTURE_DIRECTORY, fname)
    with open(full_fname, "w") as f:
        json.dump(shm_structure, f)
    return full_fname