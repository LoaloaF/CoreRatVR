import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM'))

from threading import Thread

from constants import REALSENSE_X_RESOLUTION
from constants import REALSENSE_Y_RESOLUTION
from constants import REALSENSE_N_CHANNELS
from constants import REALSENSE_FPS
from constants import REALSENSE_RECORD_DEPTH

from SHM.shm_creation import create_video_frame_shm
from SHM.shm_creation import create_singlebyte_shm
from FlagSHMInterface import FlagSHMInterface

from read2SHM.camera2shm import run_camera2shm
from streamer.display_camera import run_display_camera

from process_launcher import open_realsense2shm_subprocess
from process_launcher import open_camera2shm_subprocess
from process_launcher import open_shm2cam_stream_subprocess

# device check - to be implemented - 
# select device 1,2,... - to be implemented - 
# create metadata file from constants.py - to be implemented - 

def test_camera2shm(use_multiprocessing):
    shm_structure_fname = create_video_frame_shm(shm_name="simonswebcam", 
                                                 x_resolution=640, 
                                                 y_resolution=420, 
                                                 n_channels=3)
    termflag_shm_structure_fname = create_singlebyte_shm(shm_name="termflag")

    cam2shm_kwargs = {
        "shm_structure_fname": shm_structure_fname,
        "termflag_shm_structure_fname": termflag_shm_structure_fname,
        "x_resolution": 640,
        "y_resolution": 420,
        "n_channels": 3,
        "fps": 30,}

    displaycam_kwargs = cam2shm_kwargs.copy()
    displaycam_kwargs.pop("fps")
    
    if use_multiprocessing:
        cam2shm_proc = open_camera2shm_subprocess(**cam2shm_kwargs)
        displaycam_proc = open_shm2cam_stream_subprocess(**displaycam_kwargs)
        
    else:
        Thread(target=run_camera2shm, kwargs=cam2shm_kwargs).start()
        Thread(target=run_display_camera, kwargs=displaycam_kwargs).start()
    
    termflag_shm = FlagSHMInterface(termflag_shm_structure_fname)
    inp = input("q to quit.")
    if inp == "q":
        termflag_shm.set()
        exit()

if __name__ == "__main__":
    test_camera2shm(use_multiprocessing=True)