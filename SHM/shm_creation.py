import atexit
import json
import os
from math import log

from multiprocessing import shared_memory
from multiprocessing.resource_tracker import unregister
from multiprocessing import Process, resource_tracker
from multiprocessing.shared_memory import SharedMemory

from CustomLogger import CustomLogger as Logger
from Parameters import Parameters

from shm_interface_utils import remove_shm_from_resource_tracker
from shm_interface_utils import remove_shm_from_resource_tracker

from OSXFileBasedSHM import OSXFileBasedSHM

# framecount isn't used right now, structure in general needs to be reconsiderd

def create_video_frame_shm(shm_name, x_resolution, y_resolution, 
                           nchannels):
    L = Logger()
    L.logger.info(f"Creating video frame SHM named `{shm_name}`")
    
    package_nbytes = 80
    frame_nbytes = x_resolution * y_resolution * nchannels
    total_nbytes = package_nbytes + frame_nbytes

    _create_shm(shm_name=shm_name, total_nbytes=total_nbytes)
    
    shm_structure = {
        "shm_type": "video_frame",
        "shm_name": shm_name,
        "total_nbytes": total_nbytes,
        "fields": {"package_nbytes": package_nbytes, 
                   "frame_nbytes":frame_nbytes},
        "field_types": {"tstamp_type": "uint64",
                        "framecount_type": "int",
                        "frame_type": "uint8"},
        "metadata": {"x_resolution": x_resolution, 
                     "y_resolution": y_resolution, 
                     "nchannels": nchannels,
                     "colorformat": "BGR",
                     },
    }
    

    shm_structure_fname = _write_json(shm_structure, shm_name)
    L.logger.debug("Test access to SHM from same process")
    validate_shm_structure(shm_structure_fname)
    return shm_structure_fname

def create_singlebyte_shm(shm_name): # flags
    L = Logger()
    L.logger.info(f"Creating single byte SHM named `{shm_name}`")
    _create_shm(shm_name=shm_name, total_nbytes=1)

    shm_structure = {
        "shm_type": "singlebyte",
        "shm_name": shm_name,
        "total_nbytes": 1,
    }
    return _write_json(shm_structure, shm_name)

def create_cyclic_packages_shm(shm_name, package_nbytes, npackages):
    L = Logger()
    L.logger.info(f"Creating cylic package SHM named `{shm_name}`")

    shm_packages_nbytes = package_nbytes*npackages
    write_pntr_nbytes = 8
    total_nbytes = write_pntr_nbytes + shm_packages_nbytes
    
    _create_shm(shm_name=shm_name, total_nbytes=total_nbytes)

    shm_structure = {
        "shm_type": "cyclic_packages",
        "shm_name": shm_name,
        "total_nbytes": total_nbytes,
        "fields": {"shm_packages_nbytes": shm_packages_nbytes,
                   "write_pntr_nbytes": write_pntr_nbytes, },
        "field_types": {"shm_packages_type": "str",
                        "write_pntr_type": "uint8"},
        "metadata": {"package_nbytes": package_nbytes,
                     "npackages": npackages, },
    }
    # shm_structure = validate_shm_structure(shm_structure)
    return _write_json(shm_structure, shm_name)

def create_cyclic_bytes_shm(shm_name,    ): # audio
    pass

def _create_shm(shm_name, total_nbytes):
    L = Logger()
    try:
        # disable automatic unlinking (deletion) of shm when an access proc dies
        remove_shm_from_resource_tracker()
        
        L.logger.info(os.uname().sysname)
        # check if the system is mac os
        if os.uname().sysname != "Darwin":
            L.logger.info("IN")
            
            shm = shared_memory.SharedMemory(name=shm_name, create=True, 
                                            size=total_nbytes)
        else:
            shm = OSXFileBasedSHM(shm_name, create=True, size=total_nbytes)
        
        atexit.register(_cleanup, shm, shm_name)
        shm.buf[:total_nbytes] = bytearray(total_nbytes)
    
    except FileExistsError:
        L.logger.error(f"SHM named `{shm_name}` already exists.")
        L.logger.info("Attemping to close it...")
        shm = shared_memory.SharedMemory(name=shm_name, create=False)
        _cleanup(shm, shm_name)
        exit(1)

def _cleanup(shm, shm_name):
    P = Parameters()
    L = Logger()
    try:
        L.logger.info(f"Deleting SHM `{shm_name}`")
        shm.unlink()
    except FileNotFoundError as e:
        L.logger.warning(str(e))

    fname = f"{shm_name}_shmstruct.json"
    full_fname = os.path.join(P.SHM_STRUCTURE_DIRECTORY, fname)
    L.logger.debug(f"Deleting tmp SHM structure JSON file: {full_fname}")
    os.remove(full_fname)

def validate_shm_structure(shm_structure_fname):
    # do checks 
    pass
    
def _write_json(shm_structure, shm_name):
    P = Parameters()
    fname = f"{shm_name}_shmstruct.json"
    full_fname = os.path.join(P.SHM_STRUCTURE_DIRECTORY, fname)
    with open(full_fname, "w") as f:
        json.dump(shm_structure, f)
    return full_fname

def delete_shm(shm_name):
    # logging
    if os.uname().sysname != "Darwin":
        shm = shared_memory.SharedMemory(name=shm_name, create=False)
    else:
        shm = OSXFileBasedSHM(shm_name, create=False)
        _cleanup(shm, shm_name)