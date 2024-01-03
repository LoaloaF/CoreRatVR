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

from constants import LOGGING_DIRECTORY

from VideoFrameSHMInterface import VideoFrameSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _stream(shm_structure_fname, termflag_shm_structure_fname):
    
    # access shm
    frame_shm = VideoFrameSHMInterface(shm_structure_fname)
    x_res = frame_shm.x_res
    y_res = frame_shm.y_res
    nchannels = frame_shm.nchannels
    termflag_shm = FlagSHMInterface(termflag_shm_structure_fname)
    curr_t = time.time() #get current timestamp

    try:
        cam_index = 0
        window_name = 'Camera{}'.format(cam_index)
        cv2.startWindowThread()
        while True: 
            if termflag_shm.is_set():
                break
            #wait until new frame is available
            if not frame_shm.compare_timestamps(curr_t):
                #time.sleep(0.001) #sleep for 1ms while waiting for next frame
                pass
            else:
                frame, curr_t = frame_shm.get_frame()
                # do slicing here, format x-dim, ydim, col (np)
                if frame_shm.nchannels < 3:
                    frame = frame[:,:,0:1]

                cv2.namedWindow(window_name)
                # then flip to convert to cv2 y-x-col
                cv2.imshow(window_name, frame.transpose(1,0,2))
                cv2.waitKey(1)
    finally:
        cv2.destroyAllWindows()

def run_display_camera(shm_structure_fname, termflag_shm_structure_fname):
    _stream(shm_structure_fname, termflag_shm_structure_fname)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Display webcam stream on screen")
    argParser.add_argument("shm_structure_fname")
    argParser.add_argument("termflag_shm_structure_fname")

    kwargs = vars(argParser.parse_args())
    run_display_camera(**kwargs)