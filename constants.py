import os 
import sys
import inspect

PROJECT_DIRECTORY = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
LOGGING_DIRECTORY = os.path.join(PROJECT_DIRECTORY, "tmp_logs")
SHM_STRUCTURE_DIRECTORY = os.path.join(PROJECT_DIRECTORY, "SHM", "tmp_shm_structure_JSONs")

REALSENSE_X_RESOLUTION = 640
REALSENSE_Y_RESOLUTION = 480
REALSENSE_NCHANNELS = 3
REALSENSE_RECORD_DEPTH = False
REALSENSE_FPS = 30

USE_MULTIPROCESSING = True

SHM_BUFFER_LENGTH = 128*1024 #Max 1024 sensor data can be pushed to the cyclic buffer
SHM_ITEM_SIZE = 256 #Max possible length of JSON string
RANDOM_ID_LENGTH = 12

PORTENTA_BAUD_RATE = 921600
PORTENTA_COM_PORT = 'COM5'
PORTENTA_TIMEOUT = 1

UNO_BAUD_RATE = 115200
UNO_COM_PORT = 'COM4'
UNO_TIMEOUT = 1

REWARD_PUMP_COM_PORT = 'COM3'


PSYCHOPY_CAM_INDEX = 2

#GLOBAL VARIABLES
SCREEN_SIZE = [1920,1080]

#Importantant Sleep timers
FODDCALL_SLEEP_DURATION = 0.5
REWARD_SLEEP_DURATION = 1.0
EXTERNAL_COMMAND_SLEEP_DURATION = 1.0

#Thresholds
AUTOMATIC_REWARD_DISTANCE_THRESHOLD = 6
AUTOMATIC_REWARD_PERIOD = 3
AUTOMATIC_REWARD_STOP_PERIOD = 3


#AUDIO RELATED PARAMS
CHUNK = 1024
CHANNELS = 2
FORMAT = 'paIn16' #This will be converted to pyAudio 16bit
RATE = 44100

SAVE_FOLDER = './FirstExperimentScriptLoggingTestFolder'
CPP_BIN_FOLDER = './marmosetSetup_CppBin'

constants_dict = {key: value for key, value in locals().items() 
                  if isinstance(value, str) and not key.startswith("__")}

