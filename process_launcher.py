import os
import atexit
import subprocess

from constants import PROJECT_DIRECTORY
from constants import LOGGING_DIRECTORY

# implement good logging, either to one file or each proc has seperate one
# isolate functionality such as cmd construction, very redundant rn

def open_realsense2shm_subprocess(shm_structure_fname, termflag_shm_structure_fname,
                                  x_resolution, y_resolution, n_channels, fps, 
                                  record_depth):
    camera_indx = "0"
    fname = f'frameGrabber_{camera_indx}_stdout.txt'
    proc_log_file = open(os.path.join(LOGGING_DIRECTORY, fname),'w')
    atexit.register(_close_log_file, proc_log_file)

    script = os.path.join(PROJECT_DIRECTORY, "SHM", "read2SHM", "realsense2shm.py")
    base_cmd = ["python", script, shm_structure_fname, termflag_shm_structure_fname]
    params = x_resolution, y_resolution, n_channels, fps, record_depth
    extension_cmd = [str(p) for p in params]
           
    #    LOGGING_DIRECTORY, "--cam_index", camera_indx, '--auto_logging 0')
    return subprocess.Popen(base_cmd+extension_cmd, stdout=proc_log_file, 
                            stderr=proc_log_file)

def open_camera2shm_subprocess(shm_structure_fname, termflag_shm_structure_fname,
                               x_resolution, y_resolution, n_channels, fps):
    camera_indx = "0"
    fname = f'camera2shm_{camera_indx}_stdout.txt'
    proc_log_file = open(os.path.join(LOGGING_DIRECTORY, fname),'w')
    atexit.register(_close_log_file, proc_log_file)

    script = os.path.join(PROJECT_DIRECTORY, "read2SHM", "camera2shm.py")
    base_cmd = ["python", script, shm_structure_fname, termflag_shm_structure_fname]
    params = x_resolution, y_resolution, n_channels, fps
    extension_cmd = [str(p) for p in params]
           
    return subprocess.Popen(base_cmd+extension_cmd, stdout=proc_log_file, 
                            stderr=proc_log_file)

def open_shm2cam_stream_subprocess(shm_structure_fname, termflag_shm_structure_fname,
                                   x_resolution, y_resolution, n_channels):
    fname = f'display_camera_stdout.txt'
    proc_log_file = open(os.path.join(LOGGING_DIRECTORY, fname),'w')
    atexit.register(_close_log_file, proc_log_file)

    script = os.path.join(PROJECT_DIRECTORY, "streamer", "display_camera.py")
    base_cmd = ["python", script, shm_structure_fname, termflag_shm_structure_fname]
    params = x_resolution, y_resolution, n_channels
    extension_cmd = [str(p) for p in params]
    print(base_cmd+extension_cmd)
    return subprocess.Popen(base_cmd+extension_cmd, stdout=proc_log_file,
                            stderr=proc_log_file)

def _close_log_file(f):
    f.close()