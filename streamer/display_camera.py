import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'read2shm')) # read2SHM dir
import time
import cv2
import argparse
import matplotlib.pyplot as plt

from CustomLogger import CustomLogger as Logger
import PIL.Image as Image
import threading
import queue
from VideoFrameSHMInterface import VideoFrameSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _stream(frame_shm, termflag_shm):
    L = Logger()

    L.logger.info("Starting camera stream")
    prv_frame_package = b''

    try:
        # cv2.startWindowThread()
        cv2.namedWindow(frame_shm._shm_name)
        while True: 
            if termflag_shm.is_set():
                L.logger.info("Termination flag raised")
                break

            # wait until new frame is available
            if (frame_package := frame_shm.get_package()) == prv_frame_package:
                # time.sleep(0.001) #sleep for 1ms while waiting for next frame
                continue
            prv_frame_package = frame_package

            frame = frame_shm.get_frame()
            L.logger.debug(f"New frame {frame.shape} read from SHM: {frame_package}")
            
            # if frame_shm.nchannels < 3:
            #     frame = frame[:,:,0:1]
            
            cv2.imshow(frame_shm._shm_name, frame)
            cv2.waitKey(1)
            # time.sleep(0.1)
    finally:
        cv2.destroyAllWindows()




def run_display_camera(videoframe_shm_struc_fname, termflag_shm_struc_fname):
    # shm access
    frame_shm = VideoFrameSHMInterface(videoframe_shm_struc_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)

    _stream(frame_shm, termflag_shm)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Display webcam stream on screen")
    argParser.add_argument("--videoframe_shm_struc_fname")
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--process_prio", type=int)

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.debug(kwargs)
    
    prio = kwargs.pop("process_prio")
    if sys.platform.startswith('linux'):
        if prio != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')
    run_display_camera(**kwargs)