import platform
import sys
import psutil
import GPUtil
import cv2
import json
from glob import glob
import serial
import time

def _get_system_info():
    uname_info = platform.uname()
    sys_info = {
        'SYSTEM': uname_info.system,
        'NAME': uname_info.node,
        'RELEASE': uname_info.release,
        'VERSION': uname_info.version,
        'MACHINE': uname_info.machine,
        'PROCESSOR': uname_info.processor,
        'PHYSICAL_CORES': psutil.cpu_count(logical=False),
        'TOTAL_CORES': psutil.cpu_count(logical=True),
        'RAM_TOTAL': psutil.virtual_memory().total//1e6,
        'RAM_AVAILABLE': psutil.virtual_memory().available//1e6,
        'RAM_USED': psutil.virtual_memory().used//1e6,
        'PYTHON_VERSION': platform.python_version(),
        'WHICH_PYTHON': sys.executable,
        }
    return sys_info

def _get_gpu_info():
    gpus = GPUtil.getGPUs()
    if not gpus:
        return {'GPU_NAME': "",
                'GPU_MEM_AVAIL': "",
                'GPU_MEM_TOTAL': ""}

    gpu_info = {'GPU_NAME': gpus[0].name, 
                'GPU_MEM_AVAIL': gpus[0].memoryFree, 
                'GPU_MEM_TOTAL': gpus[0].memoryTotal}
    return gpu_info

def _open_cap(index):
    # Check if the video device is opened successfully
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        return cap
    return 

def _get_max_resolution(cap):
    common_resolutions = [
        (3840, 2160),  # Ultra HD or 4K
        (1920, 1080),  # Full HD
        (1280, 720),  # HD
        (640, 480),  # VGA
        (320, 240),  # Common low resolution
    ]
    for width, height in common_resolutions:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Read the values back to check if the set operation was successful
        set_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        set_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # Check if the set operation was successful
        if set_width == width and set_height == height:
            return width, height

def _get_max_fps(cap):
    cap.set(cv2.CAP_PROP_FPS, 300)
    return cap.get(cv2.CAP_PROP_FPS)

def _get_camera_info(sys_info):
    cam_info = {}
    for cam_i in range(5): # max checking 5 cameras
        cap = _open_cap(cam_i)
        if cap is None:
            continue
        
        max_x_res, max_y_res = _get_max_resolution(cap)
        max_fps = _get_max_fps(cap)

        # Get information about the video device
        cam_info.update({cam_i: {'max_x_res': max_x_res, 'max_y_res': max_y_res,
                                 'max_fps': max_fps,}})
        cap.release()
        cam_i += 1
    return {"CAMERAS_BY_IDX": cam_info}

def _get_arduino_info(ard_baud_rate):
    # Check common port names for Arduino on Linux and Windows
    arduino_info = dict.fromkeys(['/dev/ttyACM0', '/dev/ttyUSB0', 'COM3', 
                                  'COM4'])
    for port in arduino_info:
        ser = None
        try:
            ser = serial.Serial(port, baudrate=ard_baud_rate, timeout=1)
            
            ser.reset_input_buffer()
            time.sleep(.1)
            if not ser.in_waiting:
                raise serial.SerialTimeoutException

            val = "Working"
            ser.close()
            ser = None
            
        except serial.SerialTimeoutException:
            val = f"Timeout while reading Port. Reset Aduino?"

        except serial.SerialException as e:
            if "FileNotFoundError" in str(e) or "[Errno 2]" in str(e):
                val = f"Port doesn't exist."
            if "PermissionError" in str(e):
                val = f"Could not open port. Other process blocking access?"
        finally:
            if ser is not None:
                ser.close()
                time.sleep(2)

        arduino_info.update({port: val})
    return {"ARDUINO_BY_PORT": arduino_info}

def get_all_system_info(ard_baud_rate):
    try:
        sys_info = _get_system_info()
        gpu_info = _get_gpu_info()
        cam_info = _get_camera_info(sys_info)
        # ard_info = _get_arduino_info(ard_baud_rate)
        ard_info = {"ARDUINO_BY_PORT": {"COM3": "Working"}}
    except Exception as e:
            print(f"Error getting System information: {e}")
    all_info = {**sys_info,**gpu_info, **cam_info, **ard_info}
    return all_info
