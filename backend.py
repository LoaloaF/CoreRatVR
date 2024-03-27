import os
from time import sleep
from datetime import datetime as dt

from fastapi import HTTPException
from typing import Any

from Parameters import Parameters
from CustomLogger import CustomLogger as Logger

from SHM.shm_creation import delete_shm

from FlagSHMInterface import FlagSHMInterface

from process_launcher import shm_struct_fname

def GET_get_parameters():
    P = Parameters()
    return P.get_attributes()

def PATCH_update_parameter(key: str, new_value: Any, was_initiated: bool):
    validate_state({"initiated": was_initiated}, valid_initiated=False)
    
    P = Parameters()
    correct_type = type(P.__getattribute__(key))
    if not hasattr(P, key):
        raise HTTPException(status_code=404, detail=f"Parameter {key} not found")
    if not isinstance(key, correct_type):
        raise HTTPException(status_code=400, detail=f"value must be of type {correct_type}")
    if key == "SESSION_DATA_DIRECTORY":
        raise HTTPException(status_code=400, detail=f"SESSION_DATA_DIRECTORY is not mutable")
    
    setattr(P, key, new_value)
    return {"message": f"Parameter {key} updated successfully"}

def init_save_dir():
    P = Parameters()
    dirname = dt.now().strftime(P.SESSION_NAME_PREFIX)+P.SESSION_NAME_POSTFIX
    full_path = os.path.join(P.DATA_DIRECTORY, dirname)
    os.mkdir(full_path)
    return full_path

def init_logger(session_save_dir):
    P = Parameters()
    L = Logger()
    if L.logger.handlers:
        L.reset_logger()
    log_dir = session_save_dir if P.LOG_TO_DATA_DIR else P.LOGGING_DIRECTORY
    L.init_logger("__main__", log_dir, P.LOGGING_LEVEL)
    return log_dir

def validate_state(state, valid_initiated=None, valid_shm_created=None):
    L = Logger()

    # check if passed initiated var matches state
    if valid_initiated is not None and state["initiated"] != valid_initiated:
        detail = "Not initiated" if valid_initiated else "Already initiated"
        L.logger.error(detail)
        raise HTTPException(status_code=400, detail=detail)
    
    # check if passed shm names var matches state
    if valid_shm_created is not None:
        # itereate over pairs of shm_name and the valid `was_created`` state
        for shm_name, valid_state in valid_shm_created.items():
            if state[shm_name] != valid_state:
                msg = "not created" if valid_shm_created[shm_name] else "already created"
                L.logger.error(f"{shm_name} shm {msg}")
                raise HTTPException(status_code=400, detail=f"{shm_name} shm {msg}")

def POST_raise_term_flag(open_shm_mem_names):
    P = Parameters()
    interface = FlagSHMInterface(shm_struct_fname(P.SHM_NAME_TERM_FLAG))
    interface.set()
    interface.close_shm()

    sleep(1)
    [delete_shm(shm_name) for shm_name in open_shm_mem_names]
    sleep(1)

# TODO - check if arduino is connceted before launching process or try to auto flash Portenta
# TODO - Fix empty arduino package error in Unity
# TODO - sudo chprio command passwordless
# TODO - check if process is already running before launching (add to state?)
# TODO - design and build protoype user web interface 
# TODO - Unity input SHM: think of instructions to be sent to Unity (before and after session start)
# TODO - Unity start game with button
# TODO - Unity link portenta input to FSM and UnityInputSHM
# TODO - Unity UI
# TODO - TTL camera logger
# TODO - Unity state
# TODO - log state when changed
# TODO - create folder data and tmp_shm if not exist
# TODO - add YAML file, use venv not conda
# TODO - Unity fix lighting
# TODO - Unity Start stop sesion state machine interaction
# TODO - Unity Teleportation