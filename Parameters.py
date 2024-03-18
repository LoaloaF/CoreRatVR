import os 
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

        p = os.path.abspath(inspect.getfile(inspect.currentframe()))
        cls._instance.PROJECT_DIRECTORY = os.path.join(os.path.dirname(p), "..")
        p = cls._instance.PROJECT_DIRECTORY, "tmp_shm_structure_JSONs"
        cls._instance.SHM_STRUCTURE_DIRECTORY = os.path.join(*p)
        
        p = cls._instance.PROJECT_DIRECTORY, "data"
        cls._instance.DATA_DIRECTORY = os.path.join(*p)

        cls._instance.SESSION_NAME_PREFIX = "%Y-%m-%d_%H-%M-%S"
        cls._instance.SESSION_NAME_POSTFIX = ""
        cls._instance.SESSION_DATA_DIRECTORY = ""

        p = cls._instance.PROJECT_DIRECTORY, "logs"
        cls._instance.LOGGING_DIRECTORY = os.path.join(*p)
        cls._instance.LOGGING_LEVEL = "INFO"
        cls._instance.LOG_TO_DATA_DIR = True

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
        
        
        cls._instance.SHM_NAME_TERM_FLAG = 'termflag'
        
        cls._instance.SHM_NAME_BALLVELOCITY = 'ballvelocity'
        cls._instance.SHM_NPACKAGES_BALLVELOCITY = int(2**12) # 4k
        cls._instance.SHM_PACKAGE_NBYTES_BALLVELOCITY = 80
        
        cls._instance.SHM_NAME_PORTENTA_OUTPUT = 'portentaoutput'
        cls._instance.SHM_NPACKAGES_PORTENTA_OUTPUT = int(2**12) # 4k
        cls._instance.SHM_PACKAGE_NBYTES_PORTENTA_OUTPUT = 40
        
        cls._instance.SHM_NAME_PORTENTA_INPUT = 'portentainput'
        cls._instance.SHM_NPACKAGES_PORTENTA_INPUT = 16
        cls._instance.SHM_PACKAGE_NBYTES_PORTENTA_INPUT = 32
        
        cls._instance.SHM_NAME_UNITY_OUTPUT = 'unityoutput'
        cls._instance.SHM_NPACKAGES_UNITY_OUTPUT = -1
        cls._instance.SHM_PACKAGE_NBYTES_UNITY_OUTPUT = -1
        
        cls._instance.SHM_NAME_UNITY_INPUT = 'unityinput'
        cls._instance.SHM_NPACKAGES_UNITY_INPUT = -1
        cls._instance.SHM_PACKAGE_NBYTES_UNITY_INPUT = -1
        
        cls._instance.SHM_NAME_FACE_CAM = 'facecam'
        
        cls._instance.SHM_NAME_BODY_CAM = 'bodycam'

        cls._instance.FACE_CAM_IDX = 0
        cls._instance.FACE_CAM_X_RES = 640
        cls._instance.FACE_CAM_Y_RES = 480
        cls._instance.FACE_CAM_NCHANNELS = 3
        cls._instance.FACE_CAM_FPS = 30
        
        cls._instance.BODY_CAM_IDX = 2
        cls._instance.BODY_CAM_X_RES = 640
        cls._instance.BODY_CAM_Y_RES = 480
        cls._instance.BODY_CAM_NCHANNELS = 3
        cls._instance.BODY_CAM_FPS = 30





        cls._instance.CONSOLE_LOGGING_FMT = f'%(asctime)s|%(levelname)s|%(process)s|%(module)s|%(funcName)s\n\t%(message)s'
        cls._instance.FILE_LOGGING_FMT = f'%(asctime)s|%(levelname)s|%(process)s|%(module)s|%(funcName)s\n\t%(message)s'
        # cls._instance.SPACER_LOGGING_FMT = f'%(message)s===========================================\n'

        cls._instance.CAMERA2SHM_PROC_PRIORITY = -1
        cls._instance.CAMERA_STREAM_PROC_PRIORITY = -1
        cls._instance.PORTENTA2SHM2PORTENTA_PROC_PRIORITY = -1
        cls._instance.LOG_PORTENTA_PROC_PRIORITY = -1
        cls._instance.STREAM_PORTENTA_PROC_PRIORITY = -1
        cls._instance.LOG_CAMERA_PROC_PRIORITY = -1

        cls._instance.REALSENSE_X_RESOLUTION = 640
        cls._instance.REALSENSE_Y_RESOLUTION = 480
        cls._instance.REALSENSE_NCHANNELS = 3
        cls._instance.REALSENSE_RECORD_DEPTH = False
        cls._instance.REALSENSE_FPS = 30

        cls._instance.USE_MULTIPROCESSING = True

        #Max 1024 sensor data can be pushed to the cyclic buffer
        cls._instance.SHM_BUFFER_LENGTH = 128*1024 
        #Max possible length of JSON string
        cls._instance.SHM_ITEM_SIZE = 256 
        cls._instance.RANDOM_ID_LENGTH = 12

        cls._instance.PORTENTA_BAUD_RATE = 2000000
        cls._instance.PORTENTA_PORT = 'COM3'
        cls._instance.PORTENTA_TIMEOUT = 1

        info = get_all_system_info()
        cls._instance.SYSTEM = info["SYSTEM"]
        cls._instance.NAME = info["NAME"]
        cls._instance.RELEASE = info["RELEASE"]
        cls._instance.VERSION = info["VERSION"]
        cls._instance.MACHINE = info["MACHINE"]
        cls._instance.PROCESSOR = info["PROCESSOR"]
        cls._instance.PHYSICAL_CORES = info["PHYSICAL_CORES"]
        cls._instance.TOTAL_CORES = info["TOTAL_CORES"]
        cls._instance.RAM_TOTAL = info["RAM_TOTAL"]
        cls._instance.RAM_AVAILABLE = info["RAM_AVAILABLE"]
        cls._instance.RAM_USED = info["RAM_USED"]
        cls._instance.PYTHON_VERSION = info["PYTHON_VERSION"]
        cls._instance.WHICH_PYTHON = info["WHICH_PYTHON"]
        cls._instance.GPU_NAME = info["GPU_NAME"]
        cls._instance.GPU_MEM_AVAIL = info["GPU_MEM_AVAIL"]
        cls._instance.GPU_MEM_TOTAL = info["GPU_MEM_TOTAL"]
        cls._instance.CAMERAS_BY_IDX = info["CAMERAS_BY_IDX"]
        cls._instance.ARDUINO_BY_PORT = info["ARDUINO_BY_PORT"]
        
        # UNO_BAUD_RATE = 115200
        # UNO_COM_PORT = 'COM4'
        # UNO_TIMEOUT = 1

        # REWARD_PUMP_COM_PORT = 'COM3'


        # PSYCHOPY_CAM_INDEX = 2

        # #GLOBAL VARIABLES
        # SCREEN_SIZE = [1920,1080]

        # #Importantant Sleep timers
        # FODDCALL_SLEEP_DURATION = 0.5
        # REWARD_SLEEP_DURATION = 1.0
        # EXTERNAL_COMMAND_SLEEP_DURATION = 1.0

        # #Thresholds
        # AUTOMATIC_REWARD_DISTANCE_THRESHOLD = 6
        # AUTOMATIC_REWARD_PERIOD = 3
        # AUTOMATIC_REWARD_STOP_PERIOD = 3

        # #AUDIO RELATED PARAMS
        # CHUNK = 1024
        # CHANNELS = 2
        # FORMAT = 'paIn16' #This will be converted to pyAudio 16bit
        # RATE = 44100

        # SAVE_FOLDER = './FirstExperimentScriptLoggingTestFolder'
        # CPP_BIN_FOLDER = './marmosetSetup_CppBin'
        return cls._instance
        
    def get_locked_attributes(self) -> dict[str, Any]:
        params = get_attributes()
        locked_keys = [
            self.PROJECT_DIRECTORY,
            self.SHM_STRUCTURE_DIRECTORY,
            self.SESSION_DATA_DIRECTORY,
        ]
        return {key: value for key, value in params.items() if key in locked_keys}
    
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
