import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import time
import argparse
# from pymba import Vimba

from VideoFrameSHMInterface import VideoFrameSHMInterface
from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from FlagSHMInterface import FlagSHMInterface
from CustomLogger import CustomLogger as Logger


def _read_vimbastream(frame_shm, termflag_shm, paradigmflag_shm, camera_identifer):
    L = Logger()
    L.logger.info("Reading camera stream & writing to SHM...")

    with Vimba() as vimba:
        L.logger.debug(vimba.camera_ids())
        vimbacam = vimba.camera(camera_identifer)
        try:
            vimbacam.open()
        except Exception as e:
            L.logger.error(f"Failed to open camera: {e}")
            return
        

        def frame_acqu_callback(frame):
            nonlocal frame_i
            nonlocal prv_t
            
            L.logger.debug(f"Frame callback triggered")
            image = frame.buffer_data_numpy()

            t = int(time.time()*1e6)
            pack = "<{" + f"N:I,ID:{frame_i},PCT:{t}" + "}>\r\n"
            L.logger.debug(f"Gap was: \033[1;33m{(t-prv_t)/1000}ms \033[0m")
            
            x_res = frame_shm.metadata['x_resolution']
            y_res = frame_shm.metadata['y_resolution']
            nchannels = frame_shm.metadata['nchannels']
            
            image = image[:y_res, :x_res,]
            # flip y and x
            image = image[::-1, ::-1]
            image = image.reshape(image.shape[0], image.shape[1], 1)
            # image = image.transpose(1, 0, 2) # cv2: y-x-rgb, everywhere: x-y-rgb

            # frame_shm.add_frame(image, pack.encode('utf-8'))
            frame_bytes = image.tobytes()
            package_nbytes = frame_shm.metadata['frame_package_nbytes']
            combined_bytes = bytearray(package_nbytes+len(frame_bytes))
            combined_bytes[:len(pack)] = pack.encode('utf-8')
            combined_bytes[package_nbytes:] = frame_bytes
            frame_shm.push(combined_bytes)
            
            frame_i += 1
            prv_t = t
            
        frame_i = 0
        prv_t = 0
        vimbacam.arm('Continuous', callback=frame_acqu_callback, 
                     frame_buffer_size=3)
        vimbacam.start_frame_acquisition()
        paradigm_running_state = paradigmflag_shm.is_set()

        try:
            while True:
                if termflag_shm.is_set():
                    L.logger.info("Termination flag raised")
                    break
                
                # switching event 
                if paradigmflag_shm.is_set() != paradigm_running_state:
                    new_state = paradigmflag_shm.is_set()
                    # close to cleanly reopen after pausing
                    vimbacam.disarm()
                    vimbacam.close()
                    # when flipped to True, wait 200ms longer than Arudino ensuring 
                    # that first frame that is acuired again and read by the logger
                    # also emitted a recorded TTL
                    pause_length = 1200 if new_state else 2200 # when flipped to True
                    time.sleep(pause_length/1000.)
                
                    vimbacam.open()
                    vimbacam.arm('Continuous', callback=frame_acqu_callback, 
                                frame_buffer_size=200)
                    vimbacam.start_frame_acquisition()
                    paradigm_running_state = new_state
                    
                time.sleep(0.1)
        finally:
            vimbacam.stop_frame_acquisition()
            vimbacam.disarm()
            vimbacam.close()

def run_vimbacam2shm(videoframe_shm_struc_fname, termflag_shm_struc_fname, 
                     paradigmflag_shm_struc_fname, cam_name,
                     x_topleft, y_topleft, camera_identifer):
    # shm access
    # frame_shm = VideoFrameSHMInterface(videoframe_shm_struc_fname)
    frame_shm = CyclicPackagesSHMInterface(videoframe_shm_struc_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_struc_fname)
    paradigmflag_shm = FlagSHMInterface(paradigmflag_shm_struc_fname)
    
    _read_vimbastream(frame_shm, termflag_shm, paradigmflag_shm, camera_identifer)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Read camera stream, timestamp, ",
                                        "and place in SHM")
    argParser.add_argument("--videoframe_shm_struc_fname")
    argParser.add_argument("--termflag_shm_struc_fname")
    argParser.add_argument("--paradigmflag_shm_struc_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--cam_name")
    argParser.add_argument("--x_topleft", type=int)
    argParser.add_argument("--y_topleft", type=int)
    argParser.add_argument("--process_prio", type=int)
    argParser.add_argument("--camera_identifer")
    kwargs = vars(argParser.parse_args())
    
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    L.logger.debug(L.fmtmsg(kwargs))
    if sys.platform.startswith('linux'):
        if (prio := kwargs.pop("process_prio")) != -1:
            os.system(f'sudo chrt -f -p {prio} {os.getpid()}')
    
    try:
        from pymba import Vimba
    except ImportError:
        L.logger.error("Failed to import pymba. Install via pip.")
        sys.exit(1)
            
    run_vimbacam2shm(**kwargs)
    
    
    
    
    