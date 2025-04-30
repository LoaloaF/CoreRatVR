import json
import requests
from time import sleep
import time
import cv2

import numpy as np

import os
import sys

# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from VideoFrameSHMInterface import VideoFrameSHMInterface
from CustomLogger import CustomLogger as Logger

import SHM.shm_creation as sc


def test_endpoints():
    base_url = "http://localhost:8000"

    def createshm():
        # POST /initiate
        response = requests.post(f"{base_url}/initiate")
        print("POST /initiate:", response.json())

        # POST /shm/create_termflag_shm
        response = requests.post(f"{base_url}/shm/create_termflag_shm")
        print("POST /shm/create_termflag_shm:", response.json())

        # POST /shm/create_ballvelocity_shm
        response = requests.post(f"{base_url}/shm/create_ballvelocity_shm")
        print("POST /shm/create_ballvelocity_shm:", response.json())

        # POST /shm/create_portentaoutput_shm
        response = requests.post(f"{base_url}/shm/create_portentaoutput_shm")
        print("POST /shm/create_portentaoutput_shm:", response.json())
        
        # POST /shm/create_portentainput_shm
        response = requests.post(f"{base_url}/shm/create_portentainput_shm")
        print("POST /shm/create_portentainput_shm:", response.json())

        # POST /shm/create_unityoutput_shm
        response = requests.post(f"{base_url}/shm/create_unityoutput_shm")
        print("POST /shm/create_unityoutput_shm:", response.json())
        
        # POST /shm/create_unityinput_shm
        response = requests.post(f"{base_url}/shm/create_unityinput_shm")
        print("POST /shm/create_unityinput_shm:", response.json())
        
        # POST /shm/create_unityinput_shm
        response = requests.post(f"{base_url}/shm/create_unitycam_shm")
        print("POST /shm/create_unitycam_shm:", response.json())

    def run():
        
        # # POST /procs/open_por2shm2por_sim_proc
        # response = requests.post(f"{base_url}/procs/launch_por2shm2por_sim")
        # print("POST /procs/open_por2shm2por_sim_proc:", response.json())
        
        # POST /procs/open_por2shm2por_proc
        response = requests.post(f"{base_url}/procs/launch_por2shm2por")
        print("POST /procs/open_por2shm2por_proc:", response.json())
        
        # POST /procs/open_log_portenta_proc
        response = requests.post(f"{base_url}/procs/launch_log_portenta")
        print("POST /procs/open_log_portenta_proc:", response.json())
        
        # POST /procs/open_stream_portenta_proc
        response = requests.post(f"{base_url}/procs/launch_stream_portenta")
        print("POST /procs/open_stream_portenta_proc:", response.json())
        
        # POST /procs/launch_log_unity
        response = requests.post(f"{base_url}/procs/launch_log_unity")
        print("POST /procs/launch_log_unity:", response.json())
        
        # POST /procs/launch_log_unity
        response = requests.post(f"{base_url}/procs/launch_log_unitycam")
        print("POST /procs/launch_log_unity:", response.json())


    def run_cam():
        # POST /initiate
        response = requests.post(f"{base_url}/initiate")
        print("POST /initiate:", response.json())
        time.sleep(1)

        # POST /shm/create_termflag_shm
        response = requests.post(f"{base_url}/shm/create_termflag_shm")
        print("POST /shm/create_termflag_shm:", response.json())

        response = requests.post(f"{base_url}/shm/create_facecam_shm")
        print("POST /shm/create_facecam_shm:", response.json())

        response = requests.post(f"{base_url}/procs/launch_log_facecam")
        print("POST /procs/launch_log_facecam:", response.json())
        
        response = requests.post(f"{base_url}/procs/launch_facecam2shm")
        print("POST /procs/launch_facecam2shm:", response.json())
        
        response = requests.post(f"{base_url}/procs/launch_stream_facecam")
        print("POST /procs/launch_stream_facecam:", response.json())
        
        
        
        
        # response = requests.post(f"{base_url}/shm/create_bodycam_shm")
        # print("POST /shm/create_bodycam_shm:", response.json())

        # response = requests.post(f"{base_url}/procs/launch_bodycam2shm")
        # print("POST /procs/launch_bodycam2shm:", response.json())
        
        # time.sleep(1)
        # response = requests.post(f"{base_url}/procs/launch_stream_bodycam")
        # print("POST /procs/launch_stream_bodycam:", response.json())

    def term():
        # POST /term_session
        response = requests.post(f"{base_url}/raise_term_flag")
        print("POST /raise_term_flag:", response.json())

    def inputloop():
        while True:
            msg = input("Press Enter to send Unity input...")
            requests.post(f"{base_url}/unityinput/{msg}", json={"message": msg})
    
    def test_display_cam():
        cyclic_cam_mem = "/Users/loaloa/homedataAir/phd/ratvr/VirtualReality/CoreRatVR/../tmp_shm_structure_JSONs/cyclicFramesTest_shmstruct.json"
        frame_shm = CyclicPackagesSHMInterface(cyclic_cam_mem)
            
        L = Logger()

        L.logger.info("Starting camera stream")
        prv_frame_package = b''

        try:
            # cv2.startWindowThread()
            cv2.namedWindow(frame_shm._shm_name)
            while True: 
                # if termflag_shm.is_set():
                #     L.logger.info("Termination flag raised")
                #     break
                frame_raw = frame_shm.popitem()
                # if out is not None:
                #     print(f"o: {type(o)}, {len(o)}")
                if frame_raw is None:
                    continue
                
                y_res = 1080
                x_res = 1920
                nchannels = 3
                frame = np.frombuffer(frame_raw, dtype=np.uint8).reshape((x_res,y_res, nchannels))
                # L.logger.debug(f"New frame {frame.shape} read from SHM: {frame_package}")

                # # wait until new frame is available
                # if (frame_package := frame_shm.get_package()) == prv_frame_package:
                #     # time.sleep(0.001) #sleep for 1ms while waiting for next frame
                #     continue
                # prv_frame_package = frame_package

                # frame = frame_shm.get_frame()
                # L.logger.debug(f"New frame {frame.shape} read from SHM: {frame_package}")
                
                # # if frame_shm.nchannels < 3:
                # #     frame = frame[:,:,0:1]
                
                
                cv2.imshow(frame_shm._shm_name, frame)
                cv2.waitKey(1)
                # time.sleep(0.1)
        finally:
            cv2.destroyAllWindows()
            
    def _test_bodycam_to_cyclicmemory():
        L = Logger()
        L.logger.info("Reading camera stream & writing to SHM...")
        cyclic_frame_shmframe_shm = CyclicPackagesSHMInterface("/Users/loaloa/homedataAir/phd/ratvr/VirtualReality/CoreRatVR/../tmp_shm_structure_JSONs/cyclicFramesTest_shmstruct.json")
        try:
            frame_i = 0
            cap = cv2.VideoCapture(0)
            while True:
                # define breaking condition for the thread/process
                # if termflag_shm.is_set():
                #     L.logger.info("Termination flag raised")
                #     break
                ret, frame = cap.read()
                if not ret:
                    L.logger.info("Capture didn't return a frame, exiting.")
                    break

                pack = "<{" + f"N:I,ID:{frame_i},PCT:{int(time.time()*1e6)}" + "}>\r\n"
                L.logger.debug(f"New frame: {pack}")
                
                # frame = frame[y_topleft:frame_shm.y_res, x_topleft:frame_shm.x_res, :frame_shm.nchannels]
                frame = frame.transpose(1,0,2) # cv2: y-x-rgb, everywhere: x-y-rgb
                frame_bytes = frame.tobytes()
                cyclic_frame_shmframe_shm.push(frame_bytes)
                frame_i += 1
        finally:
            cap.release()
            

    def create_cyclic_cam_mem():
        # L = Logger()
        # L.logger.info(f"Creating video frame SHM named `{shm_name}`")
        
        # package_nbytes = 80
        # frame_nbytes = x_resolution * y_resolution * nchannels
        # total_nbytes = package_nbytes + frame_nbytes

        # _create_shm(shm_name=shm_name, total_nbytes=total_nbytes)
        
        # shm_structure = {
        #     "shm_type": "video_frame",
        #     "shm_name": shm_name,
        #     "total_nbytes": total_nbytes,
        #     "fields": {"package_nbytes": package_nbytes, 
        #             "frame_nbytes":frame_nbytes},
        #     "field_types": {"tstamp_type": "uint64",
        #                     "framecount_type": "int",
        #                     "frame_type": "uint8"},
        #     "metadata": {"x_resolution": x_resolution, 
        #                 "y_resolution": y_resolution, 
        #                 "nchannels": nchannels,
        #                 "colorformat": "BGR",
        #                 },
        # }
        
        package_nbytes = 80
        nchannels = 3
        x_resolution = 1920
        y_resolution = 1080
        shm_name = "cyclicFramesTest"
        
        frame_nbytes = x_resolution * y_resolution * nchannels
        
        total_nbytes = package_nbytes + frame_nbytes

        sc.create_cyclic_packages_shm(shm_name=shm_name,
                                      package_nbytes=frame_nbytes,
                                      npackages=32)
        
       
    def test_camera_stream():
        L = Logger()
        L.init_logger("test_camera_stream", "/Users/loaloa/homedataAir/phd/ratvr/VirtualReality/CoreRatVR/logs", "INFO")
        
        response = requests.post(f"{base_url}/initiate")
        
        # POST /initiate
        response = requests.post(f"{base_url}/initiate")
        # response = requests.post(f"{base_url}/shm/create_termflag_shm")
        # response = requests.post(f"{base_url}/shm/create_bodycam_shm")
        # response = requests.post(f"{base_url}/procs/launch_bodycam2shm")
        
        # create_cyclic_cam_mem()
        # time.sleep(20)
        # _test_bodycam_to_cyclicmemory()
        test_display_cam()

       
    test_camera_stream()
    
if __name__ == "__main__":
    test_endpoints()