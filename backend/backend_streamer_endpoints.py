from fastapi import WebSocket
from fastapi import HTTPException, Request
from starlette.types import Scope

import asyncio

from Parameters import Parameters
from backend_helpers import validate_state
from requests import request

import process_launcher as pl
from process_launcher import shm_struct_fname
from SHM.CyclicPackagesSHMInterface import CyclicPackagesSHMInterface

def attach_stream_endpoints(app):
    # singlton class - reference to instance created in lifespan
    P = Parameters()
    print("IN")
    
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
        
        ballvel_shm = CyclicPackagesSHMInterface(shm_struct_fname(P.SHM_NAME_BALLVELOCITY))
        await websocket.accept()
        try:
            ballvel_pkgs = []
            while True:
                if ballvel_shm.usage > 0:
                    ballvel_pkgs.append(ballvel_shm.popitem(return_type=dict))
                    
                if len(ballvel_pkgs) >= 10:
                    await websocket.send_json(ballvel_pkgs)
                    ballvel_pkgs.clear()
                await asyncio.sleep(0.001)
        except:
            pass
        finally:
            ballvel_shm.close_shm()
            websocket.close()