import os
import atexit
import subprocess
from Parameters import Parameters
from CustomLogger import CustomLogger as Logger

# implement good logging, either to one file or each proc has seperate one
# isolate functionality such as cmd construction, very redundant rn

def open_camera2shm_proc(shm_structure_fname, termflag_shm_structure_fname, 
                         logging_name, camera_idx, fps):
    P = Parameters()
    r2shm_script = os.path.join(P.PROJECT_DIRECTORY, "read2SHM", "camera2shm.py")
    args = (
        "--shm_structure_fname", shm_structure_fname,
        "--termflag_shm_structure_fname", termflag_shm_structure_fname,
        "--logging_dir", P.LOGGING_DIRECTORY_RUN,
        "--logging_name", logging_name,
        "--logging_level", str(P.LOGGING_LEVEL),
        "--camera_idx", str(camera_idx),
        "--fps", str(fps),
    )
    return _launch(P.WHICH_PYTHON, r2shm_script, *args)

def open_shm2cam_stream_proc(shm_structure_fname, termflag_shm_structure_fname, 
                             logging_name):
    P = Parameters()
    stream_script = os.path.join(P.PROJECT_DIRECTORY, "streamer", "display_camera.py")
    args = (
        "--shm_structure_fname", shm_structure_fname,
        "--termflag_shm_structure_fname", termflag_shm_structure_fname,
        "--logging_dir", P.LOGGING_DIRECTORY_RUN,
        "--logging_name", logging_name,
        "--logging_level", str(P.LOGGING_LEVEL),
    )
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def _launch(exec, script, *args):
    L = Logger()
    L.logger.info(f"Launching subprocess {os.path.basename(script)}") 
    msg = L.fmtmsg((f"Subprocess {os.path.basename(script)} arguments:", *args))
    L.logger.debug(msg)

    log_dir_i = [i for i in range(len(args)) if args[i] == "--logging_dir"][0]+1
    log_name_i = [i for i in range(len(args)) if args[i] == "--logging_name"][0]+1
    
    log_file = open(os.path.join(args[log_dir_i], args[log_name_i]+".log"), "w")
    atexit.register(_close_log_file, log_file)
    proc = subprocess.Popen((exec, script, *args), stderr=log_file, stdout=log_file)
    L.logger.info(f"With PID {proc.pid}") 
    return proc

def _close_log_file(file):
    L = Logger()
    L.logger.info(f"Closing {os.path.basename(file.name)} log file: `{file.name}`")
    file.close()