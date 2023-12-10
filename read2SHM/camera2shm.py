import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import time
import argparse
import cv2

from constants import LOGGING_DIRECTORY
from VideoFrameSHMInterface import VideoFrameSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _setup_capture(x_resolution, y_resolution, fps):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, fps)

    # by default the capture receives frames from the camera closest to the 
    # requested/ set resolution. The code below ensures that the recorded 
    # resolution is garanteed to be larger than the final resolution
    # crashes badly when requested res higher than max camera res:)
    new_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    new_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    while (cap.get(cv2.CAP_PROP_FRAME_WIDTH) < x_resolution or
           cap.get(cv2.CAP_PROP_FRAME_HEIGHT) < y_resolution):
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, new_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, new_height)
        new_width += 30
        new_height += 30
    return cap

def _read_stream_loop(cap, shm_structure_fname, termflag_shm_structure_fname, 
                      x_resolution, y_resolution, n_channels):
    # shm access
    frame_shm = VideoFrameSHMInterface(shm_structure_fname, x_resolution, 
                                       y_resolution, n_channels)
    termflag_shm = FlagSHMInterface(termflag_shm_structure_fname)

    try:
        frame_i = 0
        while True:
            #define breaking condition for the thread/process
            if termflag_shm.is_set():
                break
            
            ret, frame = cap.read()
            t = time.time()
            
            frame = frame[:y_resolution, :x_resolution, :n_channels]
            frame = frame.transpose(1,0,2) # cv2: y-x-rgb, everywhere: x-y-rgb
            frame_shm.add_frame(frame, t)
            # print("{} {}".format(frame_i, t))
            frame_i += 1
    finally:
        cap.release()

def run_camera2shm(shm_structure_fname, termflag_shm_structure_fname, 
                   x_resolution, y_resolution, n_channels, fps):
    cap = _setup_capture(x_resolution, y_resolution, fps)
    _read_stream_loop(cap, shm_structure_fname, termflag_shm_structure_fname, 
                      x_resolution, y_resolution, n_channels)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Read RealSense stream, timestamp, ",
                                        "and place in SHM")
    argParser.add_argument("shm_structure_fname")
    argParser.add_argument("termflag_shm_structure_fname")
    argParser.add_argument("x_resolution", type=int)
    argParser.add_argument("y_resolution", type=int)
    argParser.add_argument("n_channels", type=int)
    argParser.add_argument("fps", type=int)

    kwargs = vars(argParser.parse_args())
    print(kwargs)
    run_camera2shm(**kwargs)