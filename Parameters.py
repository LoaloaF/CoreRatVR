import os 
from pathlib import Path 
import inspect
import json
from device_checker import get_all_system_info
from typing import Any


class Parameters:
    _instance = None

    def __new__(cls):
        if cls._instance:
            return cls._instance
        cls._instance = super(Parameters, cls).__new__(cls)

        # basic path parametersPPRO
        p = os.path.abspath(inspect.getfile(inspect.currentframe()))
        cls._instance.PROJECT_DIRECTORY = os.path.join(os.path.dirname(p), "..")
        p = cls._instance.PROJECT_DIRECTORY, "tmp_shm_structure_JSONs"
        cls._instance.SHM_STRUCTURE_DIRECTORY = os.path.join(*p)
        p = cls._instance.PROJECT_DIRECTORY, "data"
        cls._instance.DATA_DIRECTORY = os.path.join(*p)
        
        cls._instance.DB_LOCATION = "/Volumes/large/Simon/nas_vrdata"
        cls._instance.DB_NAME = "vrdata.db"

        # data saving / logging parameters
        cls._instance.SESSION_NAME_TEMPLATE = "%Y-%m-%d_%H-%M-%S_active"
        cls._instance.SESSION_DATA_DIRECTORY = "set-at-init"   # set at runtime
        # logging parameters
        p = cls._instance.PROJECT_DIRECTORY, "logs"
        cls._instance.LOGGING_DIRECTORY = os.path.join(*p)
        cls._instance.LOGGING_LEVEL = "INFO"
        cls._instance.LOG_TO_DATA_DIR = True
        cls._instance.CONSOLE_LOGGING_FMT = f'%(asctime)s|%(levelname)s|%(process)s|%(module)s|%(funcName)s\n\t%(message)s'
        cls._instance.FILE_LOGGING_FMT = f'%(asctime)s|%(levelname)s|%(process)s|%(module)s|%(funcName)s\n\t%(message)s'
        cls._instance.CREATE_NAS_SESSION_DIR = False

        # Portenta SHM parameters
        cls._instance.SHM_NAME_TERM_FLAG = 'termflag'
        
        cls._instance.SHM_NAME_PARADIGM_RUNNING_FLAG = 'paradigmflag'
        
        cls._instance.SHM_NAME_BALLVELOCITY = 'ballvelocity'
        cls._instance.SHM_NPACKAGES_BALLVELOCITY = int(2**12) # 4k
        cls._instance.SHM_PACKAGE_NBYTES_BALLVELOCITY = 128
        
        cls._instance.SHM_NAME_PORTENTA_OUTPUT = 'portentaoutput'
        cls._instance.SHM_NPACKAGES_PORTENTA_OUTPUT = int(2**12) # 4k
        cls._instance.SHM_PACKAGE_NBYTES_PORTENTA_OUTPUT = 128
        
        cls._instance.SHM_NAME_PORTENTA_INPUT = 'portentainput'
        cls._instance.SHM_NPACKAGES_PORTENTA_INPUT = 16
        cls._instance.SHM_PACKAGE_NBYTES_PORTENTA_INPUT = 32


        
        
        # Unity SHM parameters
        cls._instance.SHM_NAME_UNITY_OUTPUT = 'unityoutput'
        cls._instance.SHM_NPACKAGES_UNITY_OUTPUT = 256
        cls._instance.SHM_PACKAGE_NBYTES_UNITY_OUTPUT = 256
        
        cls._instance.SHM_NAME_UNITY_INPUT = 'unityinput'
        cls._instance.SHM_NPACKAGES_UNITY_INPUT = 16
        cls._instance.SHM_PACKAGE_NBYTES_UNITY_INPUT = 256

        cls._instance.SHM_NAME_UNITY_CAM = 'unitycam'
        cls._instance.UNITY_CAM_X_RES = 500
        cls._instance.UNITY_CAM_Y_RES = 400
        cls._instance.UNITY_CAM_NCHANNELS = 3
        cls._instance.UNITY_CAM_FPS = 20



        
        #  camera shm parameters
        cls._instance.SHM_NAME_FACE_CAM = 'facecam'
        cls._instance.FACE_CAM_IDX = 0
        cls._instance.FACE_CAM_X_TOPLEFT = 0
        cls._instance.FACE_CAM_Y_TOPLEFT = 0
        cls._instance.FACE_CAM_X_RES = 640
        cls._instance.FACE_CAM_Y_RES = 480
        cls._instance.FACE_CAM_NCHANNELS = 1
        cls._instance.FACE_CAM_FPS = 30

        
        cls._instance.SHM_NAME_BODY_CAM = 'bodycam'
        cls._instance.BODY_CAM_IDX = 0
        cls._instance.BODY_CAM_X_TOPLEFT = 0
        cls._instance.BODY_CAM_Y_TOPLEFT = 0
        cls._instance.BODY_CAM_X_RES = 640
        cls._instance.BODY_CAM_Y_RES = 480
        cls._instance.BODY_CAM_NCHANNELS = 3
        cls._instance.BODY_CAM_FPS = 30


        # process priorities parameters
        cls._instance.CAMERA2SHM_PROC_PRIORITY = -1
        cls._instance.CAMERA_STREAM_PROC_PRIORITY = -1
        cls._instance.PORTENTA2SHM2PORTENTA_PROC_PRIORITY = -1
        cls._instance.LOG_PORTENTA_PROC_PRIORITY = -1
        cls._instance.STREAM_PORTENTA_PROC_PRIORITY = -1
        cls._instance.LOG_CAMERA_PROC_PRIORITY = -1
        cls._instance.LOG_UNITY_PROC_PRIORITY = -1

        # laptop camera parameters for testing
        # cls._instance.FRONT_WEBCAM_IDX = 0
        # cls._instance.FRONT_WEBCAM_NAME = "LogitechMainWebcam2"
        # cls._instance.FRONT_WEBCAM_X_RES = 640
        # cls._instance.FRONT_WEBCAM_Y_RES = 480
        # cls._instance.FRONT_WEBCAM_NCHANNELS = 3
        # cls._instance.FRONT_WEBCAM_FPS = 30

        # cls._instance.BUILTIN_WEBCAM_IDX = 2
        # cls._instance.BUILTIN_WEBCAM_NAME = "XPS13Webcam2"
        # cls._instance.BUILTIN_WEBCAM_X_RES = 640
        # cls._instance.BUILTIN_WEBCAM_Y_RES = 480
        # cls._instance.BUILTIN_WEBCAM_NCHANNELS = 3
        # cls._instance.BUILTIN_WEBCAM_FPS = 30

        info = get_all_system_info()
        
        p = cls._instance.PROJECT_DIRECTORY, info["UNITY_BUILD_DIRECTORY"]
        cls._instance.UNITY_BUILD_DIRECTORY = os.path.join(*p)
        cls._instance.UNITY_BUILD_NAME = info["UNITY_BUILD_NAME"]
        cls._instance.NAS_DATA_DIRECTORY = info["NAS_DATA_DIRECTORY"]
        
        # system parameters
        cls._instance.SYSTEM = info["SYSTEM"]
        cls._instance.NAME = info["NAME"]
        cls._instance.RELEASE = info["RELEASE"]
        cls._instance.VERSION = info["VERSION"]
        cls._instance.MACHINE = info["MACHINE"]
        cls._instance.PYTHON_VERSION = info["PYTHON_VERSION"]
        cls._instance.WHICH_PYTHON = info["WHICH_PYTHON"]
        cls._instance.PLATFORMIO_BIN = info["PLATFORMIO_BIN"]
        
        # hardware parameters
        cls._instance.PROCESSOR = info["PROCESSOR"]
        cls._instance.PHYSICAL_CORES = info["PHYSICAL_CORES"]
        cls._instance.TOTAL_CORES = info["TOTAL_CORES"]
        # cls._instance.RAM_TOTAL = info["RAM_TOTAL"]
        cls._instance.RAM_AVAILABLE = info["RAM_AVAILABLE"]
        cls._instance.RAM_USED = info["RAM_USED"]

        # additional hardware parameters
        cls._instance.GPU_NAME = info["GPU_NAME"]
        cls._instance.GPU_MEM_AVAIL = info["GPU_MEM_AVAIL"]
        # cls._instance.GPU_MEM_TOTAL = info["GPU_MEM_TOTAL"]
        # cls._instance.CAMERAS_BY_IDX = info["CAMERAS_BY_IDX"]
        cls._instance.ARDUINO_PORT = info["ARDUINO_PORT"]
        cls._instance.ARDUINO_BAUD_RATE = 2000000
        return cls._instance
        
    def get_parameter_groups(self):
        return {
            "Directories": (
                "PROJECT_DIRECTORY", "SHM_STRUCTURE_DIRECTORY", "DATA_DIRECTORY", 
                "NAS_DATA_DIRECTORY", "LOGGING_DIRECTORY", "UNITY_BUILD_DIRECTORY",
                "UNITY_BUILD_NAME","DB_LOCATION", "DB_NAME"),
            "Data/Log Saving": (
                "SESSION_NAME_TEMPLATE", "SESSION_DATA_DIRECTORY", 
                "LOGGING_LEVEL", "LOG_TO_DATA_DIR", "CONSOLE_LOGGING_FMT", 
                "FILE_LOGGING_FMT", "CREATE_NAS_SESSION_DIR"),
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
                       "SESSION_DATA_DIRECTORY"]
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

    def __str__(self) -> str:
        params = self.get_attributes()
        params_json = json.dumps(params, indent=2)
        return params_json


#TODO
# more parameters should be os depdendent, linked to devicer checker, eg /Volumes/large/Simon/nas_vrdata