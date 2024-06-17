import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'read2shm')) # read2SHM dir

import numpy as np
import time
import argparse

from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation

from CustomLogger import CustomLogger as Logger

from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _stream(ballvel_shm, portentaout_shm, termflag_shm):
    fig, axes = _init_plot()
    scatters = []

    scatters.append(axes[0].scatter([],[], s=1, color='k'))
    axes[0].set_title("pckgs in SHM", y=.75, fontsize=8, loc="right")
    
    scatters.append(axes[1].scatter([],[], s=1, color='r'))
    axes[1].set_title("package deltatime", y=.75, fontsize=8, loc="right")

    scatters.append(axes[2].scatter([],[], s=.3, color='y'))
    axes[2].set_title("isFresh ball sensor pkg", y=.75, fontsize=8, loc="right")

    scatters.append(axes[3].scatter([],[], s=1, color='b'))
    axes[3].set_title("Ball sensor, raw-only", y=.75, fontsize=8, loc="right")
    
    scatters.append(axes[4].scatter([],[], s=10, marker='.', color='g'))
    
    scatters.extend([ax.scatter([],[], s=20, marker=".", color='k') for ax in axes[5:]])
    axes[4].set_title("Lick sensor end-event", y=.75, fontsize=8, loc="right")
    axes[5].set_title("Sound start", y=.75, fontsize=8, loc="right")
    axes[6].set_title("Reward start", y=.75, fontsize=8, loc="right")

    
    ani = FuncAnimation(fig, update, fargs=(axes, scatters, ballvel_shm, portentaout_shm, termflag_shm), interval=0,
                        blit=True)
    plt.show()
    
    # L = Logger()
    # fig, axes = _init_plot()
    # scatters = [axes[0].scatter([],[], s=1)]
    # axes[0].set_title("Ball sensor, raw-only", y=.75, fontsize=8, loc="right")
    # scatters.extend([ax.scatter([],[], s=100, marker="|", color='g') for ax in axes[1:]])
    # axes[1].set_title("Lick sensor end-event", y=.75, fontsize=8, loc="right")
    # axes[2].set_title("Sound start", y=.75, fontsize=8, loc="right")
    # axes[3].set_title("Reward start", y=.75, fontsize=8, loc="right")
    
    # ani = FuncAnimation(fig, update, fargs=(axes, scatters, frame_shm, termflag_shm), interval=0,
    #                     blit=True)
    # plt.show()
    

def run_stream_packages(termflag_shm_struc_fname, ballvelocity_shm_struc_fname, 
                        portentaoutput_shm_struc_fname):
    # shm access
    ballvel_shm = CyclicPackagesSHMInterface(ballvelocity_shm_struc_fname)
    portentaout_shm = CyclicPackagesSHMInterface(portentaoutput_shm_struc_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)

    _stream(ballvel_shm, portentaout_shm, termflag_shm)

def _init_plot():
    fig, axes = plt.subplots(7, figsize=(18,5), gridspec_kw={'height_ratios': [3, 3, .5, 4, 2, 1, 1]})
    [ax.tick_params(labelbottom=False) for ax in axes]
    [axes[ax_i].spines[sp].set_visible(False) for ax_i in (0,1,2,4,5,6) 
     for sp in ('top','right','bottom','left')]
    axes[0].set_ylim(-80,8000)
    axes[1].set_ylim(0,5000)
    axes[2].tick_params(axis='both', which='both', length=0, labelleft=False)
    axes[2].set_ylim(-1,3)
    axes[3].set_ylim(-50,50)
    axes[4].set_ylim(0,300)
    axes[5].set_ylim(-100,100)
    axes[5].tick_params(axis='both', which='both', length=0, labelleft=False)
    axes[6].set_ylim(-100,100)
    axes[6].tick_params(axis='both', which='both', length=0, labelleft=False)
    return fig, axes

# def generate_package(num, last_ID):
#     if num <.95:
#         N = "B"
#         Vr = int(np.random.randn()*-100)
#         Vy = int(np.random.randn()*100)
#         Vp = int(np.random.randn()*10)
#         V = f"{Vr}_{Vy}_{Vp}"
#     elif num <.99:
#         N = "L"
#         V = int(np.random.rand()*100)
#     elif num <.995:
#         N = "S"
#         V = 1
#     else:
#         N = "R"
#         V = 1
#     ID = last_ID+1
#     T = int(time.time()*1e6+num*100000)
#     F = int(np.random.rand()>.2)
#     return {'N': N, 'ID': ID, 'T': T, 'V': V, 'F': F}

