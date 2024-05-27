from fastapi import WebSocket
from fastapi import HTTPException, Request
from starlette.types import Scope

import asyncio
import time
from CustomLogger import CustomLogger as Logger

from Parameters import Parameters
from backend_helpers import validate_state
from requests import request

import process_launcher as pl
from process_launcher import shm_struct_fname
from SHM.CyclicPackagesSHMInterface import CyclicPackagesSHMInterface

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
                await asyncio.sleep(0.00001) # check memory every 1ms
                if ballvel_shm.usage > 0:
                    pack = ballvel_shm.popitem(return_type=dict)
                    ryp = dict(zip(("raw", "yaw", "pitch"), 
                                   [int(v) for v in pack.pop("V").split("_")]))
                    ballvel_pkgs.append({**pack, **ryp})
                    
                if ballvel_shm.usage>10:
                    L.logger.warning(f"sending ball vell too slowly: {ballvel_shm.usage}")
                if  time.time() - t0 > 0.0333333: # 30 packages a second
                    # L.logger.info(f"sending {len(ballvel_pkgs)} packages")          
                    await websocket.send_json(ballvel_pkgs)
                    ballvel_pkgs.clear()
                    t0 = time.time()             
                    await asyncio.sleep(0.0005) # check memory every 1ms
                       
                    
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
                await asyncio.sleep(0.001) # check memory every 1ms
                if portentaout_shm.usage > 0:
                    pack = portentaout_shm.popitem(return_type=dict)
                    ballvel_pkgs.append(pack)
                    
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