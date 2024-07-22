import platform
import sys
import psutil
import GPUtil
import cv2
import os
from glob import glob
import serial
import time
import cpuinfo

def _get_system_info():
    cpu_info = cpuinfo.get_cpu_info()
    uname_info = platform.uname()
    if uname_info.system == "Windows":
        platformio_bin_path = "C:Program Files", ".platformio", "bin", "platformio.exe"
    else:
        platformio_bin_path = "~", ".platformio", "penv", "bin", "platformio"
    sys_info = {
        'SYSTEM': uname_info.system,
        'NAME': uname_info.node,
        'RELEASE': uname_info.release,
        'VERSION': uname_info.version,
        'MACHINE': uname_info.machine,
        'PROCESSOR': cpu_info['brand_raw'].replace("Core(TM)", ""),
        'PHYSICAL_CORES': psutil.cpu_count(logical=False),
        'TOTAL_CORES': psutil.cpu_count(logical=True),
        'RAM_TOTAL': psutil.virtual_memory().total//1e6,
        'RAM_AVAILABLE': psutil.virtual_memory().available//1e6,
        'RAM_USED': psutil.virtual_memory().used//1e6,
        'PYTHON_VERSION': platform.python_version(),
        'WHICH_PYTHON': sys.executable,
        'WHICH_PYTHON': sys.executable,
        'PLATFORMIO_BIN': os.path.join(*platformio_bin_path)
        }
    return sys_info

def _get_gpu_info():
    gpus = GPUtil.getGPUs()
    if not gpus:
        return {'GPU_NAME': "",
                'GPU_MEM_AVAIL': ""}

    gpu_info = {'GPU_NAME': gpus[0].name, 
                'GPU_MEM_AVAIL': gpus[0].memoryFree, 
                'GPU_MEM_TOTAL': gpus[0].memoryTotal}
    return gpu_info

def get_camera_info():
    def _get_max_fps(cap):
        cap.set(cv2.CAP_PROP_FPS, 300)
        return cap.get(cv2.CAP_PROP_FPS)
    
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
    
    def _open_cap(index):
        # Check if the video device is opened successfully
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            return cap
        return 
    
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

def _get_system_dep_defaults(sys_info):
    defaults = {}
    
    # Arduino
    if sys_info['SYSTEM'] == 'Linux':
        defaults['ARDUINO_PORT'] = '/dev/ttyACM0'
    elif sys_info['SYSTEM'] == 'Windows':
        defaults['ARDUINO_PORT'] = 'COM3'
    elif sys_info['SYSTEM'] == 'Darwin':
        defaults['ARDUINO_PORT'] = '/dev/tty.usbmodem14101'
        
    #platformio bin
    if sys_info['SYSTEM'] == "Windows":
        p = "C:Program Files", ".platformio", "bin", "platformio.exe"
    elif sys_info['SYSTEM'] in ("Linux", "Darwin"):
        p = "~", ".platformio", "penv", "bin", "platformio"
    defaults["PLATFORMIO_BIN"] = os.path.join(*p)
    
    #nas dir
    if sys_info['SYSTEM'] == "Windows":
        p = "D:", "NTnas", "nas_vrdata"
    elif sys_info['SYSTEM'] == "Linux":
        p = "/", "mnt", "NTnas", "nas_vrdata"
    elif sys_info['SYSTEM'] == "Darwin":
        p = "/", "Volumes", "large", "simon", "nas_vrdata"
    defaults["NAS_DATA_DIRECTORY"] = os.path.join(*p)
    
    # unity build
    if sys_info['SYSTEM'] in ("Windows", "Linux"):
        p = "UnityRatVR", "builds"
        build_name = 'build00.x86_64'
    elif sys_info['SYSTEM'] == "Darwin":
        p = "UnityRatVR", "builds", "build00.app", "Contents", "MacOS"
        build_name = "build00"
    defaults["UNITY_BUILD_DIRECTORY"] = os.path.join(*p)
    defaults["UNITY_BUILD_NAME"] = build_name
    
    return defaults

def get_all_system_info():
    sys_info = _get_system_info()
    gpu_info = _get_gpu_info()
    more_info = _get_system_dep_defaults(sys_info)
    all_info = {**sys_info,**gpu_info,**more_info}
    return all_info
