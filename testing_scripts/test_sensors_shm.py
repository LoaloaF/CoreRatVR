import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM'))

import time
import logging
from threading import Thread

from CustomLogger import CustomLogger as Logger
from Parameters import Parameters

# from process_launcher import open_camera2shm_proc
# from process_launcher import open_shm2cam_stream_proc
from SHM.shm_creation import create_cyclic_packages_shm
from SHM.shm_creation import create_singlebyte_shm

from FlagSHMInterface import FlagSHMInterface
from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface

from read2SHM.portenta2shm2portenta import run_portenta2shm2portenta
from dataloggers.log_portenta import run_log_portenta
from process_launcher import open_por2shm2por_proc
from process_launcher import open_log_portenta_proc
# from streamer.display_camera import run_display_camera

def test_portenta2shm2portenta(P):
    L = Logger()
    # setup the main logitech stream
    if P.PORTENTA_PORT not in [p for p,v in P.ARDUINO_BY_PORT.items() if v == 'Working']:
        L.logger.error(f"Port {P.PORTENTA_PORT} has no working Arudino connected")
        exit(1)
    
    # setup termination, triggered by input from here
    termflag_shm_struc_fname = create_singlebyte_shm(shm_name="termflag")
    # setup commands to Portenta, triggered by input from here
    command_shm_struc_fname = create_cyclic_packages_shm(shm_name="CommandCyclicTestSHM", 
                                                         package_nbytes=256, 
                                                         npackages=8)
    
    # setup main camera one shared memory
    sensors_shm_struc_fname = create_cyclic_packages_shm(shm_name="SensorsCyclicTestSHM", 
                                                         package_nbytes=128, 
                                                         npackages=4096)
    
    portenta2shm_kwargs = {
        "shm_structure_fname": sensors_shm_struc_fname,
        "termflag_shm_structure_fname": termflag_shm_struc_fname,
        "command_shm_structure_fname": command_shm_struc_fname,
        "port_name": P.PORTENTA_PORT,
        "baud_rate": P.PORTENTA_BAUD_RATE,
        }
    log_portenta_kwargs = portenta2shm_kwargs.copy()
    log_portenta_kwargs.pop("command_shm_structure_fname")
    log_portenta_kwargs.pop("port_name")
    log_portenta_kwargs.pop("baud_rate")
    log_portenta_kwargs["data_dir"] = P.DATA_DIRECTORY

    L.spacer()
    if P.USE_MULTIPROCESSING:
        por2shm2por_proc = open_por2shm2por_proc(logging_name="por2shm2por", 
                                                 **portenta2shm_kwargs)
        log_portenta_proc = open_log_portenta_proc(logging_name="log_portenta", 
                                                   **log_portenta_kwargs)
        
    else:
        Thread(target=run_portenta2shm2portenta, kwargs=portenta2shm_kwargs).start()
        Thread(target=run_log_portenta, kwargs=log_portenta_kwargs).start()
    
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    command_shm = CyclicPackagesSHMInterface(command_shm_struc_fname)
    
    while True:
        inp = input("q to quit, or send command to Portenta")
        if inp == "q":
            L.spacer()
            termflag_shm.set()
            exit()
        else:
            L.logger.info(inp)
            command_shm.push(inp)

def main():
    P = Parameters()
    
    # manually update params here
    P.USE_MULTIPROCESSING = True
    P.LOGGING_LEVEL = logging.WARNING
    P.LOGGING_LEVEL = logging.DEBUG
    
    if P.SYSTEM == "Linux":
        P.PORTENTA_PORT = "/dev/ttyACM0"
    else:
        P.PORTENTA_PORT = "COM3"

    L = Logger()
    logging_sub_dir = L.init_logger(__name__, P.LOGGING_DIRECTORY, 
                                    P.LOGGING_LEVEL, True)
    P.LOGGING_DIRECTORY_RUN = logging_sub_dir
    
    L.spacer()
    L.logger.info(L.fmtmsg(["Parameters", str(P)]))
    L.spacer()
    L.logger.info("Testing Portenta/Sensors SHM read and write")
    test_portenta2shm2portenta(P)

if __name__ == "__main__":
    main()