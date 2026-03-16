import os
import psutil
import json
import h5py
from datetime import datetime as dt
import pandas as pd

from fastapi import HTTPException
from typing import Any

from Parameters import Parameters
from CustomLogger import CustomLogger as Logger

def shm_struct_fname(shm_name):
    P = Parameters()
    return os.path.join(P.SHM_STRUCTURE_DIRECTORY, shm_name+"_shmstruct.json")

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
        if correct_type == list:
            return value.split(",")
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
    # close any loggers that might be open from preious usage (dir may no longer exist)
    if L.logger.handlers:
        L.reset_logger()
    log_dir = session_save_dir if P.LOG_TO_DATA_DIR else P.LOGGING_DIRECTORY
    L.init_logger("__main__", log_dir, P.LOGGING_LEVEL)
    return log_dir

def validate_state(state, valid_initiated=None, valid_initiated_inspect=None, 
                   valid_paradigmRunning=None, valid_shm_created=None, 
                   valid_proc_running=None):
    L = Logger()
    if (valid_initiated_inspect is not None and state["initiatedInspect"] != valid_initiated_inspect):
        detail = "No session loaded" if valid_initiated_inspect else "Already loaded session"
        L.logger.error(detail)
        raise HTTPException(status_code=400, detail=detail)

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

def access_session_data(key, pct_as_index=True, na2null=True, rename2oldkeys=True):
    P = Parameters()
    L = Logger()
    session_fullfname = os.path.join(P.SESSION_DATA_DIRECTORY, P.SESSION_NAME)
    
    try:
        data = pd.read_hdf(session_fullfname, key=key)
        L.logger.debug(f"Successfully accessed {key} from session data:\n{data}")
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Key {key} not found in session data")

    if na2null:
        # Convert float64 columns to object type
        for col in data.select_dtypes(include=['float64']).columns:
            data[col] = data[col].astype(object)
        # Fill NaN values with "null"
        data.fillna("null", inplace=True)
        
    if pct_as_index:
        pct_col = [col for col in data.columns if col.endswith("_pc_timestamp")][0]
        if data[pct_col].is_unique:
            data.set_index(data[pct_col], inplace=True, drop=True)
        else:
            n = data.shape[0]
            data = data.drop_duplicates(subset=[pct_col])
            L.logger.warning(f"Non-unique index values found in the "
                            f"timestamp column. Before {n} rows, after "
                            f"{data.shape[0]}, diff {n-data.shape[0]}")
        data.set_index(pd.to_datetime(data[pct_col], unit='us'), 
                        inplace=True, drop=True)
    
    if rename2oldkeys:
        if key == "unity_frame":
            rename_dict = {
                'frame_id': 'ID',
                'frame_pc_timestamp': 'PCT',
                'frame_x_position': 'X',
                'frame_z_position': 'Z',
                'frame_angle': 'A',
                'frame_state': 'S' ,
                'frame_blinker': 'FB',
                'ballvelocity_first_package': 'BFP',
                'ballvelocity_last_package': 'BLP',
            }
            # add back the name "U", indicating Unity frame
            data['N'] = "U"
        elif key == "unity_trial":
            rename_dict = {
                "trial_id": "ID", 
                "trial_start_frame": "SFID", 
                "trial_start_pc_timestamp": "SPCT", 
                "trial_end_frame": "EFID", 
                "trial_end_pc_timestamp": "EPCT",
                "trial_pc_duration": "TD", 
                "trial_outcome": "O"}
        elif key == "paradigmVariable_data":
            rename_dict = {}
            
        elif key in ["event", "ballvelocity"]:
            rename_dict = {
                f'{key}_package_id': 'ID',
                f'{key}_portenta_timestamp': 'T',
                f'{key}_pc_timestamp': 'PCT',
                f'{key}_value': 'V',
                f'{key}_name': 'N',
            }
            if key == "ballvelocity":
                rename_dict.update({
                    'ballvelocity_raw': "raw",
                    'ballvelocity_yaw': "yaw",
                    'ballvelocity_pitch': "pitch",
                    })
        
        L.logger.debug(f"Renaming columns to old keys: {data.columns}")
        data = data.rename(columns=rename_dict)


    if "cam" in key:
        # return the 
        sessionfile = h5py.File(session_fullfname, 'r')
        return data, sessionfile
    return data

class MockProcess:
    def __init__(self, pid=0):
        self.pid = pid