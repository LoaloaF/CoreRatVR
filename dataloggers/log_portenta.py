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

def _log_sensors(sensors_shm, termflag_shm, full_fname):
    L = Logger()
    L.logger.info("Reading packges from SHM and saving it...")

    package_buf = []
    last_pack_id = {}
    while True:        
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            break
        
        # get a package if there are more than 10
        if sensors_shm.usage < 10:
            continue
        ard_package = sensors_shm.bpopitem()
        
        # check for error cases
        if ard_package is None:
            L.logger.warning("Package was None, reading too fast")
        elif ard_package == "":
            L.logger.error("Empty string package!")
        
        else:
            # check if no package was skipped (cont. IDs)
            if (prv_id := last_pack_id.get(ard_package["N"])) is not None:
                if (dif := ard_package["ID"]-prv_id) != 1:
                    L.logger.error(f"Package ID discontinuous; gap was {dif}")
            # update dict with previous ID (specific for each package type/ "N")
            last_pack_id[ard_package["N"]] = ard_package["ID"]

            # append to buffer and save to file every 256 elements
            package_buf.append(ard_package)
            L.logger.debug(f"logging package: {ard_package}")
            if len(package_buf) >= 256:
                # write package buffer to hdf_file
                df = pd.DataFrame(package_buf).reset_index(drop=True).set_index("ID")
                df.to_hdf(full_fname, key='arduino_packages', mode='a', 
                          append=True, format="table")
                L.logger.debug(f"saving to hdf5:\n{df}")
                package_buf.clear()
        
        L.logger.debug(f"Packs in SHM: {sensors_shm.usage}")
        L.spacer("debug")


def run_log_portenta(shm_structure_fname, termflag_shm_structure_fname,
                     data_dir):
    # shm access
    sensors_shm = CyclicPackagesSHMInterface(shm_structure_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_structure_fname)

    full_fname = os.path.join(data_dir, "data.hdf5")
    _log_sensors(sensors_shm, termflag_shm, full_fname)

if __name__ == "__main__":
    descr = ("Write Portenta packages from SHM to a file.")
    argParser = argparse.ArgumentParser(descr)
    argParser.add_argument("--shm_structure_fname")
    argParser.add_argument("--termflag_shm_structure_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level", type=int)
    argParser.add_argument("--data_dir")

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    run_log_portenta(**kwargs)