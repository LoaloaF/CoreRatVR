import sys
import os
import argparse
from time import sleep
import time
import h5py
import cv2 as cv
import numpy as np
import pandas as pd
from queue import Queue
from threading import Thread

# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

from CustomLogger import CustomLogger as Logger
from VideoFrameSHMInterface import VideoFrameSHMInterface
from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from shm_interface_utils import extract_packet_data

from FlagSHMInterface import FlagSHMInterface



def _save_frame_packages(queue, full_fname):
    L = Logger()
    while True:
        package_buf = queue.get()
        if package_buf is None:
            break
        df = pd.DataFrame(package_buf)
        L.logger.debug(f"saving to hdf5:\n{df.to_string()}")
        try:
            df.to_hdf(full_fname, key='frame_packages', mode='a', 
                  append=True, format="table")
        except Exception as e:
            L.logger.error(f"Error saving to hdf5:\n{e}")

def _log(frame_shm, termflag_shm, paradigm_running_shm, frames_hdf, save_queue, videowriter=None):
    L = Logger()
    L.logger.info("Reading video frames from SHM and saving them...")

    # shm arguments, used to be in VideoSharedMemory
    x_res = frame_shm.metadata['x_resolution']
    y_res = frame_shm.metadata['y_resolution']
    nchannels = frame_shm.metadata['nchannels']
    package_nbytes = frame_shm.metadata['frame_package_nbytes']

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
            if package_buf:
                save_queue.put(package_buf)
            save_queue.put(None)  # Signal the saving thread to exit
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

        frame_raw = frame_shm.popitem()
        if frame_raw is None:
            sleep(0.001)
            nchecks += 1
            continue

        frame_package = frame_raw[:package_nbytes]
        frame_package = extract_packet_data(frame_package)
        frame_raw = frame_raw[package_nbytes:]
        frame = np.frombuffer(frame_raw, dtype=np.uint8).reshape([y_res, x_res, nchannels])

        # skip the first frame, it may have sat there for very long (probabmatic for logger)
        if prv_id == -1:
            prv_id = frame_package["ID"]
            L.logger.debug(f"Skipping first frame with id {prv_id}")
            continue

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

        frame_id = frame_package['ID']
        try:
            jpeg_ok, jpeg_buf = cv.imencode('.jpg', frame, [cv.IMWRITE_JPEG_QUALITY, 90])
            if jpeg_ok:
                n = frames_hdf["frames"].shape[0]
                frames_hdf["frames"].resize(n + 1, axis=0)
                frames_hdf["frame_ids"].resize(n + 1, axis=0)
                frames_hdf["frames"][-1] = jpeg_buf
                frames_hdf["frame_ids"][-1] = frame_id
            else:
                L.logger.error(f"cv.imencode failed for frame id {frame_id}")
        except Exception as e:
            L.logger.error(f"Error saving frame id {frame_id} to hdf5:\n{e}")

        prv_id = frame_package["ID"]
        nchecks = 1
        if len(package_buf) >= buf_size:
            save_queue.put(package_buf)
            package_buf = []

def run_log_camera(videoframe_shm_struc_fname, termflag_shm_struc_fname, 
                   paradigmflag_shm_struc_fname, logging_name, session_data_dir, 
                   fps, cam_name):
    # shm access
    frame_shm = CyclicPackagesSHMInterface(videoframe_shm_struc_fname)
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

    save_queue = Queue()
    save_thread = Thread(target=_save_frame_packages,
                         args=(save_queue, full_fname.replace(".hdf5", "_packages.hdf5")))
    save_thread.start()

    # Open the frames file once for the whole session.
    # Only _log (this thread) ever touches it — no collision possible.
    with h5py.File(full_fname, "a") as frames_hdf:
        frames_hdf.create_dataset("frames",    shape=(0,), maxshape=(None,),
                                  dtype=h5py.vlen_dtype(np.uint8))
        frames_hdf.create_dataset("frame_ids", shape=(0,), maxshape=(None,),
                                  dtype=np.int64)
        # parse datasets to check
        datasets = list(frames_hdf.keys())
        Logger().logger.debug(f"Datasets in frames_hdf: {datasets}")
        _log(frame_shm, termflag_shm, paradigm_running_shm, frames_hdf, save_queue)
    # frames file cleanly closed here

    save_thread.join()

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