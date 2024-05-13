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

def _check_package(ard_package, last_pack_id):
    # check if no package was skipped (cont. IDs)
    if (prv_id := last_pack_id.get(ard_package["N"])) is not None:
        if (dif := (ard_package["ID"]-prv_id)) != 1:
            L.logger.warning(f"Package ID discontinuous; gap was {dif}")
    # update dict with previous ID (specific for each package type/ "N")
    last_pack_id[ard_package["N"]] = ard_package["ID"]

    if ard_package["T"] < 0:
        L.logger.warning("Portenta timestamp was negative - Reset?")
    return last_pack_id

def _process_ballvell_package(ard_package):
    ryp_values = [int(val) for val in ard_package["V"].split("_")]
    ard_package["Vr"] = ryp_values[0]
    ard_package["Vy"] = ryp_values[1]
    ard_package["Vp"] = ryp_values[2]
    ard_package.pop("V")
    return ard_package

def _save_package_set(package_buf, full_fname, key):
    # write package buffer to hdf_file
    df = pd.DataFrame(package_buf)
    L.logger.debug(f"saving to hdf5:\n{df.to_string()}")
    try:
        df.to_hdf(full_fname, key=key, mode='a', append=True, format="table")
    except ValueError as e:
        L.logger.error(f"Error saving to hdf5:\n{e}\n\n{df.to_string()}")

def _log(termflag_shm, ballvel_shm, portentaout_shm, full_fname):
    L = Logger()
    L.logger.info("Reading Portenta packges from SHM and saving them...")

    package_buf = []
    poutputpackage_buf = []
    last_pack_id = {}
    nchecks = 1
    package_buf_size = 256
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            if package_buf:
                _save_package_set(package_buf, full_fname, "ballvelocity")
            if poutputpackage_buf:
                _save_package_set(poutputpackage_buf, full_fname, "portentaoutput")
            sleep(.5)
            break
        
        if portentaout_shm.usage > 0:
            portentaoutput_package = portentaout_shm.popitem(return_type=dict)
            poutputpackage_buf.append(portentaoutput_package)
        else:
            nchecks += 1
            continue
            
        if ballvel_shm.usage > 0:
            ballvel_package = ballvel_shm.popitem(return_type=dict)
            ballvel_package = _process_ballvell_package(ballvel_package)
            last_pack_id = _check_package(ballvel_package, last_pack_id)
            package_buf.append(ballvel_package)
        # if ard_package == "":
        #     # check for unexpected error cases when reading from SHM
        #     L.logger.error("Empty package!")
        #     continue
        
        # general outputs comes much less frequently, always save directly
        # else:
        #     _save_package_set([ard_package], full_fname, "portentaoutput")

        # L.logger.debug(f"after {nchecks} SHM checks logging package:\n\t{ard_package}")
        if len(package_buf) >= package_buf_size:
            _save_package_set(package_buf, full_fname, "ballvelocity")
            package_buf.clear()
        if len(portentaoutput_package) >= package_buf_size:
            _save_package_set(package_buf, full_fname, "portentaoutput")
            package_buf.clear()
            
        L.logger.debug((f"Packs in ballvel SHM: {ballvel_shm.usage}, in "
                        f"portentaout SHM: {portentaout_shm.usage}"))
        L.spacer("debug")
        nchecks = 1

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
    
    if sys.platform.startswith('linux'):
        if (prio := kwargs.pop("process_prio")) != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')
    run_log_portenta(**kwargs)