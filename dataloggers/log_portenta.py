import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import argparse
from time import sleep
import pandas as pd

from CustomLogger import CustomLogger as Logger
from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _check_package(ballvel_pack, last_ballvel_pack_id):
    # check if no package was skipped (cont. IDs)
    if (prv_id := last_ballvel_pack_id.get(ballvel_pack["N"])) is not None:
        if (dif := (ballvel_pack["ID"]-prv_id)) != 1:
            L.logger.warning(f"Package ID discontinuous; gap was {dif}")
    # update dict with previous ID (specific for each package type/ "N")
    last_ballvel_pack_id[ballvel_pack["N"]] = ballvel_pack["ID"]

    if ballvel_pack["T"] < 0:
        L.logger.warning("Portenta timestamp was negative - Reset?")
    return last_ballvel_pack_id

def _process_ballvell_package(ballvel_pack):
    ryp_values = [int(val) for val in ballvel_pack["V"].split("_")]
    ballvel_pack["Vr"] = ryp_values[0]
    ballvel_pack["Vy"] = ryp_values[1]
    ballvel_pack["Vp"] = ryp_values[2]
    ballvel_pack.pop("V")
    return ballvel_pack

def _save_package_set(ballvel_packages, full_fname, key):
    # write package buffer to hdf_file
    df = pd.DataFrame(ballvel_packages)
    L.logger.debug(f"saving to hdf5:\n{df.to_string()}")
    try:
        df.to_hdf(full_fname, key=key, mode='a', append=True, format="table")
    except ValueError as e:
        L.logger.error(f"Error saving to hdf5:\n{e}\n\n{df.to_string()}")

def _log(termflag_shm, ballvel_shm, portentaout_shm, full_fname):
    L = Logger()
    L.logger.info("Reading Portenta packges from SHM and saving them...")

    ballvel_packages = []
    # poutputpackage_buf = []
    last_ballvel_pack_id = {}
    nchecks = 1 # for logging
    package_buf_size = 256 # save every 256 ball vel packages
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            if ballvel_packages:
                _save_package_set(ballvel_packages, full_fname, "ballvelocity")
            sleep(.5)
            break
        
        if (ballvel_shm.usage == 0) and (portentaout_shm.usage == 0):
            nchecks += 1
            continue
        nchecks = 1 # reset
        
        # coming at about 1300Hz, save in buffer
        if ballvel_shm.usage > 0:
            ballvel_pack = ballvel_shm.popitem(return_type=dict)
            ballvel_pack = _process_ballvell_package(ballvel_pack)
            last_ballvel_pack_id = _check_package(ballvel_pack, last_ballvel_pack_id)
            ballvel_packages.append(ballvel_pack)
        L.logger.debug(f"after {nchecks} SHM checks logging package:\n\t{ballvel_pack}")
            
        # sparse events, save directly
        if portentaout_shm.usage > 0:
            portentaoutput_package = portentaout_shm.popitem(return_type=dict)
            _save_package_set([portentaoutput_package], full_fname, "portentaoutput")

        # save every 256 ball vel packages
        if len(ballvel_packages) >= package_buf_size:
            _save_package_set(ballvel_packages, full_fname, "ballvelocity")
            ballvel_packages.clear()
            
        L.logger.debug((f"Packs in ballvel SHM: {ballvel_shm.usage}, in "
                        f"portentaout SHM: {portentaout_shm.usage}"))
        L.spacer("debug")

def run_log_portenta(termflag_shm_struc_fname, ballvelocity_shm_struc_fname, 
                     portentaoutput_shm_struc_fname, session_data_dir):
    # shm access
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    ballvel_shm = CyclicPackagesSHMInterface(ballvelocity_shm_struc_fname)
    portentaout_shm = CyclicPackagesSHMInterface(portentaoutput_shm_struc_fname)

    full_fname = os.path.join(session_data_dir, "portenta_output.hdf5")
    with pd.HDFStore(full_fname) as hdf:
        hdf.put('ballvelocity', pd.DataFrame(), format='table', append=False)
        hdf.put('portentaoutput', pd.DataFrame(), format='table', append=False)
    
    _log(termflag_shm, ballvel_shm, portentaout_shm, full_fname)

if __name__ == "__main__":
    descr = ("Write Portenta packages from SHM to a file.")
    argParser = argparse.ArgumentParser(descr)
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--ballvelocity_shm_struc_fname")
    argParser.add_argument("--portentaoutput_shm_struc_fname")
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

    run_log_portenta(**kwargs)