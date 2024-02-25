import os
import atexit
import subprocess
from Parameters import Parameters
from CustomLogger import CustomLogger as Logger
import shutil

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
        "--process_prio", str(P.CAMERA2SHM_PROC_PRIORITY),
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
        "--process_prio", str(P.CAMERA_STREAM_PROC_PRIORITY),

    )
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_por2shm2por_sim_proc(shm_structure_fname, termflag_shm_structure_fname, 
                              command_shm_structure_fname, logging_name, port_name, 
                              baud_rate):
    P = Parameters()
    stream_script = os.path.join(P.PROJECT_DIRECTORY, "read2SHM", "portenta2shm2portenta_sim.py")
    args = (
        "--shm_structure_fname", shm_structure_fname,
        "--termflag_shm_structure_fname", termflag_shm_structure_fname,
        "--command_shm_structure_fname", command_shm_structure_fname,
        "--logging_dir", P.LOGGING_DIRECTORY_RUN,
        "--logging_name", logging_name,
        "--logging_level", str(P.LOGGING_LEVEL),
        "--process_prio", str(P.PORTENTA2SHM2PORTENTA_PROC_PRIORITY),
        "--port_name", port_name,
        "--baud_rate", str(baud_rate),
    )
    # exe = "nice ", " -n ", " -9 ", P.WHICH_PYTHON
    # return _launch(exe, stream_script, *args)
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_por2shm2por_proc(shm_structure_fname, termflag_shm_structure_fname, 
                          command_shm_structure_fname, logging_name, port_name, 
                          baud_rate):
    P = Parameters()
    stream_script = os.path.join(P.PROJECT_DIRECTORY, "read2SHM", "portenta2shm2portenta.py")
    args = (
        "--shm_structure_fname", shm_structure_fname,
        "--termflag_shm_structure_fname", termflag_shm_structure_fname,
        "--command_shm_structure_fname", command_shm_structure_fname,
        "--logging_dir", P.LOGGING_DIRECTORY_RUN,
        "--logging_name", logging_name,
        "--logging_level", str(P.LOGGING_LEVEL),
        "--process_prio", str(P.PORTENTA2SHM2PORTENTA_PROC_PRIORITY),
        "--port_name", port_name,
        "--baud_rate", str(baud_rate),
    )
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_log_portenta_proc(shm_structure_fname, termflag_shm_structure_fname, 
                          logging_name, data_dir):
    P = Parameters()
    stream_script = os.path.join(P.PROJECT_DIRECTORY, "dataloggers", "log_portenta.py")
    args = (
        "--shm_structure_fname", shm_structure_fname,
        "--termflag_shm_structure_fname", termflag_shm_structure_fname,
        "--logging_dir", P.LOGGING_DIRECTORY_RUN,
        "--logging_name", logging_name,
        "--logging_level", str(P.LOGGING_LEVEL),
        "--process_prio", str(P.LOG_PORTENTA_PROC_PRIORITY),
        "--data_dir", data_dir,
    )
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_stream_portenta_proc(shm_structure_fname, termflag_shm_structure_fname, 
                              logging_name):
    P = Parameters()
    stream_script = os.path.join(P.PROJECT_DIRECTORY, "streamer", "display_packages.py")
    args = (
        "--shm_structure_fname", shm_structure_fname,
        "--termflag_shm_structure_fname", termflag_shm_structure_fname,
        "--logging_dir", P.LOGGING_DIRECTORY_RUN,
        "--logging_name", logging_name,
        "--logging_level", str(P.LOGGING_LEVEL),
        "--process_prio", str(P.STREAM_PORTENTA_PROC_PRIORITY),
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
    
    # if (isinstance(exec, str)):
    #     # Use `tasset` command to set highest priority
    #     exec = ["/bin/nice", "-n", "-90", exec]
    #     # exec = [exec]
    #     proc = subprocess.Popen((*exec, script, *args), stderr=log_file, stdout=log_file)
    proc = subprocess.Popen((exec, script, *args), stderr=log_file, stdout=log_file)

    L.logger.info(f"With PID {proc.pid}") 
    return proc

def _close_log_file(file):
    L = Logger()
    L.logger.info(f"Closing {os.path.basename(file.name)} file: `{file.name}`")
    L.spacer()
    file.close()