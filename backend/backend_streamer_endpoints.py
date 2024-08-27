import os
import h5py
import pandas as pd
from fastapi import WebSocket, Query
from fastapi import HTTPException, Request
from starlette.types import Scope
from starlette.websockets import WebSocketDisconnect

import base64

import glob
import asyncio
import time
import cv2
from CustomLogger import CustomLogger as Logger

from Parameters import Parameters
from backend_helpers import validate_state
from requests import request

import process_launcher as pl
from backend.backend_helpers import shm_struct_fname
from SHM.CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from SHM.VideoFrameSHMInterface import VideoFrameSHMInterface

from backend_helpers import access_session_data

def attach_stream_endpoints(app):
    # singlton class - reference to instance created in lifespan
    P = Parameters()

    @app.websocket("/stream/unityoutput")
    async def stream_bodycam(websocket: WebSocket, inspect: str = Query("false")):
        P = Parameters()
        inspect = inspect.lower() == "true"
        # every 10ms, pop a max of 10 unity packages (expected at 60Hz)
        check_interval = 0.01
        maxpops = 6
        data_name = "unity_frame"
        shm_name = P.SHM_NAME_UNITY_OUTPUT
        await _stream_packages_loop(inspect, websocket, app, data_name, shm_name, 
                                    check_interval=check_interval, maxpops=maxpops)
        
    @app.websocket("/stream/ballvelocity")
    async def stream_ballvelocity(websocket: WebSocket, inspect: str = Query("false")):
        P = Parameters()
        inspect = inspect.lower() == "true"
        # every 10ms, pop a max of 30 ballvelocity packages (expected at 1500Hz)
        check_interval = 0.01
        maxpops = 30
        data_name = "ballvelocity"
        shm_name = P.SHM_NAME_BALLVELOCITY
        await _stream_packages_loop(inspect, websocket, app, data_name, shm_name, 
                                    check_interval=check_interval, maxpops=maxpops)

    @app.websocket("/stream/portentaoutput")
    async def stream_portentaoutput(websocket: WebSocket, inspect: str = Query("false")):
        P = Parameters()
        inspect = inspect.lower() == "true"
        # every 20ms, pop a max of 20 event packages (async, max ~1000Hz, shortly)
        check_interval = 0.02
        maxpops = 20
        data_name = "event"
        shm_name = P.SHM_NAME_PORTENTA_OUTPUT
        await _stream_packages_loop(inspect, websocket, app, data_name, shm_name, 
                                    check_interval=check_interval, maxpops=maxpops)
        
    @app.websocket("/stream/bodycam")
    async def stream_bodycam(websocket: WebSocket, inspect: str = Query("false")):
        inspect = inspect.lower() == "true"
        cam_name = "bodycam"
        check_interval = 0.01
        await _stream_cam_loop(inspect, websocket, cam_name, app, 
                               check_interval=check_interval)
        
    @app.websocket("/stream/facecam")
    async def stream_facecam(websocket: WebSocket, inspect: str = Query("false")):
        inspect = inspect.lower() == "true"
        cam_name = "facecam"
        check_interval = 0.01
        await _stream_cam_loop(inspect, websocket, cam_name, app, 
                               check_interval=check_interval)
        
    @app.websocket("/stream/unitycam")
    async def stream_unitycam(websocket: WebSocket, inspect: str = Query("false")):
        inspect = inspect.lower() == "true"
        cam_name = "unitycam"
        check_interval = 0.01
        await _stream_cam_loop(inspect, websocket, cam_name, app, 
                               check_interval=check_interval)
    
    # this steam is only used for reward delivery tracking
    @app.websocket("/stream/portentainput")
    async def stream_portentainput(websocket: WebSocket):
        L = Logger()
        check_interval = 0.1
        
        validate_state(app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_PORTENTA_INPUT: True},
                       valid_proc_running=None)
        await websocket.accept()

        portentainput_shm = CyclicPackagesSHMInterface(shm_struct_fname(P.SHM_NAME_PORTENTA_INPUT))
        # clear the memory
        while portentainput_shm.popitem(): pass
        
        try:
            while True:
                await asyncio.sleep(check_interval) # check memory every 100ms
                if portentainput_shm.usage > 0:
                    portenta_cmd = portentainput_shm.popitem(return_type=str)
                    await websocket.send_json(portenta_cmd)
        except WebSocketDisconnect:
            L.logger.info(f"Client disconnected from portentainput weboscket")
        except Exception as e:
            L.logger.error(f"Error in portentainput stream: {e}")
        finally:
            portentainput_shm.close_shm()
    
    @app.websocket("/stream/logfiles")
    async def stream_logfiles(websocket: WebSocket):
        P = Parameters()
        L = Logger()
        check_interval = 1
        
        validate_state(app.state.state, valid_initiated=True)
        await websocket.accept()
        
        logfile_content = {}
        try:
            while True:
                await asyncio.sleep(check_interval)
                logfile_names = glob.glob(os.path.join(P.SESSION_DATA_DIRECTORY, "/*.log"))
                
                for logfile_name in logfile_names:
                    with open(logfile_name, 'rb+') as logfile:
                        if os.path.getsize(logfile_name) > 300_000:  # 300KB
                            # L.logger.info(f"Logfile {logfile_name} is too large. Truncating...")
                            logfile.seek(0)
                            content = logfile.read(150_000).decode('utf-8')  
                            logfile.seek(-150_000, os.SEEK_END)
                            content += "\n\n\n...\n\n\n" + logfile.read().decode('utf-8')  
                            
                        else:
                            content = logfile.read().decode('utf-8') 
                        logfile_content[os.path.basename(logfile_name)] = content
                await websocket.send_json(logfile_content)

        except WebSocketDisconnect:
            L.logger.info(f"Client disconnected from logfiles weboscket")
        except Exception as e:
            L.logger.warning(f"Error in logfiles stream: {e}")
            






