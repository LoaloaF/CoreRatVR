import os
import atexit
import subprocess
from Parameters import Parameters
from SessionParamters import SessionParamters

from CustomLogger import CustomLogger as Logger

def open_camera2shm_proc(cam_name):
    P = Parameters()
    script = "camera2shm.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "read2SHM", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args(shm_args=("termflag", cam_name))
    cam_idx = str(P.FACE_CAM_IDX) if cam_name == 'facecam' else str(P.BODY_CAM_IDX)
    fps = str(P.FACE_CAM_FPS) if cam_name == 'facecam' else str(P.BODY_CAM_FPS)
    args.extend([
        "--logging_name", cam_name+"2shm",
        "--process_prio", str(P.CAMERA2SHM_PROC_PRIORITY),
        "--camera_idx", cam_idx,
        # "--channels", P.FACE_CAM_IDX if cam_name == 'facecam' else P.BODY_CAM_IDX,
        "--fps", fps,
        "--cam_name", cam_name
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_vimbacam2shm_proc(cam_name):
    P = Parameters()
    script = "vimbacam2shm.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "read2SHM", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args(shm_args=("termflag", cam_name))
    cam_idx = str(P.FACE_CAM_IDX) if cam_name == 'facecam' else str(P.BODY_CAM_IDX)
    args.extend([
        "--logging_name", cam_name+"2shm",
        "--process_prio", str(P.CAMERA2SHM_PROC_PRIORITY),
        "--camera_idx", cam_idx,
        # "--channels", P.FACE_CAM_IDX if cam_name == 'facecam' else P.BODY_CAM_IDX,
        "--cam_name", cam_name
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_shm2cam_stream_proc(cam_name):
    P = Parameters()
    script = "display_camera.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "streamer", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args(shm_args=("termflag", cam_name))
    args.extend([
        "--logging_name", "display_"+cam_name,
        "--process_prio", str(P.CAMERA2SHM_PROC_PRIORITY),
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_log_camera_proc(cam_name):
    P = Parameters()
    script = "log_camera.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "dataloggers", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args(shm_args=("termflag", cam_name))
    
    match cam_name:
        case 'facecam':
            fps = str(P.FACE_CAM_FPS)
        case 'bodycam':
            fps = str(P.BODY_CAM_FPS)
        case 'unitycam':
            fps = str(P.UNITY_CAM_FPS)
    args.extend([
        "--logging_name", "log_"+cam_name,
        "--process_prio", str(P.LOG_CAMERA_PROC_PRIORITY),
        "--session_data_dir", P.SESSION_DATA_DIRECTORY,
        "--fps", fps,
        "--cam_name", cam_name
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_por2shm2por_sim_proc():
    P = Parameters()
    script = "portenta2shm2portenta_sim.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "read2SHM", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args(shm_args=("termflag", "ballvelocity", 
                                     "portentaoutput", "portentainput"))
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
        "--port_name", P.ARDUINO_PORT,
        "--baud_rate", str(P.ARDUINO_BAUD_RATE),
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

def open_log_unity_proc():
    P = Parameters()
    script = "log_unity.py"
    path = P.PROJECT_DIRECTORY, "CoreRatVR", "dataloggers", script
    stream_script = os.path.join(*path)
    
    args = _make_proc_args(shm_args=("termflag", "unityoutput"))
    args.extend([
        "--logging_name", script.replace(".py", ""),
        "--process_prio", str(P.LOG_UNITY_PROC_PRIORITY),
        "--session_data_dir", P.SESSION_DATA_DIRECTORY
        # "--trial_package_variables", str(SessionParamters().session_parameters_dict["trialPackageVariables"]),
    ])
    return _launch(P.WHICH_PYTHON, stream_script, *args)

def open_unity_proc():
    P = Parameters()
    path = P.PROJECT_DIRECTORY, "UnityRatVR", "builds", P.UNITY_BUILD_NAME
    script = os.path.join(*path)
    
    # for mac:
    # path + ".app"
    args = [
        "-a", script,
        "-n",
        "-W",
        "--args",
        "-logfile", log_fullfname,
    ]
    subprocess.Popen(("open", *args))
    
    log_fullfname = os.path.join(P.LOGGING_DIRECTORY, "unity.log")
    args = [
        "-logfile", log_fullfname,
    ]

    print(script)
    if not os.path.exists(script):
        return -1
    
    L = Logger()
    L.logger.info(f"Launching subprocess {os.path.basename(script)}") 
    L.logger.info(f"Logging to {log_fullfname}")
    return subprocess.Popen((script, *args))

def open_process_session_proc():
    P = Parameters()
    script = os.path.join(P.PROJECT_DIRECTORY, "CoreRatVR", 'process_session.py')
    
    args = _make_proc_args(shm_args=())
    args.extend([
        "--logging_name", script.replace(".py", ""),
    ])
    return _launch(P.WHICH_PYTHON, script, *args)

def shm_struct_fname(shm_name):
    P = Parameters()
    return os.path.join(P.SHM_STRUCTURE_DIRECTORY, shm_name+"_shmstruct.json")

def _make_proc_args(shm_args=("termflag", "ballvelocity", "portentaoutput"),
                   logging_args=True):
    P = Parameters()
    args = []
    if "termflag" in shm_args:
        args.extend(("--termflag_shm_struc_fname", 
                     shm_struct_fname(P.SHM_NAME_TERM_FLAG)))
    if "ballvelocity" in shm_args:
        args.extend(("--ballvelocity_shm_struc_fname", 
                     shm_struct_fname(P.SHM_NAME_BALLVELOCITY)))
    if "portentaoutput" in shm_args:
        args.extend(("--portentaoutput_shm_struc_fname", 
                     shm_struct_fname(P.SHM_NAME_PORTENTA_OUTPUT)))
    if "portentainput" in shm_args:
        args.extend(("--portentainput_shm_struc_fname", 
                     shm_struct_fname(P.SHM_NAME_PORTENTA_INPUT)))
    if "facecam" in shm_args:
        args.extend(("--videoframe_shm_struc_fname", 
                     shm_struct_fname(P.SHM_NAME_FACE_CAM)))
    if "bodycam" in shm_args:
        args.extend(("--videoframe_shm_struc_fname", 
                     shm_struct_fname(P.SHM_NAME_BODY_CAM)))
    if "unityoutput" in shm_args:
        args.extend(("--unityoutput_shm_struc_fname", 
                     shm_struct_fname(P.SHM_NAME_UNITY_OUTPUT)))
    if "unityinput" in shm_args:
        args.extend(("--unityinput_shm_struc_fname", 
                     shm_struct_fname(P.SHM_NAME_UNITY_INPUT)))
    if "unitycam" in shm_args:
        args.extend(("--videoframe_shm_struc_fname", 
                     shm_struct_fname(P.SHM_NAME_UNITY_CAM)))
       
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