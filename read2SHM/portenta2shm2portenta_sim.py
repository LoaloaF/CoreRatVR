import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import time
import argparse

import numpy as np

from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from FlagSHMInterface import FlagSHMInterface

from CustomLogger import CustomLogger as Logger

V_ID = 0
L_ID = 0
S_ID = 0
F_ID = 0
R_ID = 0
P_ID = 0

Vr = 0
Vy = 0
Vp = 0

def generate_test_package():
    global V_ID
    global L_ID
    global S_ID
    global F_ID
    global R_ID
    global P_ID
    global Vr
    global Vy
    global Vp
    num = np.random.rand()
    if num <.95:
        N = "B"
        V_ID += 1
        ID = V_ID
        Vr += int(0.1*np.random.randn()*-100)
        Vy += int(0.1*np.random.randn()*100)
        Vp += int(0.1*np.random.randn()*100)
        V = f"{Vr}_{Vy}_{Vp}"
    elif num <.98:
        N = "L"
        L_ID += 1
        ID = L_ID
        V = 1
    elif num <.983:
        N = "S"
        S_ID += 1
        ID = S_ID
        V = 1
    elif num <.986:
        N = "F"
        F_ID += 1
        ID = F_ID
        V = 1
    elif num <.99:
        N = "R"
        R_ID += 1
        ID = R_ID
        V = 1
    else:
        N = "P"
        P_ID += 1
        ID = P_ID
        V = 1
    
    T = int(time.perf_counter()*1e6)
    F = int(np.random.rand()>.2)

    pack = "<{" + f"N:{N},ID:{ID},T:{T},PCT:{T},V:{V},F:{F}" + "}>\r\n"
    return pack, N

def _handle_input(ballvel_shm, portentaoutput_shm):
    pack, name = generate_test_package()
    if name == "B":
        ballvel_shm.bpush(pack.encode())
    else:
        portentaoutput_shm.bpush(pack.encode())
    return 

def _read_write_loop(termflag_shm, ballvel_shm, portentaoutput_shm):
    L = Logger()
    L.logger.info("Reading serial port packages & writing to SHM...")
    L.logger.info("Reading command packages from SHM & writing to serial port...")
    
    t0 = time.perf_counter()*1e6
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            break
        
        # check for incoming packages on serial port, timestamp and write shm
        # buf and timestamp are stateful, relevant for consecutive serial checks 
        _handle_input(ballvel_shm, portentaoutput_shm)
        while True:
            dt = time.perf_counter()*1e6-t0
            if dt > 500:
                t0 = time.perf_counter()*1e6
                if dt > 1000:
                    L.logger.warning(f"slow - dt: {dt}")
                break


def run_portenta2shm2portenta_sim(termflag_shm_struc_fname, ballvelocity_shm_struc_fname, 
                                  portentaoutput_shm_struc_fname):
    # shm access
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    ballvel_shm = CyclicPackagesSHMInterface(ballvelocity_shm_struc_fname)
    portentaoutput_shm = CyclicPackagesSHMInterface(portentaoutput_shm_struc_fname)

    _read_write_loop(termflag_shm, ballvel_shm, portentaoutput_shm)

if __name__ == "__main__":
    descr = ("Read incoming Portenta packages, timestamp and place in SHM. Also"
             " read command packages from SHM and send them back to Portenta.")
    argParser = argparse.ArgumentParser(descr)
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--ballvelocity_shm_struc_fname")
    argParser.add_argument("--portentaoutput_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--process_prio", type=int)

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    
    if sys.platform.startswith('linux'):
        if (prio := kwargs.pop("process_prio")) != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')
    run_portenta2shm2portenta_sim(**kwargs)