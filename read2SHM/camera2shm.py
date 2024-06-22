import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import time
import argparse
import cv2

from VideoFrameSHMInterface import VideoFrameSHMInterface
from FlagSHMInterface import FlagSHMInterface
from CustomLogger import CustomLogger as Logger

def _setup_capture(x_resolution, y_resolution, camera_idx, fps):
    L = Logger()
    L.logger.debug(f"Setting up video capture for cam {camera_idx}")
    
    cap = cv2.VideoCapture(camera_idx)
    if not cap.isOpened():
        L.logger.error("Failed to open camera")
        exit(1)
    cap.set(cv2.CAP_PROP_FPS, fps)

    #TODO adjust recording size by startfrom xy and end at xy, to allow cropping
    #TODO unity stream is upside and wrong color rgb bgr

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
    L.logger.debug((f"Capturing at resolution X={cap.get(cv2.CAP_PROP_FRAME_WIDTH)} "
                    f"Y={cap.get(cv2.CAP_PROP_FRAME_HEIGHT)} and "
                    f"FPS={cap.get(cv2.CAP_PROP_FPS)}"))
    return cap

def _read_stream_loop(frame_shm, termflag_shm, cap, x_topleft, y_topleft):
    L = Logger()
    L.logger.info("Reading camera stream & writing to SHM...")
    try:
        frame_i = 0
        while True:
            # define breaking condition for the thread/process
            if termflag_shm.is_set():
                L.logger.info("Termination flag raised")
                break
            ret, frame = cap.read()
            if not ret:
                L.logger.info("Capture didn't return a frame, exiting.")
                break

            pack = "<{" + f"N:I,ID:{frame_i},PCT:{int(time.time()*1e6)}" + "}>\r\n"
            L.logger.debug(f"New frame: {pack}")
            
            frame = frame[y_topleft:frame_shm.y_res, x_topleft:frame_shm.x_res, :frame_shm.nchannels]
            frame = frame.transpose(1,0,2) # cv2: y-x-rgb, everywhere: x-y-rgb
            frame_shm.add_frame(frame, pack.encode('utf-8'))
            frame_i += 1
    finally:
        cap.release()

def run_camera2shm(videoframe_shm_struc_fname, termflag_shm_struc_fname, cam_name,
                   x_topleft, y_topleft, camera_idx, fps):
    # shm access
    frame_shm = VideoFrameSHMInterface(videoframe_shm_struc_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)

    cap = _setup_capture(frame_shm.x_res, frame_shm.y_res, camera_idx, fps)
    _read_stream_loop(frame_shm, termflag_shm, cap, x_topleft, y_topleft)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Read camera stream, timestamp, ",
                                        "and place in SHM")
    argParser.add_argument("--videoframe_shm_struc_fname")
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--cam_name")
    argParser.add_argument("--x_topleft", type=int)
    argParser.add_argument("--y_topleft", type=int)
    argParser.add_argument("--process_prio", type=int)
    argParser.add_argument("--camera_idx", type=int)
    argParser.add_argument("--fps", type=int)
    kwargs = vars(argParser.parse_args())
    
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    L.logger.debug(L.fmtmsg(kwargs))
    
    prio = kwargs.pop("process_prio")
    if sys.platform.startswith('linux'):
        if prio != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')

    run_camera2shm(**kwargs)