# def generate_dummy_packages(n):
#     packages = [generate_package(0,0)]
#     for _ in range(n):
#         num = np.random.rand()
#         pack = generate_package(num, packages[-1]["ID"])
#         packages.append(pack)
#     return packages

def get_packages_from_shm(ballvel_shm, portentaout_shm, termflag_shm):
    L = Logger()
    packages = []
    while True:
        L.combi_msg += f'{len(packages)}...'
        # if frame_shm.usage <= 1:
        #     L.logger.debug(f"emptied SHM: {L.combi_msg}")
        #     return packages
        
        if portentaout_shm.usage > 0:
            pack = portentaout_shm.popitem(return_type=dict)
        else:
            pack = ballvel_shm.popitem(return_type=dict)

        if pack is None:
            # L.logger.debug(f"Pack was None, got all:{L.combi_msg}")
            L.combi_msg = ""
            return packages
        if pack == "":
            L.logger.debug(f"Pack was empty string, got all:{L.combi_msg}")
            L.combi_msg = ""
            return packages
        packages.append(pack)

        if len(packages)>100:
            L.logger.debug(f"got 100: {L.combi_msg}")
            L.combi_msg = ""
            return packages

def update(i, axes, scatters, ballvel_shm, portentaout_shm, termflag_shm):
    if termflag_shm is not None and termflag_shm.is_set():
        plt.close()
        exit()

    L = Logger()
    def proc_packet_type(packs, j):
        L.logger.debug(f"processing packets: {packs}")
        x = [p["T"] for p in packs]
        if (x[0] > axes[0].get_xlim()[1]):
            print("ressesetting")
            [ax.set_xlim(x[0], x[0]+4e6) for ax in axes]
        
        y = [p["V"] for p in packs]
        if j==0:
            Vr, Vy, Vp = zip(*[map(int, item.split('_')) for item in y])
            Vr_offsets = np.column_stack((x, Vr))
            Vy_offsets = np.column_stack((x, Vy))
            Vp_offsets = np.column_stack((x, Vp))
            y = Vr

            isFresh = np.array([p["F"] for p in packs], dtype=int)
            offsets = np.column_stack((np.array(x)[isFresh==0], isFresh[isFresh==0]))
            scatters[2].set_offsets(np.concatenate((scatters[2].get_offsets(), offsets)))  # Concatenate old and new points
        
        dt = np.diff([p["T"] for p in packs])
        x_dt = np.column_stack((x[1:], dt))
        scatters[1].set_offsets(np.concatenate((scatters[1].get_offsets(), x_dt)))  # Concatenate old and new points

        shm_size = ballvel_shm.usage
        scat_data = np.column_stack(([x[0]], [shm_size]))
        scatters[0].set_offsets(np.concatenate((scatters[0].get_offsets(), scat_data)))  # Concatenate old and new points
    
        # Update the existing scatter plot with new data
        offsets = np.column_stack((x, y))
        scatters[j+3].set_offsets(np.concatenate((scatters[j+3].get_offsets(), offsets)))  # Concatenate old and new points
        # scatters[j].set_color('r')

    packages = get_packages_from_shm(ballvel_shm, portentaout_shm, termflag_shm)
    # packages = generate_dummy_packages(100)
    if not len(packages):
        return scatters
    
    BV_packs = [p for p in packages if p["N"]=="B"]
    L_packs = [p for p in packages if p["N"]=="L"]
    S_packs = [p for p in packages if p["N"]=="S"]
    R_packs = [p for p in packages if p["N"]=="R"]

    [proc_packet_type(which_p, i) for i, which_p in 
     enumerate([BV_packs,L_packs,S_packs,R_packs]) if which_p]
    L.logger.debug("rendering new")
    L.spacer("debug")
    return scatters

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Display Portenta packages stream on screen")
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--ballvelocity_shm_struc_fname")
    argParser.add_argument("--portentaoutput_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--process_prio", type=int)

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    
    if sys.platform.startswith('linux'):
        if (prio := kwargs.pop("process_prio")) != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')
    run_stream_packages(**kwargs)