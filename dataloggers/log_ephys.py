import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import pandas as pd

import argparse
from time import sleep
import time
from CustomLogger import CustomLogger as Logger
from FlagSHMInterface import FlagSHMInterface

import maxlab as mx


def _log(termflag_shm, paradigm_running_shm, session_data_dir, fname, use_legacy_format):
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
            if use_legacy_format:
                s.set_legacy_format(True)
            else:
                s.set_legacy_format(False)

            s.open_directory(session_data_dir)
            s.start_file(fname)
            s.group_delete_all()
            s.group_define(0, "all_channels", list(range(1024)))
            is_recording = True
            L.logger.debug("Successfully opened file and defined group. Starting recording...")
    
            s.start_recording(recording_wells)

def _reset_MEA1K(gain, enable_stimulation_power=False):
    L = Logger()
    L.logger.info(f"Initialize MEA1K and set gain of {gain}")
    mx.util.initialize()
    if enable_stimulation_power:
        mx.send(mx.chip.Core().enable_stimulation_power(True))
    mx.send(mx.chip.Amplifier().set_gain(gain))

def _animal_name2implant_device(nas_dir, animal_name):
    fullfname = os.path.join(nas_dir, 'devices', 'implant_to_animal_map.csv')
    mapping = pd.read_csv(fullfname, index_col=0, header=0)
    Logger().logger.debug(f"Animal->Implant map:\n{mapping}")
    if animal_name in mapping.index:
        return mapping.loc[animal_name].item()
    else:
        raise ValueError(f"No implant name found for `{animal_name}` Add to the "
                         f"mapping manually: {fullfname}")
    
def run_log_ephys(termflag_shm_struc_fname, paradigmflag_shm_struc_fname,
                  session_data_dir, nas_dir, maxwell_config_of_animal, gain, use_legacy_format):
    L = Logger()
    # shm access
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    paradigm_running_shm = FlagSHMInterface(paradigmflag_shm_struc_fname)
    
    # implant_name = [f.replace("implanted_", "") for f in os.listdir(which_implant_path) 
    #                 if f.startswith("implanted_")]
    # if not implant_name:
    #     L.logger.error(f"No implant found at {which_implant_path} - not "
    #                    "changing configuration.")
    # else:
    #     implant_name = implant_name[0]
    #                                     implant_name, 'bonding', 
    #                                     f"bonding_mapping_{implant_name}.cfg")
    #     L.logger.info(f"Placeholder for config setting {config_fullfname}")
        # _reset_MEA1K(gain, enable_stimulation_power=False)
        # array = mx.chip.Array()
        # array.load_config(config_fullfname)
        # L.logger.info(f"Successfully loaded configuration from {config_fullfname}")
    config_fullfname = os.path.join(nas_dir, 'mea1k_configs', 'all_parallel', 'el_001.cfg')
    if not os.path.exists(config_fullfname):
        raise FileNotFoundError(f"MEA1K configuration file not found at {config_fullfname}")
    _reset_MEA1K(gain, enable_stimulation_power=False) 
        
        
    while not paradigm_running_shm.is_set():
        # arduino pauses 1000ms, at some point in this inveral (between 0 and 500ms)
        # the logger wakes up - but there are no packages coming from the arudino 
        # yet bc it's still in wait mode. Ensures that we get first pack
        sleep(.5) # 500ms 
        L.logger.debug("Waiting for paradigm flag to be raised...")  
        
    current_time = int(time.time()*1e6)
    L.logger.info(f"Paradigm flag raised at {current_time}. Starting to log ephys data now...")

    _log(termflag_shm, paradigm_running_shm, session_data_dir, fname="ephys_output", 
         use_legacy_format=use_legacy_format)

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
    argParser.add_argument("--nas_dir")
    argParser.add_argument("--maxwell_config_of_animal")
    argParser.add_argument("--gain")
    argParser.add_argument("--use_legacy_format", type=int)

    kwargs = vars(argParser.parse_args())
    kwargs['use_legacy_format'] = bool(kwargs['use_legacy_format'])
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    L.logger.debug(L.fmtmsg(kwargs))
    L.logger.debug(kwargs['use_legacy_format'])
    L.logger.debug(type(kwargs['use_legacy_format']))
    
    prio = kwargs.pop("process_prio")
    if sys.platform.startswith('linux'):
        if prio != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')

    run_log_ephys(**kwargs)