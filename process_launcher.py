import os
import atexit
import subprocess
from Parameters import Parameters
from CustomLogger import CustomLogger as Logger
import shutil

# implement good logging, either to one file or each proc has seperate one
# isolate functionality such as cmd construction, very redundant rn

def open_camera2shm_proc(cam_name):
    P = Parameters()
    script = "camera2shm.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "read2SHM", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args(shm_args=("termflag", cam_name))
    cam_idx = str(P.FACE_CAM_IDX) if cam_name == 'facecam' else str(P.BODY_CAM_IDX)
    fps = str(P.FACE_CAM_FPS) if cam_name == 'facecam' else str(P.BODY_CAM_FPS)
    args.extend([
        "--logging_name", (cam_name+script).replace(".py", ""),
        "--process_prio", str(P.CAMERA2SHM_PROC_PRIORITY),
        "--camera_idx", cam_idx,
        # "--channels", P.FACE_CAM_IDX if cam_name == 'facecam' else P.BODY_CAM_IDX,
        "--fps", fps,
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_shm2cam_stream_proc(cam_name):
    P = Parameters()
    script = "display_camera.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "streamer", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args(shm_args=("termflag", cam_name))
    args.extend([
        "--logging_name", (cam_name+script).replace(".py", ""),
        "--process_prio", str(P.CAMERA2SHM_PROC_PRIORITY),
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_por2shm2por_sim_proc():
    P = Parameters()
    script = "portenta2shm2portenta_sim.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "read2SHM", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args()
    args.extend([
        "--logging_name", script.replace(".py", ""),
        "--process_prio", str(P.PORTENTA2SHM2PORTENTA_PROC_PRIORITY),
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_por2shm2por_proc():
    P = Parameters()
    script = "portenta2shm2portenta.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "read2SHM", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args(shm_args=("termflag", "ballvelocity", 
                                     "portentaoutput", "portentainput"))
    args.extend([
        "--logging_name", script.replace(".py", ""),
        "--process_prio", str(P.PORTENTA2SHM2PORTENTA_PROC_PRIORITY),
        "--port_name", P.PORTENTA_PORT,
        "--baud_rate", str(P.PORTENTA_BAUD_RATE),
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_log_portenta_proc():
    P = Parameters()
    script = "log_portenta.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "dataloggers", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args()
    args.extend([
        "--logging_name", script.replace(".py", ""),
        "--process_prio", str(P.LOG_PORTENTA_PROC_PRIORITY),
        "--session_data_dir", P.SESSION_DATA_DIRECTORY,
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_stream_portenta_proc():
    P = Parameters()
    script = "display_packages.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "streamer", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args()
    args.extend([
        "--logging_name", script.replace(".py", ""),
        "--process_prio", str(P.STREAM_PORTENTA_PROC_PRIORITY),
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)


def _make_proc_args(shm_args=("termflag", "ballvelocity", "portentaoutput"),
                   logging_args=True):
    P = Parameters()
    constr_fname = lambda name: os.path.join(P.SHM_STRUCTURE_DIRECTORY, 
                                             name+"_shmstruct.json")
    args = []
    if "termflag" in shm_args:
        args.extend(("--termflag_shm_struc_fname", 
                     constr_fname(P.SHM_NAME_TERM_FLAG)))
    if "ballvelocity" in shm_args:
        args.extend(("--ballvelocity_shm_struc_fname", 
                     constr_fname(P.SHM_NAME_BALLVELOCITY)))
    if "portentaoutput" in shm_args:
        args.extend(("--portentaoutput_shm_struc_fname", 
                     constr_fname(P.SHM_NAME_PORTENTA_OUTPUT)))
    if "portentainput" in shm_args:
        args.extend(("--portentainput_shm_struc_fname", 
                     constr_fname(P.SHM_NAME_PORTENTA_INPUT)))
    if "facecam" in shm_args:
        args.extend(("--videoframe_shm_struc_fname", 
                     constr_fname(P.SHM_NAME_FACE_CAM)))
    if "bodycam" in shm_args:
        args.extend(("--videoframe_shm_struc_fname", 
                     constr_fname(P.SHM_NAME_BODY_CAM)))
       
    if logging_args:
        args.extend(("--logging_dir", P.LOGGING_DIRECTORY))
        args.extend(("--logging_level", P.LOGGING_LEVEL))
    return args






def _launch(exec, script, *args):
    L = Logger()
    L.logger.info(f"Launching subprocess {os.path.basename(script)}") 
    msg = L.fmtmsg((f"Subprocess {os.path.basename(script)} arguments:", *args))
    L.logger.debug(msg)

    log_dir_i = [i for i in range(len(args)) if args[i] == "--logging_dir"][0]+1
    log_name_i = [i for i in range(len(args)) if args[i] == "--logging_name"][0]+1
    
    log_file = open(os.path.join(args[log_dir_i], args[log_name_i]+".log"), "w")
    L.logger.info(f"Logging to {log_file.name}")
    L.spacer()
    atexit.register(_close_log_file, log_file)
    proc = subprocess.Popen((exec, script, *args), stderr=log_file, stdout=log_file)

    L.logger.info(f"With PID {proc.pid}") 
    return proc

def _close_log_file(file):
    L = Logger()
    L.logger.info(f"Closing {os.path.basename(file.name)} file: `{file.name}`")
    L.spacer()
    file.close()