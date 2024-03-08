import os
from time import sleep
from datetime import datetime as dt

from fastapi import HTTPException
from typing import Any

from Parameters import Parameters
from CustomLogger import CustomLogger as Logger

from SHM.shm_creation import create_cyclic_packages_shm
from SHM.shm_creation import create_singlebyte_shm
from SHM.shm_creation import delete_shm

from FlagSHMInterface import FlagSHMInterface
from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface

from process_launcher import open_por2shm2por_proc
from process_launcher import open_log_portenta_proc
from process_launcher import open_stream_portenta_proc
from process_launcher import open_por2shm2por_sim_proc

def GET_get_parameters():
    P = Parameters()
    return P.get_attributes()

def PATCH_update_parameter(key: str, new_value: Any, was_initiated: bool):
    P = Parameters()
    correct_type = type(P.__getattribute__(key))
    if not hasattr(P, key):
        raise HTTPException(status_code=404, detail=f"Parameter {key} not found")
    if not isinstance(key, correct_type):
        raise HTTPException(status_code=400, detail=f"value must be of type {correct_type}")
    if was_initiated:
        raise HTTPException(status_code=400, detail=f"Already initiated - Paramteres are locked.")
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
    L.init_logger(__name__, log_dir, P.LOGGING_LEVEL)
    return log_dir

def handle_create_termflag_shm():
    P = Parameters()
    create_singlebyte_shm(shm_name=P.SHM_NAME_TERM_FLAG)

def handle_create_ballvelocity_shm():
    P = Parameters()
    create_cyclic_packages_shm(shm_name=P.SHM_NAME_BALLVELOCITY, 
                               package_nbytes=P.SHM_PACKAGE_NBYTES_BALLVELOCITY, 
                               npackages=P.SHM_NPACKAGES_BALLVELOCITY)

def handle_create_portentaoutput_shm():
    P = Parameters()
    create_cyclic_packages_shm(shm_name=P.SHM_NAME_PORTENTA_OUTPUT, 
                               package_nbytes=P.SHM_PACKAGE_NBYTES_PORTENTA_OUTPUT, 
                               npackages=P.SHM_NPACKAGES_PORTENTA_OUTPUT)

def handle_create_portentainput_shm():
    P = Parameters()
    create_cyclic_packages_shm(shm_name=P.SHM_NAME_PORTENTA_INPUT, 
                               package_nbytes=P.SHM_PACKAGE_NBYTES_PORTENTA_INPUT, 
                               npackages=P.SHM_NPACKAGES_PORTENTA_INPUT)

def handle_open_por2shm2por_sim_proc():
    P = Parameters()
    constr_fname = lambda name: os.path.join(P.SHM_STRUCTURE_DIRECTORY, 
                                             name+"_shmstruct.json")
    kwargs = {
        "termflag_shm_struc_fname": constr_fname(P.SHM_NAME_TERM_FLAG),
        "ballvelocity_shm_struc_fname": constr_fname(P.SHM_NAME_BALLVELOCITY),
        "portentaoutput_shm_struc_fname": constr_fname(P.SHM_NAME_PORTENTA_OUTPUT),
        "portentainput_shm_struc_fname": constr_fname(P.SHM_NAME_PORTENTA_INPUT),
        "port_name": P.PORTENTA_PORT,
        "baud_rate": P.PORTENTA_BAUD_RATE,
        }
    return open_por2shm2por_sim_proc(logging_name="por2shm2por_sim", **kwargs)

def handle_open_por2shm2por_proc():
    P = Parameters()
    constr_fname = lambda name: os.path.join(P.SHM_STRUCTURE_DIRECTORY, 
                                             name+"_shmstruct.json")
    kwargs = {
        "termflag_shm_struc_fname": constr_fname(P.SHM_NAME_TERM_FLAG),
        "ballvelocity_shm_struc_fname": constr_fname(P.SHM_NAME_BALLVELOCITY),
        "portentaoutput_shm_struc_fname": constr_fname(P.SHM_NAME_PORTENTA_OUTPUT),
        "portentainput_shm_struc_fname": constr_fname(P.SHM_NAME_PORTENTA_INPUT),
        "port_name": P.PORTENTA_PORT,
        "baud_rate": P.PORTENTA_BAUD_RATE,
        }
    return open_por2shm2por_proc(logging_name="por2shm2por", **kwargs)
    
def handle_open_log_portenta_proc():
    P = Parameters()
    constr_fname = lambda name: os.path.join(P.SHM_STRUCTURE_DIRECTORY, 
                                             name+"_shmstruct.json")
    kwargs = {
        "termflag_shm_struc_fname": constr_fname(P.SHM_NAME_TERM_FLAG),
        "ballvelocity_shm_struc_fname": constr_fname(P.SHM_NAME_BALLVELOCITY),
        "portentaoutput_shm_struc_fname": constr_fname(P.SHM_NAME_PORTENTA_OUTPUT),
        "session_data_dir": P.SESSION_DATA_DIRECTORY,
        }
    return open_log_portenta_proc(logging_name="log_portenta", **kwargs)
    
###
# TO DO - merge process launching into process launcher, take away backend functions
# TO DO - test cameara
# TO DO - cleanup SHM stuff, like logging formatting etc
# TO DO - check if arduino is connceted before launching process
# TO DO - write logger proccess properly

def POST_raise_term_flag(open_shm_mem_names):
    P = Parameters()
    shm_structure_JSON_fname = P.SHM_NAME_TERM_FLAG + "_shmstruct.json"
    full_fname = os.path.join(P.SHM_STRUCTURE_DIRECTORY, shm_structure_JSON_fname)
    interface = FlagSHMInterface(full_fname)
    interface.set()
    interface.close_shm()

    sleep(1)
    [delete_shm(shm_name) for shm_name in open_shm_mem_names]
    sleep(1)