import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import argparse
from time import sleep
import time
from CustomLogger import CustomLogger as Logger
from FlagSHMInterface import FlagSHMInterface

import maxlab as mx


def _log(termflag_shm, paradigm_running_shm, session_data_dir, fname):
    L = Logger()
    L.logger.info("Saving ephys data to hdf5...")

    s = mx.Saving()
    recording_wells = [0]
    is_recording = False
    portenta_start_stop_flag = False
    portenta_start_stop_pct = 0
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            return
        
        current_time = int(time.time()*1e6)  
        if not paradigm_running_shm.is_set():
            if not portenta_start_stop_flag:
                L.logger.info(f"Paradigm start not running at {current_time}, on halt....")
                portenta_start_stop_flag = True
                portenta_start_stop_pct = int(time.time()*1e6)
            elif current_time-portenta_start_stop_pct > 1000000:            
                L.logger.debug("Paradigm not running, on halt....")
                # if the flag is not raised, and we are recording, stop recording
                if is_recording:
                    L.logger.debug("Paradigm not running, stopping recording...")
                    s.stop_recording()
                    s.stop_file()
                    s.group_delete_all()
                    is_recording = False
        
        # if the flag is raised, and we are noot already recording, start recording
        elif not is_recording:        
            s.open_directory(session_data_dir)
            s.start_file(fname)
            s.group_delete_all()
            s.group_define(0, "all_channels", list(range(1024)))
            is_recording = True
            L.logger.debug("Successfully opened file and defined group. Starting recording...")
    
            s.start_recording(recording_wells)


def run_log_ephys(termflag_shm_struc_fname, paradigmflag_shm_struc_fname,
                  session_data_dir):
    L = Logger()
    # shm access
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    paradigm_running_shm = FlagSHMInterface(paradigmflag_shm_struc_fname)

    while not paradigm_running_shm.is_set():
        # arduino pauses 1000ms, at some point in this inveral (between 0 and 500ms)
        # the logger wakes up - but there are no packages coming from the arudino 
        # yet bc it's still in wait mode. Ensures that we get first pack
        sleep(.5) # 500ms 
        L.logger.debug("Waiting for paradigm flag to be raised...")  
        
    current_time = int(time.time()*1e6)
    L.logger.info(f"Paradigm flag raised at {current_time}. Starting to log ephys data now...")

    _log(termflag_shm, paradigm_running_shm, session_data_dir, fname="ephys_output")

if __name__ == "__main__":
    descr = ("Save electrophysiology data from measerver.")
    argParser = argparse.ArgumentParser(descr)
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--paradigmflag_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--process_prio", type=int)
    argParser.add_argument("--session_data_dir")

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    
    prio = kwargs.pop("process_prio")
    if sys.platform.startswith('linux'):
        if prio != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')

    run_log_ephys(**kwargs)