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
A_ID = 0

Vr = 0
Vy = 0
Vp = 0

def _gen_package(N, ID, V):
    T = int(time.perf_counter()*1e6)
    F = int(np.random.rand()>.2)

    pack = "<{" + f"N:{N},ID:{ID},T:{T},PCT:{T},V:{V},F:{F}" + "}>\r\n"
    return pack, N

def gen_ballvel_package():
    global V_ID
    global Vr
    global Vy
    global Vp

    N = "B"
    V_ID += 1
    ID = V_ID
    Vr = int(0.8*Vr + 0.2*(np.random.randn()*20))     # move sideways (unity z)
    Vy = int(0.8*Vy + 0.2*(np.random.randn()*20))     # move forward (unity x)
    Vp = int(0.8*Vp + 0.2*(np.random.randn()*20))     # rotate (around unity y axis)
    V = f"{Vr}_{Vy}_{Vp}"
    return _gen_package(N, ID, V)

def gen_L_package():
    global L_ID
    L_ID += 1
    return _gen_package("L", L_ID, -int(np.random.randn()*100)) # length lick in ms into the past

def gen_A_package():
    global A_ID
    A_ID += 1
    return _gen_package("A", A_ID, 1)

def gen_S_package(v):
    global S_ID
    S_ID += 1
    return _gen_package("S", S_ID, v)  # -1 for failure, 1 for success sound

def gen_R_package():
    global R_ID
    R_ID += 1
    return _gen_package("R", R_ID, 1)

def gen_P_package():
    global P_ID
    P_ID += 1
    return _gen_package("P", P_ID, 1) # length punishment in ms

def _handle_portentaoutput(ballvel_shm, portentaoutput_shm):
    num = np.random.rand()
    if num < .995:
        ballvel_pack, _ = gen_ballvel_package()
        Logger().logger.debug(f"ballvel_pack: {ballvel_pack}")
        ballvel_shm.push(ballvel_pack.encode())
    else:
        lickpack, _ = gen_L_package()
        Logger().logger.debug(f"lickpack: {lickpack}")
        portentaoutput_shm.push(lickpack.encode())


def _handle_portentainput(portentaoutput_shm, portentainput_shm,):
    cmd = portentainput_shm.popitem(return_type=str)
    if cmd is not None:
        Logger().logger.info(f"cmd in SHM: `{cmd}` - Simulating write to serial.")
        
        which_cmd = cmd[0]
        values = cmd[1:].split(",")
        if which_cmd == "A":
            pack, _ = gen_A_package()
        if which_cmd == "P":
            pack, _ = gen_P_package()
        if which_cmd == "F": #ailure
            pack, _ = gen_S_package(v=-1) #sound
        if which_cmd == "S": #uccess
            pack, _ = gen_S_package(v=1) #sound
            portentaoutput_shm.push(pack.encode())
            Logger().logger.debug(f"feedbackpack: {pack}")
            pack, _ = gen_R_package() #reward/valve open
        Logger().logger.debug(f"feedbackpack: {pack}")

        portentaoutput_shm.push(pack.encode())

def _read_write_loop(termflag_shm, ballvel_shm, portentaoutput_shm,
                     portentainput_shm):
    L = Logger()
    L.logger.info("Reading serial port packages & writing to SHM...")
    L.logger.info("Reading command packages from SHM & writing to serial port...")
    
    t0 = time.perf_counter()*1e6
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            break

        _handle_portentainput(portentaoutput_shm, portentainput_shm)
        
        # check for incoming packages on serial port, timestamp and write shm
        # buf and timestamp are stateful, relevant for consecutive serial checks 
        _handle_portentaoutput(ballvel_shm, portentaoutput_shm)
        while True:
            dt = time.perf_counter()*1e6-t0
            if dt > 1250:
                t0 = time.perf_counter()*1e6
                if dt > 10000:
                    L.logger.warning(f"slow - dt: {dt}")
                break


def run_portenta2shm2portenta_sim(termflag_shm_struc_fname, ballvelocity_shm_struc_fname, 
                                  portentaoutput_shm_struc_fname, 
                                  portentainput_shm_struc_fname):
    # shm access
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    ballvel_shm = CyclicPackagesSHMInterface(ballvelocity_shm_struc_fname)
    portentaoutput_shm = CyclicPackagesSHMInterface(portentaoutput_shm_struc_fname)
    portentainput_shm = CyclicPackagesSHMInterface(portentainput_shm_struc_fname)

    _read_write_loop(termflag_shm, ballvel_shm, portentaoutput_shm,
                     portentainput_shm)

if __name__ == "__main__":
    descr = ("Read incoming Portenta packages, timestamp and place in SHM. Also"
             " read command packages from SHM and send them back to Portenta.")
    argParser = argparse.ArgumentParser(descr)
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--ballvelocity_shm_struc_fname")
    argParser.add_argument("--portentaoutput_shm_struc_fname")
    argParser.add_argument("--portentainput_shm_struc_fname")
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