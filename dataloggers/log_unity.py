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

def check_package(package, prv_id, prv_BVid):
    # check for ID discontinuity
    if (dif := (package["ID"]-prv_id)) != 1:
        L.logger.warning(f"Frame Package ID discontinuous; gap was {dif}")
    
    if (dif := (package["BFP"]-prv_BVid)) != 1:
        L.logger.warning(f"BallVel package IDs between frames discontinuous; "
                         f"gap was {dif}")

def _save_package_set(package_buf, full_fname, key):
    # write package buffer to hdf_file
    df = pd.DataFrame(package_buf)
    L.logger.debug(f"saving to hdf5:\n{df.to_string()}")
    try:
        df.to_hdf(full_fname, key=key, mode='a', 
                  append=True, format="table")
    except ValueError as e:
        L.logger.error(f"Error saving to hdf5:\n{e}\n\n{df.to_string()}")

def _log(termflag_shm, unityout_shm, full_fname):
    L = Logger()
    L.logger.info("Reading Unity packges from SHM and saving them...")

    package_buf = []
    prv_id = -1
    prv_BVid = -1
    nchecks = 1
    package_buf_size = 32
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            if package_buf:
                _save_package_set(package_buf, full_fname, key="unityframes")
            sleep(.5)
            break
        
        if unityout_shm.usage > 0:
            unity_package = unityout_shm.popitem(return_type=dict)
        else:
            nchecks += 1
            sleep(0.001)
            continue
        if unity_package == "":
            # check for unexpected error cases when reading from SHM
            L.logger.error("Empty package!")
            continue

        L.logger.debug(unity_package)
        if unity_package["N"] == "TN":
            _save_package_set([unity_package], full_fname, key="trialstarts")
        
        elif unity_package["N"] == "TE":
            _save_package_set([unity_package], full_fname, key="trialends")
            
        elif unity_package["N"] == "U":
            # check for ID discontinuity
            check_package(unity_package, prv_id, prv_BVid)
            # unity_package.pop("N")

            # append to buffer and save to file every 256 elements
            package_buf.append(unity_package)

            if len(package_buf) >= package_buf_size:
                _save_package_set(package_buf, full_fname, key="unityframes")
                package_buf.clear()
            L.logger.debug((f"Packs in unity output SHM: {unityout_shm.usage}"))
            prv_id = unity_package["ID"]
            prv_BVid = unity_package["BLP"]
        L.spacer("debug")
        L.logger.debug(f"after {nchecks} SHM checks logging package:\n\t{unity_package}")
        nchecks = 1

def run_log_unity(termflag_shm_struc_fname, unityoutput_shm_struc_fname, 
                  session_data_dir, paradigm_pillar_types):
    # shm access
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    unityout_shm = CyclicPackagesSHMInterface(unityoutput_shm_struc_fname)

    full_fname = os.path.join(session_data_dir, "unity_output.hdf5")
    with pd.HDFStore(full_fname) as hdf:
        df = pd.DataFrame(columns=["N","ID","PCT","X","Z","A","S","FB","BFP","BLP"],index=[])
        print(df)
        hdf.put('unityframes', df, format='table', append=False)
        
        # trial start packages have information about pillar types
        print(paradigm_pillar_types)
        if ',' in paradigm_pillar_types:
            pillar_cols = [el for p in paradigm_pillar_types.split(",") 
                        for el in (f"P{p}R", f"P{p}T", f"P{p}P")]
        else:
            pillar_cols = []
        df = pd.DataFrame(columns=["N", "ID", "FID", "PCT", *pillar_cols], index=[])
        print(df)
        hdf.put('trialstarts', df, format='table', append=False)
        
        df = pd.DataFrame(columns=["N","ID","FID","PCT","TD","P"], index=[])
        print(df)
        hdf.put('trialends', df, format='table', append=False)
    _log(termflag_shm, unityout_shm, full_fname)

if __name__ == "__main__":
    descr = ("Write Unity packages from SHM to a file.")
    argParser = argparse.ArgumentParser(descr)
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--unityoutput_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--process_prio", type=int)
    argParser.add_argument("--session_data_dir")
    argParser.add_argument("--paradigm_pillar_types")

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    
    if sys.platform.startswith('linux'):
        if (prio := kwargs.pop("process_prio")) != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')
    run_log_unity(**kwargs)

    # <{N:U,ID:1038,PCT:63846526825643413,X:0,Z:0.006149074,A:0.1225071,S:dummyState,BFP:0,BLP:0}>