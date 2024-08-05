import os
from fastapi import WebSocket
from fastapi import HTTPException, Request
from starlette.types import Scope

import glob
import asyncio
import time
import cv2
from CustomLogger import CustomLogger as Logger

from Parameters import Parameters
from backend_helpers import validate_state
from requests import request

import process_launcher as pl
from process_launcher import shm_struct_fname
from SHM.CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from SHM.VideoFrameSHMInterface import VideoFrameSHMInterface

def attach_stream_endpoints(app):
    # singlton class - reference to instance created in lifespan
    P = Parameters()
    
    @app.websocket("/stream/ballvelocity")
    async def stream_ballvelocity(websocket: WebSocket):
        validate_state(app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_BALLVELOCITY: True,
                                          },
                       # either one of these should be running but validate_state doesn't allow that yet
                       valid_proc_running={
                                        #    "por2shm2por_sim": True,
                                        #    "por2shm2por": True,   
                                           })
        
        L = Logger()
        ballvel_shm = CyclicPackagesSHMInterface(shm_struct_fname(P.SHM_NAME_BALLVELOCITY))
        await websocket.accept()
        try:
            ballvel_pkgs = []
            t0 = time.time()                
            while True:
                await asyncio.sleep(0.001) # check memory every 100us

                maxpops = 3
                while ballvel_shm.usage > 0 and maxpops > 0:
                    pack = ballvel_shm.popitem(return_type=dict)
                    ryp = dict(zip(("raw", "yaw", "pitch"), 
                                   [int(v) for v in pack.pop("V").split("_")]))
                    ballvel_pkgs.append({**pack, **ryp})
                    # L.logger.warning(f"pop took {time.time()*1e6 - _t0}us, pckg delta: {pack['PCT']-pckg_t0}us")
                    pckg_t0 = pack["PCT"]
                    maxpops -= 1
                    
                if ballvel_shm.usage>10 and time.time() - t0 > 0.0333333:
                    L.logger.warning(f"sending ball vell too slowly: {ballvel_shm.usage}")
                if  time.time() - t0 > 0.0333333: # 30 packages a second
                    # L.logger.info(f"\n\nSending {len(ballvel_pkgs)} packages")          
                    await websocket.send_json(ballvel_pkgs)
                    ballvel_pkgs.clear()
                    t0 = time.time()             
                       
                    
        except:
            pass
        finally:
            ballvel_shm.close_shm()
            websocket.close()
    
    
    @app.websocket("/stream/portentaoutput")
    async def stream_portentaoutput(websocket: WebSocket):
        validate_state(app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          },
                       # either one of these should be running but validate_state doesn't allow that yet
                       valid_proc_running={
                                        #    "por2shm2por_sim": True,
                                        #    "por2shm2por": True,   
                                           })
        
        L = Logger()
        portentaout_shm = CyclicPackagesSHMInterface(shm_struct_fname(P.SHM_NAME_PORTENTA_OUTPUT))
        while portentaout_shm.popitem():
            pass
        await websocket.accept()
        try:
            ballvel_pkgs = []
            t0 = time.time()
            while True:
                await asyncio.sleep(0.020) # check memory every 1ms
                if portentaout_shm.usage > 0:
                    pack = portentaout_shm.popitem(return_type=dict)
                    ballvel_pkgs.append(pack)
                else:
                    continue
                    
                if portentaout_shm.usage>10:
                    L.logger.info(f"sending lick too slowly: {portentaout_shm.usage}")
                if  ballvel_pkgs and time.time() - t0 > 0.0333333: # 30 packages a second
                    L.logger.info(f"sending {len(ballvel_pkgs)} packages")          
                    await websocket.send_json(ballvel_pkgs)
                    ballvel_pkgs.clear()
                    t0 = time.time()
                    
        except:
            pass
        finally:
            portentaout_shm.close_shm()
            websocket.close()
    
    @app.websocket("/stream/unityoutput")
    async def stream_unityoutput(websocket: WebSocket):
        validate_state(app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_UNITY_OUTPUT: True},
                       valid_proc_running=None)
                    #    valid_proc_running={"unity": True,})
        
        L = Logger()
        unityout_shm = CyclicPackagesSHMInterface(shm_struct_fname(P.SHM_NAME_UNITY_OUTPUT))
        await websocket.accept()
        while unityout_shm.popitem():
            pass
        try:
            unity_pkgs = []
            t0 = time.time()                
            while True:
                await asyncio.sleep(0.01) # check memory every 10ms
                if unityout_shm.usage > 0:
                    pack = unityout_shm.popitem(return_type=dict)
                    unity_pkgs.append(pack)
                    
                if unityout_shm.usage>10:
                    L.logger.debug(f"sending to slowly: {unityout_shm.usage}")
                if  unity_pkgs and time.time() - t0 > 0.0333333: # sending packge pack every 30ms
                    L.logger.debug(f"sending {len(unity_pkgs)} packages")
                    await websocket.send_json(unity_pkgs)
                    unity_pkgs.clear()
                    t0 = time.time()                
                    
        except:
            pass
        finally:
            unityout_shm.close_shm()
            websocket.close()
    
    @app.websocket("/stream/portentainput")
    async def stream_unityoutput(websocket: WebSocket):
        validate_state(app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_PORTENTA_INPUT: True},
                       valid_proc_running=None)
        
        L = Logger()
        portentainput_shm = CyclicPackagesSHMInterface(shm_struct_fname(P.SHM_NAME_PORTENTA_INPUT))
        await websocket.accept()
        while portentainput_shm.popitem():
            pass
        try:
            while True:
                await asyncio.sleep(0.1) # check memory every 100ms
                if portentainput_shm.usage > 0:
                    portenta_cmd = portentainput_shm.popitem(return_type=str)
                    await websocket.send_json(portenta_cmd)
                    
        except:
            pass
        finally:
            portentainput_shm.close_shm()
            websocket.close()
        
    @app.websocket("/stream/bodycam")
    async def stream_unityoutput(websocket: WebSocket):
        validate_state(app.state.state, valid_initiated=True, 
                    valid_shm_created={P.SHM_NAME_BODY_CAM: True},
                    valid_proc_running={"bodycam2shm": True,})
        
        L = Logger()
        frame_shm = VideoFrameSHMInterface(shm_struct_fname(P.SHM_NAME_BODY_CAM))
        
        await websocket.accept()
        
        prv_frame_package = b''
        try:
            t0 = time.time()                
            while True:
                await asyncio.sleep(0.01) # check memory every 10ms
                L.logger.debug(f"Checking for new frame")
                # wait until new frame is available
                if (frame_package := frame_shm.get_package()) == prv_frame_package:
                    L.logger.debug(f"Same package: {frame_package}")
                    continue
                prv_frame_package = frame_package

                frame = frame_shm.get_frame()
                L.logger.debug(f"New frame {frame.shape} read from SHM: {frame_package}")
                
                frame_encoded = cv2.imencode('.jpg', frame)[1].tobytes()  # Encode the frame as JPEG
                await websocket.send_bytes(frame_encoded)  # Send the encoded frame
        except Exception as e:
            L.logger.warning(f"Error in bodycam stream: {e}")
        finally:
            # frame_shm.close_shm()
            websocket.close()

    @app.websocket("/stream/facecam")
    async def stream_unityoutput(websocket: WebSocket):
        validate_state(app.state.state, valid_initiated=True, 
                    valid_shm_created={P.SHM_NAME_FACE_CAM: True},
                    valid_proc_running={"facecam2shm": True,})
        
        L = Logger()
        frame_shm = VideoFrameSHMInterface(shm_struct_fname(P.SHM_NAME_FACE_CAM))
        
        await websocket.accept()
        
        prv_frame_package = b''
        try:
            t0 = time.time()                
            while True:
                await asyncio.sleep(0.01) # check memory every 10ms
                
                # wait until new frame is available
                if (frame_package := frame_shm.get_package()) == prv_frame_package:
                    continue
                prv_frame_package = frame_package

                frame = frame_shm.get_frame()
                L.logger.debug(f"New frame {frame.shape} read from SHM: {frame_package}")
                
                frame_encoded = cv2.imencode('.jpg', frame)[1].tobytes()  # Encode the frame as JPEG
                await websocket.send_bytes(frame_encoded)  # Send the encoded frame
        except:
            pass
        finally:
            # frame_shm.close_shm()
            websocket.close()

    @app.websocket("/stream/unitycam")
    async def stream_unityoutput(websocket: WebSocket):
        validate_state(app.state.state, valid_initiated=True, 
                    valid_shm_created={P.SHM_NAME_UNITY_CAM: True},
                    valid_proc_running={"unity": True,})
        
        L = Logger()
        frame_shm = VideoFrameSHMInterface(shm_struct_fname(P.SHM_NAME_UNITY_CAM))
        
        await websocket.accept()
        
        prv_frame_package = b''
        try:
            t0 = time.time()                
            while True:
                await asyncio.sleep(0.01) # check memory every 10ms
                
                # wait until new frame is available
                if (frame_package := frame_shm.get_package()) == prv_frame_package:
                    continue
                prv_frame_package = frame_package
                
                frame = cv2.flip(frame_shm.get_frame(), 0)
                # frame = cv2.flip(frame)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                L.logger.debug(f"New frame {frame.shape} read from SHM: {frame_package}")
                
                frame_encoded = cv2.imencode('.jpg', frame)[1].tobytes()  # Encode the frame as JPEG
                await websocket.send_bytes(frame_encoded)  # Send the encoded frame
        except:
            pass
        finally:
            # frame_shm.close_shm()
            websocket.close() 
    
    @app.websocket("/stream/logfiless")
    async def stream_unityoutput(websocket: WebSocket):
        P = Parameters()
        validate_state(app.state.state, valid_initiated=True)
        
        L = Logger()
        
        await websocket.accept()
        logfile_content = {}
        new_logfile_content = {}
        try:
            while True:
                await asyncio.sleep(1)
                # logfile_names = [fname for fname in os.listdir(P.SESSION_DATA_DIRECTORY) if fname.endswith(".log")]
                logfile_names = glob.glob(P.SESSION_DATA_DIRECTORY+"/*.log")
                # L.logger.info(f"Logfiles: {[os.path.basename(f) for f in logfile_names]}")
                for logfile_name in logfile_names:
                    # L.logger.info(logfile_name)
                    with open(logfile_name, 'r') as logfile:
                        logfile_content[os.path.basename(logfile_name)] = logfile.read()
                        # if logfile_name in logfile_content:
                        #     cur_content = logfile_content[logfile_name]
                        # else:
                        #     cur_content = ""
                        #     logfile_content[logfile_name] = cur_content
                        # new_logfile_content[logfile_name] = logfile.read()[len(cur_content):]
                    # await websocket.send_text(logfile_content[logfile_name])
                
                # L.logger.info(f"New logfiles: {logfile_content}")
                await websocket.send_json(logfile_content)  # Send the encoded frame
        except:
            pass
        finally:
            websocket.close() 