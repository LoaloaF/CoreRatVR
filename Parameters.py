import os 
from pathlib import Path 
import inspect
import json
from device_checker import get_all_system_info
from typing import Any

import platform


class Parameters:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Parameters, cls).__new__(cls)
            cls._instance.initialize_defaults()
        return cls._instance
    
    def initialize_defaults(self):
        # basic path parameters
        self.PROJECT_DIRECTORY = self.get_default_project_directory()
        self.SHM_STRUCTURE_DIRECTORY = os.path.join(self.PROJECT_DIRECTORY, "tmp_shm_structure_JSONs")
        self.DATA_DIRECTORY = os.path.join(self.PROJECT_DIRECTORY, "data")
        
        self.DB_LOCATION = "/Volumes/large/Simon/nas_vrdata"
        self.DB_NAME = "vrdata.db"

        # data saving / logging parameters
        self.SESSION_NAME_TEMPLATE = "%Y-%m-%d_%H-%M-%S_active"
        self.SESSION_NAME = "set-at-init"   # set at runtime
        self.SESSION_DATA_DIRECTORY = "set-at-init"   # set at runtime
        self.LOGGING_DIRECTORY = os.path.join(self.PROJECT_DIRECTORY, "logs")
        self.LOGGING_LEVEL = "INFO"
        self.LOG_TO_DATA_DIR = True
        self.CONSOLE_LOGGING_FMT = f'%(asctime)s|%(levelname)s|%(process)s|%(module)s|%(funcName)s\n\t%(message)s'
        self.FILE_LOGGING_FMT = f'%(asctime)s|%(levelname)s|%(process)s|%(module)s|%(funcName)s\n\t%(message)s'
        # self.CREATE_NAS_SESSION_DIR = False
        self.INSPECT_FROM_DB = False

        # Portenta SHM parameters
        self.SHM_NAME_TERM_FLAG = 'termflag'
        self.SHM_NAME_PARADIGM_RUNNING_FLAG = 'paradigmflag'
        self.SHM_NAME_BALLVELOCITY = 'ballvelocity'
        self.SHM_NPACKAGES_BALLVELOCITY = int(2**12) # 4k
        self.SHM_PACKAGE_NBYTES_BALLVELOCITY = 80
        self.SHM_NAME_PORTENTA_OUTPUT = 'portentaoutput'
        self.SHM_NPACKAGES_PORTENTA_OUTPUT = int(2**12) # 4k
        self.SHM_PACKAGE_NBYTES_PORTENTA_OUTPUT = 80
        self.SHM_NAME_PORTENTA_INPUT = 'portentainput'
        self.SHM_NPACKAGES_PORTENTA_INPUT = 16
        self.SHM_PACKAGE_NBYTES_PORTENTA_INPUT = 32

        # Unity SHM parameters
        self.SHM_NAME_UNITY_OUTPUT = 'unityoutput'
        self.SHM_NPACKAGES_UNITY_OUTPUT = 128
        self.SHM_PACKAGE_NBYTES_UNITY_OUTPUT = 256
        self.SHM_NAME_UNITY_INPUT = 'unityinput'
        self.SHM_NPACKAGES_UNITY_INPUT = 16
        self.SHM_PACKAGE_NBYTES_UNITY_INPUT = 256
        self.SHM_NAME_UNITY_CAM = 'unitycam'
        self.UNITY_CAM_X_RES = 500
        self.UNITY_CAM_Y_RES = 400
        self.UNITY_CAM_NCHANNELS = 3
        self.UNITY_CAM_FPS = 20

        # camera shm parameters
        self.SHM_NAME_FACE_CAM = 'facecam'
        self.FACE_CAM_IDX = 0
        self.FACE_CAM_X_TOPLEFT = 0
        self.FACE_CAM_Y_TOPLEFT = 0
        self.FACE_CAM_X_RES = 640
        self.FACE_CAM_Y_RES = 480
        self.FACE_CAM_NCHANNELS = 1
        self.FACE_CAM_FPS = 30

        self.SHM_NAME_BODY_CAM = 'bodycam'
        self.BODY_CAM_IDX = 0
        self.BODY_CAM_X_TOPLEFT = 0
        self.BODY_CAM_Y_TOPLEFT = 0
        self.BODY_CAM_X_RES = 640
        self.BODY_CAM_Y_RES = 480
        self.BODY_CAM_NCHANNELS = 3
        self.BODY_CAM_FPS = 30

        # process priorities parameters
        self.CAMERA2SHM_PROC_PRIORITY = -1
        self.CAMERA_STREAM_PROC_PRIORITY = -1
        self.PORTENTA2SHM2PORTENTA_PROC_PRIORITY = -1
        self.LOG_PORTENTA_PROC_PRIORITY = -1
        self.STREAM_PORTENTA_PROC_PRIORITY = -1
        self.LOG_CAMERA_PROC_PRIORITY = -1
        self.LOG_UNITY_PROC_PRIORITY = -1

        # laptop camera parameters for testing
        # self.FRONT_WEBCAM_IDX = 0
        # self.FRONT_WEBCAM_NAME = "LogitechMainWebcam2"
        # self.FRONT_WEBCAM_X_RES = 640
        # self.FRONT_WEBCAM_Y_RES = 480
        # self.FRONT_WEBCAM_NCHANNELS = 3
        # self.FRONT_WEBCAM_FPS = 30

        # self.BUILTIN_WEBCAM_IDX = 2
        # self.BUILTIN_WEBCAM_NAME = "XPS13Webcam2"
        # self.BUILTIN_WEBCAM_X_RES = 640
        # self.BUILTIN_WEBCAM_Y_RES = 480
        # self.BUILTIN_WEBCAM_NCHANNELS = 3
        # self.BUILTIN_WEBCAM_FPS = 30

        info = get_all_system_info()
        
        self.UNITY_BUILD_DIRECTORY = os.path.join(self.PROJECT_DIRECTORY, info["UNITY_BUILD_DIRECTORY"])
        self.UNITY_BUILD_NAME = info["UNITY_BUILD_NAME"]
        self.NAS_DATA_DIRECTORY = self.get_default_nas_directory()
        
        # system parameters
        self.SYSTEM = info["SYSTEM"]
        self.NAME = info["NAME"]
        self.RELEASE = info["RELEASE"]
        self.VERSION = info["VERSION"]
        self.MACHINE = info["MACHINE"]
        self.PYTHON_VERSION = info["PYTHON_VERSION"]
        self.WHICH_PYTHON = info["WHICH_PYTHON"]
        self.PLATFORMIO_BIN = info["PLATFORMIO_BIN"]
        
        # hardware parameters
        self.PROCESSOR = info["PROCESSOR"]
        self.PHYSICAL_CORES = info["PHYSICAL_CORES"]
        self.TOTAL_CORES = info["TOTAL_CORES"]
        # self.RAM_TOTAL = info["RAM_TOTAL"]
        self.RAM_AVAILABLE = info["RAM_AVAILABLE"]
        self.RAM_USED = info["RAM_USED"]

        # additional hardware parameters
        self.GPU_NAME = info["GPU_NAME"]
        self.GPU_MEM_AVAIL = info["GPU_MEM_AVAIL"]
        # self.GPU_MEM_TOTAL = info["GPU_MEM_TOTAL"]
        # self.CAMERAS_BY_IDX = info["CAMERAS_BY_IDX"]
        self.ARDUINO_PORT = info["ARDUINO_PORT"]
        self.ARDUINO_BAUD_RATE = 2000000
        
    def get_parameter_groups(self):
        return {
            "Directories": (
                "PROJECT_DIRECTORY", "SHM_STRUCTURE_DIRECTORY", "DATA_DIRECTORY", 
                "NAS_DATA_DIRECTORY", "LOGGING_DIRECTORY", "UNITY_BUILD_DIRECTORY",
                "UNITY_BUILD_NAME","DB_LOCATION", "DB_NAME"),
            "Session saving/ Inspect": (
                "SESSION_NAME_TEMPLATE", "SESSION_NAME", "SESSION_DATA_DIRECTORY", 
                "LOGGING_LEVEL", "LOG_TO_DATA_DIR", "CONSOLE_LOGGING_FMT", 
                "FILE_LOGGING_FMT", "INSPECT_FROM_DB"),
            "Portenta shared memory": (
                "SHM_NAME_TERM_FLAG", "SHM_NAME_BALLVELOCITY", "SHM_NPACKAGES_BALLVELOCITY", 
                "SHM_PACKAGE_NBYTES_BALLVELOCITY", "SHM_NAME_PORTENTA_OUTPUT", 
                "SHM_NPACKAGES_PORTENTA_OUTPUT", "SHM_PACKAGE_NBYTES_PORTENTA_OUTPUT", 
                "SHM_NAME_PORTENTA_INPUT", "SHM_NPACKAGES_PORTENTA_INPUT", 
                "SHM_PACKAGE_NBYTES_PORTENTA_INPUT"),
            "Unity shared memory": (
                "SHM_NAME_UNITY_OUTPUT", "SHM_NPACKAGES_UNITY_OUTPUT", 
                "SHM_PACKAGE_NBYTES_UNITY_OUTPUT", "SHM_NAME_UNITY_INPUT", 
                "SHM_NPACKAGES_UNITY_INPUT", "SHM_PACKAGE_NBYTES_UNITY_INPUT", 
                "SHM_NAME_UNITY_CAM", "UNITY_CAM_X_RES", "UNITY_CAM_Y_RES", 
                "UNITY_CAM_NCHANNELS"),
            "Face Camera": (
                "SHM_NAME_FACE_CAM", "FACE_CAM_IDX", "FACE_CAM_X_TOPLEFT", 
                "FACE_CAM_Y_TOPLEFT", "FACE_CAM_X_RES", 
                "FACE_CAM_Y_RES", "FACE_CAM_NCHANNELS"),
            "Body Camera": (
                "SHM_NAME_BODY_CAM", "BODY_CAM_IDX", "BODY_CAM_X_RES", 
                "BODY_CAM_Y_RES", "BODY_CAM_X_TOPLEFT", "BODY_CAM_Y_TOPLEFT", 
                "BODY_CAM_NCHANNELS"),
            "Process Priorities": (
                "CAMERA2SHM_PROC_PRIORITY", "CAMERA_STREAM_PROC_PRIORITY", 
                "PORTENTA2SHM2PORTENTA_PROC_PRIORITY", "LOG_PORTENTA_PROC_PRIORITY", 
                "STREAM_PORTENTA_PROC_PRIORITY", "LOG_CAMERA_PROC_PRIORITY", 
                "LOG_UNITY_PROC_PRIORITY"),
            "System": (
                "SYSTEM", "NAME", "RELEASE", "VERSION", "MACHINE", 
                "PYTHON_VERSION", "WHICH_PYTHON", "PLATFORMIO_BIN"),
            "Hardware": (
                "PROCESSOR", "PHYSICAL_CORES", "TOTAL_CORES", "RAM_AVAILABLE",
                "GPU_NAME", "GPU_MEM_AVAIL", "ARDUINO_PORT"),
        }

    def get_locked_parameters(self) -> dict[str, Any]:
        locked_keys = ["PROJECT_DIRECTORY", "SHM_STRUCTURE_DIRECTORY",
                       "SESSION_DATA_DIRECTORY", "SESSION_NAME", "INSPECT_FROM_DB"]
        locked_keys.extend([key for key in self.get_attributes().keys() 
                            if key.startswith("SHM_NAME")])
        [locked_keys.extend(self.get_parameter_groups()[key]) 
         for key in ('System', 'Hardware')]
        locked_keys = list(filter(lambda key: key!="ARDUINO_PORT", locked_keys))
        return locked_keys
    
    def get_attributes(self) -> dict[str, Any]:
        return {key: value for key, value in vars(self).items()
                if isinstance(key, str) and key.isupper()}
    
    def save_to_json(self, session_save_dir: str) -> None:
        with open(os.path.join(session_save_dir,'parameters.json'), 'w') as f:
            json.dump(self.get_attributes(), f)
            
    def update_from_json(self, params):
        # TODO check for keys that are not in the current parameters
        for key, value in params.items():
            if key not in self.get_attributes().keys():
                print('Deprecated parameter key will be ignored:', key)
                continue
            setattr(self, key, value)

    def __str__(self) -> str:
        params = self.get_attributes()
        params_json = json.dumps(params, indent=2)
        return params_json
    
    @classmethod
    def get_default_project_directory(cls) -> str:
        p = os.path.abspath(inspect.getfile(inspect.currentframe()))
        return os.path.join(os.path.dirname(p), "..")
    
    @classmethod
    def get_default_nas_directory(cls) -> str:
        #nas dir
        if platform.uname().system == "Windows":
            p = "D:", "NTnas", "nas_vrdata"
        elif platform.uname().system == "Linux":
            p = "/", "mnt", "SpatialSequenceLearning"
        elif platform.uname().system == "Darwin":
            p = "/", "Volumes", "large", "BMI", "VirtualReality", "SpatialSequenceLearning"
            # p = "/", "Users", "loaloa", "local_data", "nas_imitation"
        return os.path.join(*p)
        