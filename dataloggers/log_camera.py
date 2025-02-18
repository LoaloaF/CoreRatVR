import sys
import os

# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import argparse
from time import sleep
import time
import h5py
import cv2 as cv
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from CustomLogger import CustomLogger as Logger
from VideoFrameSHMInterface import VideoFrameSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _save_frame_packages(package_buf, full_fname):
    # write package buffer to hdf_file
    L = Logger()
    df = pd.DataFrame(package_buf)
    L.logger.debug(f"saving to hdf5:\n{df.to_string()}")
    try:
        df.to_hdf(full_fname, key='frame_packages', mode='a', 
                  append=True, format="table")
    except ValueError as e:
        L.logger.error(f"Error saving to hdf5:\n{e}\n\n{df.to_string()}")
    except Exception as e:
        L.logger.error(f"Error saving to hdf5:\n{e}")

def _log(frame_shm, termflag_shm, paradigm_running_shm, full_fname, 
         frames_h5_file, videowriter=None, ):
    L = Logger()
    L.logger.info("Reading video frames from SHM and saving them...")

    package_buf = []
    prv_id = -1
    nchecks = 1
    buf_size = 32
    portenta_start_stop_flag = False
    portenta_start_stop_pct = 0
    prv_time = 0
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            frames_h5_file.close()
            if package_buf:
                _save_frame_packages(package_buf, full_fname)
            break
        
        current_time = int(time.time()*1e6)  
        if not paradigm_running_shm.is_set():
            if not portenta_start_stop_flag:
                L.logger.info(f"Paradigm start not running at {current_time}, on halt....")
                portenta_start_stop_flag = True
                portenta_start_stop_pct = int(time.time()*1e6)
            elif current_time-portenta_start_stop_pct > 1000000:            
                L.logger.debug("Paradigm stopped, on halt....")
                continue
        
        # wait until new frame is available
        if (frame_package := frame_shm.get_package(dict)).get('ID') in (prv_id, None):
            sleep(0.001)
            nchecks += 1
            continue
        
        # skip the first frame, it may have sat there for very long (probabmatic for logger)
        if prv_id == -1:
            prv_id = frame_package["ID"]
            L.logger.debug(f"Skipping first frame with id {prv_id}")
            continue
        
        frame = frame_shm.get_frame()
        # check for ID discontinuity
        if (dif := (frame_package["ID"]-prv_id)) != 1:
            L.logger.warning(f"Package ID discontinuous; gap was {dif}")

        L.logger.debug(f"after {nchecks} SHM checks got frame {frame.shape} "
                       f"{frame_package}. Time from last frame {frame_package['PCT']-prv_time} us")
        frame_package.pop("N")
        package_buf.append(frame_package)
        prv_time = frame_package["PCT"]
               
        if frame_shm._shm_name == "unitycam":
            frame = np.flip(frame, 0)
            frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
        
        # videowriter.write(frame)
            
        # single frame saving
        jpeg_data = cv.imencode('.jpg', frame, [cv.IMWRITE_JPEG_QUALITY, 90])
        name = f"frames/frame_{frame_package['ID']:06d}"
        try:
            frames_h5_file.create_dataset(name=name, data=np.void(jpeg_data[1].tobytes()))
        except Exception as e:
            L.logger.error(f"Error saving frame {name} to hdf5:\n{e}")
            
        prv_id = frame_package["ID"]
        nchecks = 1
        if len(package_buf) >= buf_size:
            # clse and reopen h5 file so pandas based writing of packages works
            frames_h5_file.close()
            _save_frame_packages(package_buf, full_fname)
            package_buf.clear()
            frames_h5_file = h5py.File(full_fname, "a")

def run_log_camera(videoframe_shm_struc_fname, termflag_shm_struc_fname, 
                   paradigmflag_shm_struc_fname, logging_name, session_data_dir, 
                   fps, cam_name):
    # shm access
    frame_shm = VideoFrameSHMInterface(videoframe_shm_struc_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    paradigm_running_shm = FlagSHMInterface(paradigmflag_shm_struc_fname)

    while not paradigm_running_shm.is_set():
        # arduino pauses 1000ms, at some point in this inveral (between 0 and 500ms)
        # the logger wakes up - but there are no packages coming from the arudino 
        # yet bc it's still in wait mode. Ensures that we get first pack
        sleep(.5) # 500ms 
        L.logger.debug("Waiting for paradigm flag to be raised...")  
        
    L.logger.info(f"Paradigm flag raised. Starting to save data...")

    full_fname = os.path.join(session_data_dir, f"{logging_name.replace('log_','')}.hdf5")
    Logger().logger.debug(full_fname)
    with pd.HDFStore(full_fname) as hdf:
        hdf.put('frame_packages', pd.DataFrame(), format='table', append=False)
    # single frame saving, keep open
    frames_h5_file = h5py.File(full_fname, "a")
    frames_h5_file.create_group('frames')
        
    # for speed, don't render videos yet, do it in post
    
    # video saving
    # fourcc = cv.VideoWriter_fourcc(*'mp4v')
    # if cam_name == "bodycam":
    #     videowriter = cv.VideoWriter(full_fname.replace(".hdf5", ".mp4"), fourcc, 
    #                                 fps, (frame_shm.x_res, frame_shm.y_res), isColor=True)
    # elif cam_name == "facecam":
    #     videowriter = cv.VideoWriter(full_fname.replace(".hdf5", ".mp4"), fourcc, 
    #                         fps, (frame_shm.x_res, frame_shm.y_res), isColor=False)
    # elif cam_name == "unitycam":
    #     videowriter = cv.VideoWriter(full_fname.replace(".hdf5", ".mp4"), fourcc, 
    #                         fps, (frame_shm.x_res, frame_shm.y_res), isColor=True)
    
    _log(frame_shm, termflag_shm, paradigm_running_shm, full_fname, frames_h5_file)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Log camera from SHM to save directory")
    argParser.add_argument("--videoframe_shm_struc_fname")
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--paradigmflag_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--cam_name")
    argParser.add_argument("--process_prio", type=int)
    argParser.add_argument("--session_data_dir")
    argParser.add_argument("--fps", type=int)

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.get('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    L.logger.debug(L.fmtmsg(kwargs))
    
    prio = kwargs.pop("process_prio")
    if sys.platform.startswith('linux'):
        if prio != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')
    run_log_camera(**kwargs)