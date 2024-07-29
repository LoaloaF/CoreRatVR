import os
from time import sleep
from datetime import datetime as dt

from fastapi import HTTPException
from typing import Any
import psutil
import json

from Parameters import Parameters
from CustomLogger import CustomLogger as Logger

def _parse2type(value: str, correct_type: type):
    try:
        if correct_type == int:
            return int(value)
        if correct_type == float:
            return float(value)
        if correct_type == bool:
            if value.lower() in ('false', '0'):
                return False
            else:
                return True
    except ValueError:
        return 
    
def patch_parameter(key: str, new_value: Any, was_initiated: bool):
    validate_state({"initiated": was_initiated}, valid_initiated=False)
    
    P = Parameters()
    correct_type = type(P.__getattribute__(key))
    if not hasattr(P, key):
        raise HTTPException(status_code=404, detail=f"Parameter {key} not found")
    if not isinstance(new_value, correct_type):
        if (new_value := _parse2type(new_value, correct_type)) is None:
            raise HTTPException(status_code=400, detail=f"value must be of type {correct_type}")
    if key in P.get_locked_parameters():
        raise HTTPException(status_code=400, detail=f"{key} is not mutable")
    
    setattr(P, key, new_value)
    return {"message": f"Parameter {key} updated successfully"}

def init_save_dir():
    P = Parameters()
    dirname = dt.now().strftime(P.SESSION_NAME_TEMPLATE)
    full_path = os.path.join(P.DATA_DIRECTORY, dirname)
    os.mkdir(full_path)
    if P.CREATE_NAS_SESSION_DIR:
        os.mkdir(os.path.join(P.NAS_DATA_DIRECTORY, dirname))
    return full_path

def check_base_dirs():
    P = Parameters()
    for d in (P.LOGGING_DIRECTORY,P.DATA_DIRECTORY,P.SHM_STRUCTURE_DIRECTORY):
        if not os.path.exists(d):
            # logger not initialized yet
            print(f"Directory {d} does not exist. Creating it...")
            os.mkdir(d)

def init_logger(session_save_dir):
    P = Parameters()
    L = Logger()
    if L.logger.handlers:
        L.reset_logger()
    log_dir = session_save_dir if P.LOG_TO_DATA_DIR else P.LOGGING_DIRECTORY
    L.init_logger("__main__", log_dir, P.LOGGING_LEVEL)
    return log_dir

def validate_state(state, valid_initiated=None, valid_paradigmRunning=None, 
                   valid_shm_created=None, valid_proc_running=None):
    L = Logger()

    # check if passed unitySessionRunning var matches state
    if (valid_paradigmRunning is not None and 
        state["paradigmRunning"] != valid_paradigmRunning):
        detail = "Unity session" 
        detail += "not running" if valid_paradigmRunning else "already running"
        L.logger.error(detail)
        raise HTTPException(status_code=400, detail=detail)

    # check if passed initiated var matches state
    if valid_initiated is not None and state["initiated"] != valid_initiated:
        detail = "Not initiated" if valid_initiated else "Already initiated"
        L.logger.error(detail)
        raise HTTPException(status_code=400, detail=detail)
    
    # check if passed shm names var matches state
    if valid_shm_created is not None:
        # itereate over pairs of shm_name and the valid `was_created`` state
        for shm_name, valid_state in valid_shm_created.items():
            if state['shm'][shm_name] != valid_state:
                msg = "not created" if valid_shm_created[shm_name] else "already created"
                L.logger.error(f"{shm_name} shm {msg}")
                raise HTTPException(status_code=400, detail=f"{shm_name} shm {msg}")

    if valid_proc_running is not None:
        for proc_name, valid_state in valid_proc_running.items():
            if bool(state['procs'][proc_name]) != valid_state:
                msg = "not running" if valid_proc_running[proc_name] else "already running"
                L.logger.error(f"{proc_name} process {msg}")
                raise HTTPException(status_code=400, detail=f"{proc_name} process {msg}")

def check_processes(app):
    for proc_name, pid in app.state.state["procs"].items():
        if pid != 0:
            try:
                proc_status = psutil.Process(pid).status()
                if proc_status != psutil.STATUS_ZOMBIE:
                    continue
            # PID doesn't exist
            except psutil.NoSuchProcess:
                pass
            # PID doesn't exist
            app.state.state["procs"][proc_name] = 0
            if proc_name != "process_session":
                Logger().logger.warning(f"{proc_name} process terminated unexpectedly")

def state2serializable(state):
    S = state.copy()
    S['termflag_shm_interface'] = False if S['termflag_shm_interface'] is None else True
    S['unityinput_shm_interface'] = False if S['unityinput_shm_interface'] is None else True
    S['paradigm_running_shm_interface'] = False if S['paradigm_running_shm_interface'] is None else True
    return json.dumps(S)

class MockProcess:
            def __init__(self, pid=0):
                self.pid = pid
                
# DONETODO - check if arduino is connceted before launching process or try to auto flash Portenta:
# end point with exec platformio run --target upload --environment portenta_h7_m7 --project-dir /home/loaloa/homedataXPS/projects/ratvr/VirtualReality/PlatformIO/Projects/PortentaRatVR
# TODO - sudo chprio command passwordless - not important
# DONETODO - FastAPI state control
    # DONETODO - check if process is already running before launching (add to state?)
# TODO - design and build protoype user web interface 
# Unity
    # DONETODO - Fix empty arduino package error in Unity
    # DONETODO - Unity input SHM: think of instructions to be sent to Unity (before and after session start)
    # DONETODO - Unity start game with button
    # DONETODO - Unity link portenta input to UnityInputSHM
    # DONETODO - Unity UI
    # TODO - Unity gloabl sessionStarted conditinal for everything 9logging, state machine etc)
    # TODO - Unity fix lighting
    # TODO - Unity integrate Yuanzhao's FSM code
    # TODO - Unity Start stop sesion state machine interaction
    # DONETODO - Unity Teleportation
# TODO - TTL camera logger, check libraries, drivers etc
# TODO - from x from y integration into camera reader
# DONETODO - create folder data and tmp_shm if not exist
# DONETODO - add YAML file, use venv not conda