# stream helpers
def _access_shm(shm_name, matching_proc, app):
    validate_state(app.state.state, valid_initiated=True, 
                valid_shm_created={shm_name: True},
                valid_proc_running=None if matching_proc is None else {matching_proc: True,})
    if "cam" in shm_name:
        return VideoFrameSHMInterface(shm_struct_fname(shm_name))
    elif shm_name in ("ballvelocity", "portentaoutput", "portentainput", "unityoutput"):
        return CyclicPackagesSHMInterface(shm_struct_fname(shm_name))
    
def _inspect_get_frame(requested_PCT, packages, sessionfile, cam_name):
    L = Logger()
    closest_timepoint = packages.index.asof(requested_PCT)
    if closest_timepoint is pd.NaT:
        L.logger.error(f"Requested time is before session start")
        return

    frame_pkg = packages.loc[closest_timepoint].fillna("null").rename({
        f"{cam_name}_image_id": "ID",
        f"{cam_name}_image_pc_timestamp": "PCT",
    }).to_dict()
    frame_key = f"frame_{int(frame_pkg['ID']):06d}"
    return (sessionfile[f"{cam_name}_frames"][frame_key][()]).item(), frame_pkg

def _live_get_frame(shm, prv_frame_package):
    L = Logger()
    L.logger.debug(f"Checking for new frame")
    if (frame_package := shm.get_package(dict)) == prv_frame_package:
        L.logger.debug(f"Same package: {frame_package}")
        return None, prv_frame_package
    
    frame_jpg = shm.get_frame()
    L.logger.debug(f"New frame {frame_jpg.shape} read from SHM: {frame_package}")
    return cv2.imencode('.jpg', frame_jpg)[1].tobytes(), frame_package

