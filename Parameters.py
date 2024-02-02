import os 
import sys
import inspect
import logging
import json
from device_checker import get_all_system_info


class Parameters:
    _instance = None

    def __new__(cls):
        if cls._instance:
            return cls._instance

        cls._instance = super(Parameters, cls).__new__(cls)
        cls._instance.var1 = 2
        cls._instance.var2 = 4
        cls._instance.var3 = 22

        cls._instance.FRONT_WEBCAM_IDX = 0
        cls._instance.FRONT_WEBCAM_NAME = "LogitechMainWebcam2"
        cls._instance.FRONT_WEBCAM_X_RES = 640
        cls._instance.FRONT_WEBCAM_Y_RES = 480
        cls._instance.FRONT_WEBCAM_NCHANNELS = 3
        cls._instance.FRONT_WEBCAM_FPS = 30

        cls._instance.BUILTIN_WEBCAM_IDX = 2
        cls._instance.BUILTIN_WEBCAM_NAME = "XPS13Webcam2"
        cls._instance.BUILTIN_WEBCAM_X_RES = 640
        cls._instance.BUILTIN_WEBCAM_Y_RES = 480
        cls._instance.BUILTIN_WEBCAM_NCHANNELS = 3
        cls._instance.BUILTIN_WEBCAM_FPS = 30

        p = os.path.abspath(inspect.getfile(inspect.currentframe()))
        cls._instance.PROJECT_DIRECTORY = os.path.dirname(p)
        p = cls._instance.PROJECT_DIRECTORY, "SHM", "tmp_shm_structure_JSONs"
        cls._instance.SHM_STRUCTURE_DIRECTORY = os.path.join(*p)
        
        p = cls._instance.PROJECT_DIRECTORY, "..", "data"
        cls._instance.DATA_DIRECTORY = os.path.join(*p)

        p = cls._instance.PROJECT_DIRECTORY, "logs"
        cls._instance.LOGGING_DIRECTORY = os.path.join(*p)
        cls._instance.LOGGING_DIRECTORY_RUN = ""
        cls._instance.LOGGING_LEVEL = logging.INFO

        cls._instance.CONSOLE_LOGGING_FMT = f'%(asctime)s|%(levelname)s|%(process)s|%(module)s|%(funcName)s\n\t%(message)s'
        cls._instance.FILE_LOGGING_FMT = f'%(asctime)s|%(levelname)s|%(process)s|%(module)s|%(funcName)s\n\t%(message)s'
        cls._instance.SPACER_LOGGING_FMT = f'%(message)s===========================================\n'

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
        cls._instance.PORTENTA_COM_PORT = 'COM5'
        cls._instance.PORTENTA_TIMEOUT = 1

        info = get_all_system_info(ard_baud_rate=cls._instance.PORTENTA_BAUD_RATE)
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
        
    def __str__(self):
        params = {key: value for key, value in vars(self).items()
                    if isinstance(key, str) and key.isupper()}
        params_json = json.dumps(params, indent=2)
        return params_json