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
from streamer.display_packages import run_stream_packages

from process_launcher import open_por2shm2por_proc
from process_launcher import open_log_portenta_proc
from process_launcher import open_stream_portenta_proc
from process_launcher import open_por2shm2por_sim_proc


# from streamer.display_camera import run_display_camera

def test_portenta2shm2portenta(P):
    L = Logger()
    # setup the main logitech stream
    if P.ARDUINO_PORT not in [p for p,v in P.ARDUINO_BY_PORT.items() if v == 'Working']:
        L.logger.error(f"Port {P.ARDUINO_PORT} has no working Arudino connected")
        exit(1)
    
    # setup termination, triggered by input from here
    termflag_shm_struc_fname = create_singlebyte_shm(shm_name="termflag")
    # setup commands to Portenta, triggered by input from here
    command_shm_struc_fname = create_cyclic_packages_shm(shm_name="CommandCyclicTestSHM", 
                                                         package_nbytes=32, 
                                                         npackages=8)
    
    # setup main camera one shared memory
    sensors_shm_struc_fname = create_cyclic_packages_shm(shm_name="SensorsCyclicTestSHM", 
                                                         package_nbytes=128, 
                                                         npackages=int(2**13)) # 8MB
    
    portenta2shm_kwargs = {
        "shm_structure_fname": sensors_shm_struc_fname,
        "termflag_shm_structure_fname": termflag_shm_struc_fname,
        "command_shm_structure_fname": command_shm_struc_fname,
        "port_name": P.ARDUINO_PORT,
        "baud_rate": P.ARDUINO_BAUD_RATE,
        }
    log_portenta_kwargs = portenta2shm_kwargs.copy()
    log_portenta_kwargs.pop("command_shm_structure_fname")
    log_portenta_kwargs.pop("port_name")
    log_portenta_kwargs.pop("baud_rate")
    stream_portenta_kwargs = log_portenta_kwargs.copy()
    log_portenta_kwargs["data_dir"] = P.DATA_DIRECTORY

    L.spacer()
    if P.USE_MULTIPROCESSING:
        stream_portenta_proc = open_stream_portenta_proc(logging_name="stream_portenta", 
                                                      **stream_portenta_kwargs)
        time.sleep(2)
        # log_portenta_proc = open_log_portenta_proc(logging_name="log_portenta", 
        #                                            **log_portenta_kwargs)
        # time.sleep(2)
        por2shm2por_proc = open_por2shm2por_sim_proc(logging_name="por2shm2por", 
                                                 **portenta2shm_kwargs)
        time.sleep(2)
        por2shm2por_proc = open_por2shm2por_proc(logging_name="por2shm2por", 
                                                 **portenta2shm_kwargs)
        time.sleep(2)
        
    else:
        Thread(target=run_portenta2shm2portenta, kwargs=portenta2shm_kwargs).start()
        Thread(target=run_log_portenta, kwargs=log_portenta_kwargs).start()
        Thread(target=run_stream_packages, kwargs=stream_portenta_kwargs).start()
    
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    command_shm = CyclicPackagesSHMInterface(command_shm_struc_fname)
    
    while True:
        t = time.time()
        if t-int(t) < 0.001:
            break
    try:
        i = 0
        while True:
            # inp = input("q to quit, or send command to Portenta")
            # if inp == "q":
            #     L.spacer()
            #     termflag_shm.set()
            #     exit()    
            t1 = time.time()
            if t1 > t+i:
                command_shm.push("S100,100\r\n")
                L.logger.info("Pushed")
                i += 5
            
            # if t1 > t+10.8:
            #     raise KeyboardInterrupt

    except KeyboardInterrupt:
        L.spacer()
        termflag_shm.set()
        exit()

    #  while True:
    #     inp = input("q to quit, or send command to Portenta")
    #     if inp == "q":
    #         L.spacer()
    #         termflag_shm.set()
    #         exit()
    #     else:
    #         L.logger.info(inp)
    #         # time.sleep(2)
    #         # command_shm.push("Y100,100,100")
    #         command_shm.push(inp)



def main():
    P = Parameters()
    
    # manually update params here
    P.USE_MULTIPROCESSING = True
    P.LOGGING_LEVEL = logging.INFO
    # P.LOGGING_LEVEL = logging.DEBUG
    
    if P.SYSTEM == "Linux":
        P.ARDUINO_PORT = "/dev/ttyACM0"
        P.ARDUINO_BY_PORT = {"/dev/ttyACM0": "Working"}
        P.DATA_DIRECTORY = "~/"
    else:
        P.ARDUINO_PORT = "COM3"
        P.ARDUINO_BY_PORT = {"COM3": "Working"}
        P.DATA_DIRECTORY = "c://Users//RatVR//"

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
    
    # overhang packge when term flag raised nooed to be looged (partial 256)
    # timestamps of buffered packages should be set to inital read event timestamp
    # benchmark max read rate, dial in, test on high perf Linux machine