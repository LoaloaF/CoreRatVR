import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import argparse
import pandas as pd
from time import sleep

from CustomLogger import CustomLogger as Logger
from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _check_package(package, prv_id, prv_BVid):
    # check for ID discontinuity
    if (dif := (package["ID"]-prv_id)) != 1:
        L.logger.warning(f"Frame Package ID discontinuous; gap was {dif}")
    
    if (dif := (package["BFP"]-prv_BVid)) != 1:
        if dif == 0:
            L.logger.warning(f"No ball velocity packages in Unity")
        else:
            L.logger.warning(f"BallVel package IDs between frames discontinuous; "
                             f"gap was {dif}")

def _save_package_set(package_buf, full_fname, key):
    # write package buffer to hdf_file
    df = pd.DataFrame(package_buf)
    L.logger.debug(f"saving to hdf5:\n{df.to_string()}")
    try:
        df.to_hdf(full_fname, key=key, mode='a', append=True, format="table")
    except ValueError as e:
        L.logger.error(f"Error saving to hdf5:\n{e}\n\n{df.to_string()}")

def _log(termflag_shm, unityout_shm, paradigm_running_shm, full_fname):
    L = Logger()
    L.logger.info("Reading Unity packges from SHM and saving them...")

    package_buf = []
    prv_id, prv_BVid = -1, -1
    nchecks = 1
    package_buf_size = 32
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            if package_buf:
                _save_package_set(package_buf, full_fname, key="unityframes")
            break
        if not paradigm_running_shm.is_set():
            L.logger.debug("Paradigm stopped, on halt....")
            continue
        
        if unityout_shm.usage == 0:
            nchecks += 1
            sleep(0.001)
            continue
        nchecks = 1 # reset
        
        if unityout_shm.usage > 0:
            unity_package = unityout_shm.popitem(return_type=dict)
            L.logger.debug(f"after {nchecks} SHM checks found unity package:"
                           f"\n\t{unity_package}")

            # trial data is directly saved to the trialPackages key
            if unity_package["N"] == "T":
                _save_package_set([unity_package], full_fname, key="trialPackages")
                
            # frame packages are save to a buffer, come at 60 Hz
            elif unity_package["N"] == "U":
                _check_package(unity_package, prv_id, prv_BVid) # check for ID discontinuity
                prv_id = unity_package["ID"]
                prv_BVid = unity_package["BLP"]
                package_buf.append(unity_package)

        if len(package_buf) >= package_buf_size:
            _save_package_set(package_buf, full_fname, key="unityframes")
            package_buf.clear()
        
        L.logger.debug((f"Packs in unity output SHM: {unityout_shm.usage}"))
        L.spacer("debug")
        nchecks = 1

def run_log_unity(termflag_shm_struc_fname, unityoutput_shm_struc_fname, 
                  paradigmflag_shm_struc_fname, session_data_dir):
    # shm access
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    unityout_shm = CyclicPackagesSHMInterface(unityoutput_shm_struc_fname)
    paradigm_running_shm = FlagSHMInterface(paradigmflag_shm_struc_fname)

    while not paradigm_running_shm.is_set():
        # arduino pauses 1000ms, at some point in this inveral (between 0 and 500ms)
        # the logger wakes up - but there are no packages coming from the arudino 
        # yet bc it's still in wait mode. Ensures that we get first pack
        sleep(.5) # 500ms 
        L.logger.debug("Waiting for paradigm flag to be raised...")  
        L.logger.debug(f"Usage: {unityout_shm.usage}")  
        
    unityout_shm.reset_reader()
    L.logger.info(f"Paradigm flag raised. unityout shm usage: "
                  f"{unityout_shm.usage} - Starting to save data...")

    full_fname = os.path.join(session_data_dir, "unity_output.hdf5")
    with pd.HDFStore(full_fname) as hdf:
        hdf.put('unityframes', pd.DataFrame(), format='table', append=False)
        hdf.put('trialPackages', pd.DataFrame(), format='table', append=False)

    _log(termflag_shm, unityout_shm, paradigm_running_shm, full_fname)

if __name__ == "__main__":
    descr = ("Write Unity packages from SHM to a file.")
    argParser = argparse.ArgumentParser(descr)
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--unityoutput_shm_struc_fname")
    argParser.add_argument("--paradigmflag_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--process_prio", type=int)
    argParser.add_argument("--session_data_dir")
    # argParser.add_argument("--trial_package_variables")

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    L.logger.debug(L.fmtmsg(kwargs))
    
    prio = kwargs.pop("process_prio")
    if sys.platform.startswith('linux'):
        if prio != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')

    run_log_unity(**kwargs)

    # <{N:U,ID:1038,PCT:63846526825643413,X:0,Z:0.006149074,A:0.1225071,S:dummyState,BFP:0,BLP:0}>