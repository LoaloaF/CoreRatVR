import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'read2shm')) # read2SHM dir

import numpy as np
import cv2
from datetime import datetime
import time
import argparse

from CustomLogger import CustomLogger as Logger

from VideoFrameSHMInterface import VideoFrameSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _stream(frame_shm, termflag_shm):
    L = Logger()
    # access shm
    x_res = frame_shm.x_res
    y_res = frame_shm.y_res
    nchannels = frame_shm.nchannels
    curr_t = time.time() #get current timestamp

    L.logger.info("Starting camera stream")
    try:
        cam_index = 0
        cv2.startWindowThread()
        while True: 
            if termflag_shm.is_set():
                L.logger.info("Termination flag raised")
                break

            #wait until new frame is available
            if not frame_shm.compare_timestamps(curr_t):
                #time.sleep(0.001) #sleep for 1ms while waiting for next frame
                pass
            else:
                frame, curr_t = frame_shm.get_frame()
                L.logger.debug(f"New frame read from SHM")

                # do slicing here, format x-dim, ydim, col (np)
                if frame_shm.nchannels < 3:
                    frame = frame[:,:,0:1]

                cv2.namedWindow(frame_shm._shm_name)
                # then flip to convert to cv2 y-x-col
                cv2.imshow(frame_shm._shm_name, frame.transpose(1,0,2))
                cv2.waitKey(1)
    finally:
        cv2.destroyAllWindows()

def run_display_camera(shm_structure_fname, termflag_shm_structure_fname):
    # shm access
    frame_shm = VideoFrameSHMInterface(shm_structure_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_structure_fname)

    _stream(frame_shm, termflag_shm)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Display webcam stream on screen")
    argParser.add_argument("--shm_structure_fname")
    argParser.add_argument("--termflag_shm_structure_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level", type=int)

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    run_display_camera(**kwargs)