async def _stream_cam_loop(inspect, websocket, cam_name, app, check_interval=0.01):
    L = Logger()
    P = Parameters()
        
    # initialize for either viewing a recordded session or stream live from memory    
    if not inspect:
        if cam_name == "facecam":
            shm = _access_shm(P.SHM_NAME_FACE_CAM, "facecam2shm", app)
        elif cam_name == "bodycam":
            shm = _access_shm(P.SHM_NAME_BODY_CAM, "bodycam2shm", app)
        elif cam_name == "unitycam":
            shm = _access_shm(P.SHM_NAME_UNITY_CAM, "unity", app)
    else:
        validate_state(app.state.state, valid_initiated_inspect=True)
        packages, sessionfile = access_session_data(f"{cam_name}_packages")
    await websocket.accept()

    frame_package = {}
    try: 
        while True:
            await asyncio.sleep(check_interval)
                        
            if inspect:
                # index the recorded session with the requested pc timestamp
                t = int(await websocket.receive_text())
                requested_PCT = pd.to_datetime(t, unit='us')
                frame_jpg, frame_package = _inspect_get_frame(requested_PCT, packages, 
                                                              sessionfile, cam_name)
            else:
                # stream live from memory
                frame_jpg, frame_package = _live_get_frame(shm, frame_package)
                if frame_jpg is None:
                    continue

            await websocket.send_bytes(frame_jpg)  # Send the encoded frame
            await websocket.send_json(frame_package)  # Send the encoded frame
    
    except WebSocketDisconnect:
        L.logger.info(f"Client disconnected from {cam_name} weboscket")
    except Exception as e:
        L.logger.warning(f"Error in {cam_name} stream: {e}")
    finally:
        if not inspect:
            shm.close_shm()
        else:
            sessionfile.close()

async def _stream_packages_loop(inspect, websocket, app, data_name, shm_name, 
                                check_interval=0.01, maxpops=3):
    L = Logger()
    try: 
        # initialize for either viewing a recordded session or stream live from memory    
        if not inspect:
            shm = _access_shm(shm_name, None, app)
            shm.reset_reader() 
            await websocket.accept()
            
        else:
            validate_state(app.state.state, valid_initiated_inspect=True)
            await websocket.accept()
            data = access_session_data(data_name, na2null=True, rename2oldkeys=True)
            L.logger.info(f"{data_name} data: {", ".join(data.columns)}\n\n{data}")
        
        packages = []
        t0 = 0
        while True:
            await asyncio.sleep(check_interval)  # check memory every 10ms
            if inspect:
                # # index the recorded session with the requested pc timestamp
                start_t, stop_t = (await websocket.receive_text()).split(",")
                requested_start_PCT = pd.to_datetime(int(start_t), unit='us')
                requested_stop_PCT = pd.to_datetime(int(stop_t), unit='us')
                L.logger.debug(f"Requested PCT for {data_name}: "
                               f"{requested_start_PCT} to {requested_stop_PCT}")
                try:
                    requested_interval = data.loc[requested_start_PCT:requested_stop_PCT]
                except Exception as e:
                    L.logger.error(e)
                    continue
                packages = requested_interval.to_dict(orient='records')
            else:
                # stream live from memory
                i = 0 
                while shm.usage > 0 and i < maxpops: # pop maxpops packages at a time
                    pack = shm.popitem(return_type=dict)
                    if data_name == "ballvelocity":
                        ryp = dict(zip(("raw", "yaw", "pitch"), 
                                    [int(v) for v in pack.pop("V").split("_")]))
                        pack = {**pack, **ryp}
                    packages.append(pack)
                    i += 1
                    
                if shm.usage>100 and (time.time()-t0) >3: # max every 3s
                    L.logger.warning(f"sending {shm_name} too slowly: {shm.usage}")
                    t0 = time.time()
                    
            if packages:
                L.logger.debug(f"sending {len(packages)} packages")
                await websocket.send_json(packages)
                packages.clear()
                
    except WebSocketDisconnect:
        L.logger.info(f"Client disconnected from {shm_name} weboscket")
    except Exception as e:
        L.logger.error(f"Error in {shm_name} stream: {e}")
    finally:
        if not inspect:
            shm.close_shm()