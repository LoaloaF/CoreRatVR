import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import time
import argparse
# from pymba import Vimba

from VideoFrameSHMInterface import VideoFrameSHMInterface
from FlagSHMInterface import FlagSHMInterface
from CustomLogger import CustomLogger as Logger

def _read_vimbastream(frame_shm, termflag_shm, paradigmflag_shm):
    L = Logger()
    L.logger.info("Reading camera stream & writing to SHM...")
    paradigm_running_state = paradigmflag_shm.is_set()

    with Vimba() as vimba:
        vimbacam = vimba.camera(0)
        vimbacam.open()
        vimbacam.arm('SingleFrame')

        try:
            frame_i = 0
            while True:
                if termflag_shm.is_set():
                    L.logger.info("Termination flag raised")
                    break
                
                # switching event 
                if paradigmflag_shm.is_set() != paradigm_running_state:
                    new_state = paradigmflag_shm.is_set()
                    vimbacam.disarm()
                    vimbacam.close()
                    # when flipped to True, wait 200ms longer than Arudino ensuring 
                    # that first frame that is acuired again and read by the logger
                    # also emitted a recorded TTL
                    pause_length = 1200 if new_state else 2200 # when flipped to True
                    time.sleep(pause_length/1000.)
                
                    vimbacam.open()
                    vimbacam.arm('SingleFrame')
                    paradigm_running_state = new_state
                    
                frame = vimbacam.acquire_frame()
                image = frame.buffer_data_numpy()

                pack = "<{" + f"N:I,ID:{frame_i},PCT:{int(time.time()*1e6)}" + "}>\r\n"
                L.logger.debug(f"New frame: {pack}")
                
                image = image[:frame_shm.y_res, :frame_shm.x_res]
                image = image.reshape(image.shape[0], image.shape[1], 1)
                image = image.transpose(1, 0, 2) # cv2: y-x-rgb, everywhere: x-y-rgb

                frame_shm.add_frame(image, pack.encode('utf-8'))
                frame_i += 1

        finally:
            vimbacam.disarm()
            vimbacam.close()

def run_vimbacam2shm(videoframe_shm_struc_fname, termflag_shm_struc_fname, 
                     paradigmflag_shm_struc_fname, cam_name,
                     x_topleft, y_topleft, camera_idx):
    # shm access
    frame_shm = VideoFrameSHMInterface(videoframe_shm_struc_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    paradigmflag_shm = FlagSHMInterface(paradigmflag_shm_struc_fname)
    
    _read_vimbastream(frame_shm, termflag_shm, paradigmflag_shm)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Read camera stream, timestamp, ",
                                        "and place in SHM")
    argParser.add_argument("--videoframe_shm_struc_fname")
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--paradigmflag_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--cam_name")
    argParser.add_argument("--x_topleft", type=int)
    argParser.add_argument("--y_topleft", type=int)
    argParser.add_argument("--process_prio", type=int)
    argParser.add_argument("--camera_idx", type=int)
    kwargs = vars(argParser.parse_args())
    
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    L.logger.debug(L.fmtmsg(kwargs))
    if sys.platform.startswith('linux'):
        if (prio := kwargs.pop("process_prio")) != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')
    
    try:
        from pymba import Vimba
    except ImportError:
        L.logger.error("Failed to import pymba. Install via pip.")
        sys.exit(1)
            
    run_vimbacam2shm(**kwargs)