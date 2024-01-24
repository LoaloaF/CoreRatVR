import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM'))

import time
import logging
from threading import Thread

from CustomLogger import CustomLogger as Logger
from Parameters import Parameters

from process_launcher import open_camera2shm_proc
from process_launcher import open_shm2cam_stream_proc

from SHM.shm_creation import create_video_frame_shm
from SHM.shm_creation import create_singlebyte_shm

from FlagSHMInterface import FlagSHMInterface

from read2SHM.camera2shm import run_camera2shm
from streamer.display_camera import run_display_camera

def test_camera2shm(P):
    L = Logger()
    # setup the main logitech stream
    if P.FRONT_WEBCAM_IDX not in P.CAMERAS_BY_IDX:
        L.logger.error(f"Camera with index {P.FRONT_WEBCAM_IDX} not found.")
        exit(1)
    
    # setup termination
    termflag_shm_structure_fname = create_singlebyte_shm(shm_name="termflag")
    
    # setup main camera one shared memory
    camone_shm_struc_fname = create_video_frame_shm(shm_name=P.FRONT_WEBCAM_NAME,
                                                    x_resolution=P.FRONT_WEBCAM_X_RES, 
                                                    y_resolution=P.FRONT_WEBCAM_Y_RES, 
                                                    nchannels=P.FRONT_WEBCAM_NCHANNELS)
    camone2shm_kwargs = {
        "shm_structure_fname": camone_shm_struc_fname,
        "termflag_shm_structure_fname": termflag_shm_structure_fname,
        "camera_idx": P.FRONT_WEBCAM_IDX,
        "fps": P.FRONT_WEBCAM_FPS,
        }
    display_camone_kwargs = camone2shm_kwargs.copy()
    display_camone_kwargs.pop("camera_idx")
    display_camone_kwargs.pop("fps")
    
    # setup camera two shared memory
    camtwo_shm_struc_fname = create_video_frame_shm(shm_name=P.BUILTIN_WEBCAM_NAME, 
                                                    x_resolution=P.BUILTIN_WEBCAM_X_RES, 
                                                    y_resolution=P.BUILTIN_WEBCAM_Y_RES, 
                                                    nchannels=P.BUILTIN_WEBCAM_NCHANNELS)
    camtwo2shm_kwargs = {
        "shm_structure_fname": camtwo_shm_struc_fname,
        "termflag_shm_structure_fname": termflag_shm_structure_fname,
        "camera_idx": P.BUILTIN_WEBCAM_IDX,
        "fps": P.BUILTIN_WEBCAM_FPS,
        }
    display_camtwo_kwargs = camtwo2shm_kwargs.copy()
    display_camtwo_kwargs.pop("camera_idx")
    display_camtwo_kwargs.pop("fps")
    
    
    L.spacer()
    if P.USE_MULTIPROCESSING:
        ln = f"camera2shm_cam{P.FRONT_WEBCAM_IDX}"
        camone2shm_proc = open_camera2shm_proc(logging_name=ln, **camone2shm_kwargs)
        time.sleep(1)   # camera access by opencv more reliable with sleeping
        
        lln = f"stream_camera_cam{P.FRONT_WEBCAM_IDX}"
        display_camone_proc = open_shm2cam_stream_proc(logging_name=ln, 
                                                       **display_camone_kwargs)
        time.sleep(1)
        
        ln = f"camera2shm_cam{P.BUILTIN_WEBCAM_IDX}"
        camtwo2shm_proc = open_camera2shm_proc(logging_name=ln, **camtwo2shm_kwargs)
        time.sleep(1)
        
        ln = f"stream_camera_cam{P.BUILTIN_WEBCAM_IDX}"
        display_camtwo_proc = open_shm2cam_stream_proc(logging_name=ln, 
                                                       **display_camtwo_kwargs)
        
    else:
        Thread(target=run_camera2shm, kwargs=camone2shm_kwargs).start()
        Thread(target=run_camera2shm, kwargs=camtwo2shm_kwargs).start()
        # can only run one opencv display thread at a time...
        Thread(target=run_display_camera, kwargs=display_camtwo_kwargs).start()
        # Thread(target=run_display_camera, kwargs=display_camone_kwargs).start()
    
    termflag_shm = FlagSHMInterface(termflag_shm_structure_fname)
    inp = input("q to quit.")
    if inp == "q":
        L.spacer()
        termflag_shm.set()
        exit()

def main():
    P = Parameters()
    
    # manually update params here
    P.USE_MULTIPROCESSING = True
    P.LOGGING_LEVEL = logging.INFO
    P.LOGGING_LEVEL = logging.DEBUG
    
    L = Logger()
    logging_sub_dir = L.init_logger(__name__, P.LOGGING_DIRECTORY, 
                                    P.LOGGING_LEVEL, True)
    P.LOGGING_DIRECTORY_RUN = logging_sub_dir
    
    L.spacer()
    L.logger.info(L.fmtmsg(["Parameters", str(P)]))
    L.spacer()
    L.logger.info("Testing video SHM read and write with two webcams")
    test_camera2shm(P)

if __name__ == "__main__":
    main()