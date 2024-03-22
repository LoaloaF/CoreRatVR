import sys
import os

# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import argparse
from time import sleep

import h5py
import cv2 as cv
import numpy as np
import pandas as pd

from CustomLogger import CustomLogger as Logger
from VideoFrameSHMInterface import VideoFrameSHMInterface
from FlagSHMInterface import FlagSHMInterface

def _save_frame_packages(package_buf, full_fname):
    # write package buffer to hdf_file
    df = pd.DataFrame(package_buf)
    L.logger.debug(f"saving to hdf5:\n{df.to_string()}")
    try:
        df.to_hdf(full_fname, key='frame_packages', mode='a', 
                  append=True, format="table")
    except ValueError as e:
        L.logger.error(f"Error saving to hdf5:\n{e}\n\n{df.to_string()}")

def _log(frame_shm, termflag_shm, full_fname, videowriter):
    L = Logger()
    L.logger.info("Reading video frames from SHM and saving them...")

    package_buf = []
    prv_id = -1
    nchecks = 1
    buf_size = 32
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            if package_buf:
                _save_frame_packages(package_buf, full_fname)
            break

        # wait until new frame is available
        if (frame_package := frame_shm.get_package(dict)).get('ID') in (prv_id, None):
            sleep(0.001)
            nchecks += 1
            continue
        frame = frame_shm.get_frame()
        # check for ID discontinuity
        if (dif := (frame_package["ID"]-prv_id)) != 1:
            L.logger.warning(f"Package ID discontinuous; gap was {dif}")

        L.logger.debug(f"after {nchecks} SHM checks got frame {frame.shape} {frame_package}")
        frame_package.pop("N")
        package_buf.append(frame_package)
        
        # video frame saving
        videowriter.write(frame.transpose(1,0,2))
        # single frame saving
        with h5py.File(full_fname, "a") as hdf:
            jpeg_data = cv.imencode('.jpg', frame, [cv.IMWRITE_JPEG_QUALITY, 90])
            hdf.create_dataset(f"frames/frame_{frame_package['ID']:06d}", 
                               data=np.void(jpeg_data[1].tobytes()))

        prv_id = frame_package["ID"]
        nchecks = 1
        if len(package_buf) >= buf_size:
            _save_frame_packages(package_buf, full_fname)
            package_buf.clear()

def run_log_camera(videoframe_shm_struc_fname, termflag_shm_struc_fname, 
                   logging_name, session_data_dir, fps):
    # shm access
    frame_shm = VideoFrameSHMInterface(videoframe_shm_struc_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)

    full_fname = os.path.join(session_data_dir, f"{logging_name.replace('log_','')}.hdf5")
    with pd.HDFStore(full_fname) as hdf:
        hdf.put('frame_packages', pd.DataFrame(), format='table', append=False)
    # single frame saving
    with h5py.File(full_fname, "a") as hdf:
        hdf.create_group('frames')
    # video saving
    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    videowriter = cv.VideoWriter(full_fname.replace(".hdf5", ".mp4"), fourcc, 
                                 fps, (frame_shm.x_res, frame_shm.y_res))
    
    Logger().logger.debug(full_fname)
    _log(frame_shm, termflag_shm, full_fname, videowriter)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Log camera from SHM to save directory")
    argParser.add_argument("--videoframe_shm_struc_fname")
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--process_prio", type=int)
    argParser.add_argument("--session_data_dir")
    argParser.add_argument("--fps", type=int)

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.get('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.debug(kwargs)
    if sys.platform.startswith('linux'):
        if (prio := kwargs.pop("process_prio")) != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')
    run_log_camera(**kwargs)