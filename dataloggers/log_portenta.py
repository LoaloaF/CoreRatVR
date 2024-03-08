import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import pandas as pd
import argparse

from CustomLogger import CustomLogger as Logger

from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _log_sensors(termflag_shm, ballvelocity_shm, portentaoutput_shm, full_fname):
    L = Logger()
    L.logger.info("Reading packges from SHM and saving it...")

    package_buf = []
    last_pack_id = {}
    while True:        
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            break
        
        # get a package if there are more than 10
        if ballvelocity_shm.usage <= 1:
            continue
        ard_package = ballvelocity_shm.bpopitem()
        
        # TO DO
        # ard_package = portentaoutput_shm.bpopitem()
        
        # check for error cases
        if ard_package is None:
            L.logger.warning("Package was None, reading too fast")
        elif ard_package == "":
            L.logger.error("Empty string package!")
        
        else:
            # check if no package was skipped (cont. IDs)
            if (prv_id := last_pack_id.get(ard_package["N"])) is not None:
                if (dif := (ard_package["ID"]-prv_id)) != 1:
                    L.logger.warning(f"Package ID discontinuous; gap was {dif}")
            # update dict with previous ID (specific for each package type/ "N")
            last_pack_id[ard_package["N"]] = ard_package["ID"]

            # if ard_package["N"] in ("S", "R", "F", "L", c"P"):
            #     ard_package["V"] = str(ard_package["V"])
            
            if ard_package["N"] == "B":
                ryp_values = [int(val) for val in ard_package["V"].split("_")]
                ard_package["V"] = max([abs(v) for v in ryp_values])
                ard_package["Vr"] = ryp_values[0]
                ard_package["Vy"] = ryp_values[1]
                ard_package["Vp"] = ryp_values[2]

            if ard_package["T"] < 0:
                L.logger.warning("Portenta timestamp was negative - Reset?")

            # append to buffer and save to file every 256 elements
            package_buf.append(ard_package)
            L.logger.debug(f"logging package: {ard_package}")
            if len(package_buf) >= 256:
                # write package buffer to hdf_file
                df = pd.DataFrame(package_buf)#.reset_index(drop=True).set_index("ID")
                L.logger.debug(f"saving to hdf5:\n{df.to_string()}")
                df.to_hdf(full_fname, key='arduino_packages', mode='a', 
                          append=True, format="table")
                package_buf.clear()
        
        L.logger.debug(f"Packs in SHM: {ballvelocity_shm.usage}")
        L.spacer("debug")


def run_log_portenta(termflag_shm_struc_fname, ballvelocity_shm_struc_fname, 
                     portentaoutput_shm_struc_fname, session_data_dir):
    # shm access
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    ballvelocity_shm = CyclicPackagesSHMInterface(ballvelocity_shm_struc_fname)
    portentaoutput_shm = CyclicPackagesSHMInterface(portentaoutput_shm_struc_fname)

    full_fname = os.path.join(session_data_dir, "data.hdf5")
    # check if the file exists and create it if necessary
    if os.path.exists(full_fname):
        os.remove(full_fname)
    with pd.HDFStore(full_fname) as hdf:
        hdf.put('arduino_packages', pd.DataFrame(), format='table', append=False)
    
    _log_sensors(termflag_shm, ballvelocity_shm, portentaoutput_shm, full_fname)

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