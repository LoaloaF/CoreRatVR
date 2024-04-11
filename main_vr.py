import os
import signal
import sys
sys.path.insert(1, os.path.join(sys.path[0], 'SHM'))

from time import sleep
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles

import logging
import uvicorn
from typing import Any
import subprocess

from Parameters import Parameters
from CustomLogger import CustomLogger as Logger

from backend_helpers import patch_parameter
from backend_helpers import init_save_dir
from backend_helpers import check_base_dirs
from backend_helpers import init_logger
from backend_helpers import validate_state

from process_launcher import shm_struct_fname

import process_launcher as pl
import SHM.shm_creation as sc

from SHM.FlagSHMInterface import FlagSHMInterface
from SHM.CyclicPackagesSHMInterface import CyclicPackagesSHMInterface

from SHM.shm_creation import delete_shm


def attach_endpoints(app):
    # singlton class - reference to instance created in lifespan
    P = Parameters()

    # @app.exception_handler(Exception)
    # async def global_exception_handler(request, exc):
    #     L = Logger()
    #     L.spacer()
    #     L.logger.error(exc)
    #     L.spacer()
    #     os.kill(os.getpid(), signal.SIGINT)  # Terminate the server
    #     raise HTTPException(status_code=500, 
    #                         detail=f"Server error:{exc} Terminating server.")
    
    @app.get("/state")
    def get_state(request: Request):
        S = request.app.state.state.copy()
        S['termflag_shm_interface'] = False if S['termflag_shm_interface'] is None else True
        S['unityinput_shm_interface'] = False if S['unityinput_shm_interface'] is None else True
        return S

    @app.get("/parameters")
    def get_parameters():
        return P.get_attributes()
    
    @app.get("/parameters/locked")
    def locked_parameters():
        return P.get_locked_parameters()
    
    @app.get("/parameters/groups")
    def grouped_parameters():
        return P.get_parameter_groups()

    @app.patch("/parameters/{key}")
    async def update_parameter(key: str, new_value: Any, request: Request):
        return patch_parameter(key, new_value, 
                               request.app.state.state["initiated"])

    @app.post("/initiate")
    def initiate(request: Request):
        validate_state(app.state.state, valid_initiated=False)
        session_save_dir = check_base_dirs()
        session_save_dir = init_save_dir()
        logging_dir = init_logger(session_save_dir)
        P.SESSION_DATA_DIRECTORY = session_save_dir
        P.LOGGING_DIRECTORY = logging_dir
        P.save_to_json(P.SESSION_DATA_DIRECTORY)
        request.app.state.state["initiated"] = True

        L = Logger()
        L.spacer()
        L.logger.info("Session initiated.")
        L.logger.debug(L.fmtmsg(["Parameters", str(Parameters())]))
        L.spacer()
    
    @app.post("/flash_portenta/{core}")
    def flash_portenta(request: Request, core: str):
        validate_state(request.app.state.state, valid_initiated=True)
        command = (f"{P.PLATFORMIO_BIN} run --target upload --environment "
                   f"portenta_h7_{core} --project-dir "
                   f"{os.path.join(P.PROJECT_DIRECTORY, 'ArduinoRatVR')}")

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        result = (f"Flashed Portenta: {command}\nSTDOUT: {stdout.decode()}\n"
                  f"STDERR: {stderr.decode()}")
        Logger().logger.debug(result)

        if "FAILED" in stderr.decode():
            raise HTTPException(status_code=400, detail=f"Failed to flash Portenta")
        return True

    @app.post("/unityinput/{msg}")
    def unityinput(msg: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                           P.SHM_NAME_UNITY_INPUT: True,
                                           })
        request.app.state.state["unityinput_shm_interface"].push(msg.encode())
    
    @app.post("/raise_term_flag")
    def raise_term_flag(request: Request):
        L = Logger()
        L.logger.warning("procs_state")

        validate_state(request.app.state.state, valid_initiated=True, 
                valid_shm_created={P.SHM_NAME_TERM_FLAG: True})
        shm_state = request.app.state.state['shm']
        procs_state = request.app.state.state['procs']
        termflag_shm_interface = request.app.state.state["termflag_shm_interface"]
        unityinput_shm_interface = request.app.state.state["unityinput_shm_interface"]
        
        # send termination flag to all processes
        termflag_shm_interface.set()
        # reset the termination flag interface
        termflag_shm_interface.close_shm()
        request.app.state.state["termflag_shm_interface"] = None
        
        request.app.state.state['procs'].update({proc_name: 0 for proc_name in procs_state.keys()})
        L.logger.info(request.app.state.state['procs'])

        # delete all shared memory
        sleep(1)
        for shm_name, shm_created in shm_state.items():
            if shm_created:
                delete_shm(shm_name)
                request.app.state.state["shm"][shm_name] = False

                # special interface that is used by the main process
                if shm_name == "unityinput_shm_interface":
                    unityinput_shm_interface.close_shm()
                    request.app.state.state["unityinput_shm_interface"] = None
        request.app.state.state["initiated"] = False




    ############################################################################
    ############################## create SHM ##################################
    ############################################################################

    @app.post("/shm/create_termflag_shm")
    def create_termflag_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: False})
        sc.create_singlebyte_shm(shm_name=P.SHM_NAME_TERM_FLAG)
        request.app.state.state["shm"][P.SHM_NAME_TERM_FLAG] = True

        # create an interface for closing procesces
        shm_interface = FlagSHMInterface(shm_struct_fname(P.SHM_NAME_TERM_FLAG))
        request.app.state.state["termflag_shm_interface"] = shm_interface


    @app.post("/shm/create_ballvelocity_shm")
    def create_ballvelocity_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_BALLVELOCITY: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_BALLVELOCITY, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_BALLVELOCITY, 
                                      npackages=P.SHM_NPACKAGES_BALLVELOCITY)
        request.app.state.state["shm"][P.SHM_NAME_BALLVELOCITY] = True
    
    @app.post("/shm/create_portentaoutput_shm")
    def create_portentaoutput_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_PORTENTA_OUTPUT: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_PORTENTA_OUTPUT, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_PORTENTA_OUTPUT, 
                                      npackages=P.SHM_NPACKAGES_PORTENTA_OUTPUT)
        request.app.state.state["shm"][P.SHM_NAME_PORTENTA_OUTPUT] = True
        
    @app.post("/shm/create_portentainput_shm")
    def create_portentainput_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_PORTENTA_INPUT: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_PORTENTA_INPUT, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_PORTENTA_INPUT, 
                                      npackages=P.SHM_NPACKAGES_PORTENTA_INPUT)
        request.app.state.state["shm"][P.SHM_NAME_PORTENTA_INPUT] = True
    
    @app.post("/shm/create_unityinput_shm")
    def create_unityinput_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_UNITY_INPUT: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_UNITY_INPUT, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_UNITY_INPUT,
                                      npackages=P.SHM_NPACKAGES_UNITY_INPUT)
        request.app.state.state["shm"][P.SHM_NAME_UNITY_INPUT] = True

        # create an interface for writing commands to shm (read by Unity)
        shm_interface = CyclicPackagesSHMInterface(shm_struct_fname(P.SHM_NAME_UNITY_INPUT))
        request.app.state.state["unityinput_shm_interface"] = shm_interface
    
    @app.post("/shm/create_unityoutput_shm")
    def create_unityoutput_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_UNITY_OUTPUT: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_UNITY_OUTPUT, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_UNITY_OUTPUT,
                                      npackages=P.SHM_NPACKAGES_UNITY_OUTPUT)
        request.app.state.state["shm"][P.SHM_NAME_UNITY_OUTPUT] = True


    @app.post("/shm/create_facecam_shm")
    def create_facecam_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_FACE_CAM: False})
        sc.create_video_frame_shm(shm_name=P.SHM_NAME_FACE_CAM, 
                                  x_resolution=P.FACE_CAM_X_RES,
                                  y_resolution=P.FACE_CAM_Y_RES,
                                  nchannels=P.FACE_CAM_NCHANNELS)
        request.app.state.state["shm"][P.SHM_NAME_FACE_CAM] = True

    @app.post("/shm/create_bodycam_shm")
    def create_bodycam_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_BODY_CAM: False})
        sc.create_video_frame_shm(shm_name=P.SHM_NAME_BODY_CAM, 
                                  x_resolution=P.BODY_CAM_X_RES,
                                  y_resolution=P.BODY_CAM_Y_RES,
                                  nchannels=P.BODY_CAM_NCHANNELS)
        request.app.state.state["shm"][P.SHM_NAME_BODY_CAM] = True
    
    @app.post("/shm/create_unitycam_shm")
    def create_unitycam_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_UNITY_CAM: False})
        sc.create_video_frame_shm(shm_name=P.SHM_NAME_UNITY_CAM, 
                                  x_resolution=P.UNITY_CAM_X_RES,
                                  y_resolution=P.UNITY_CAM_Y_RES,
                                  nchannels=P.UNITY_CAM_NCHANNELS)
        request.app.state.state["shm"][P.SHM_NAME_UNITY_CAM] = True




    ############################################################################
    ############################## create procs ################################
    ############################################################################
        
    @app.post("/procs/launch_por2shm2por_sim")
    def launch_por2shm2por_sim(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          P.SHM_NAME_BALLVELOCITY: True,
                                          })
        proc = pl.open_por2shm2por_sim_proc()
        request.app.state.state["procs"]["por2shm2por_sim"] = proc.pid

    @app.post("/procs/launch_por2shm2por")
    def launch_por2shm2por(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          P.SHM_NAME_BALLVELOCITY: True,
                                          P.SHM_NAME_PORTENTA_INPUT: True,
                                          })
        proc = pl.open_por2shm2por_proc()
        request.app.state.state["procs"]["por2shm2por"] = proc.pid
        
    @app.post("/procs/launch_log_portenta")
    def launch_log_portenta(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          P.SHM_NAME_BALLVELOCITY: True,
                                          })
        proc = pl.open_log_portenta_proc()
        request.app.state.state["procs"]["log_portenta"] = proc.pid

    @app.post("/procs/launch_stream_portenta")
    def launch_stream_portenta(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          P.SHM_NAME_BALLVELOCITY: True,
                                          })
        proc = pl.open_stream_portenta_proc()
        request.app.state.state["procs"]["stream_portenta"] = proc.pid
    
    @app.post("/procs/launch_facecam2shm")
    def launch_facecam2shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_FACE_CAM: True,
                                          })
        proc = pl.open_camera2shm_proc(P.SHM_NAME_FACE_CAM)
        request.app.state.state["procs"]["facecam2shm"] = proc.pid
    
    @app.post("/procs/launch_bodycam2shm")
    def launch_bodycam2shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_BODY_CAM: True,
                                          })
        proc = pl.open_camera2shm_proc(P.SHM_NAME_BODY_CAM)
        request.app.state.state["procs"]["bodycam2shm"] = proc.pid
    
    @app.post("/procs/launch_stream_facecam")
    def launch_stream_facecam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_FACE_CAM: True,
                                          })
        proc = pl.open_shm2cam_stream_proc(P.SHM_NAME_FACE_CAM)
        request.app.state.state["procs"]["stream_facecam"] = proc.pid

    @app.post("/procs/launch_log_facecam")
    def launch_log_facecam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_FACE_CAM: True,
                                          })
        proc = pl.open_log_camera_proc(P.SHM_NAME_FACE_CAM)
        request.app.state.state["procs"]["log_facecam"] = proc.pid
    
    @app.post("/procs/launch_log_bodycam")
    def launch_log_bodycam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_BODY_CAM: True,
                                          })
        proc = pl.open_log_camera_proc(P.SHM_NAME_BODY_CAM)
        request.app.state.state["procs"]["log_bodycam"] = proc.pid
    
    @app.post("/procs/launch_stream_bodycam")
    def launch_stream_bodycam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_BODY_CAM: True,
                                          })
        proc = pl.open_shm2cam_stream_proc(P.SHM_NAME_BODY_CAM)
        request.app.state.state["procs"]["stream_bodycam"] = proc.pid
    
    @app.post("/procs/launch_log_unity")
    def launch_log_unity(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_UNITY_OUTPUT: True,
                                          })
        proc = pl.open_log_unity_proc()
        request.app.state.state["procs"]["log_unity"] = proc.pid

    @app.post("/procs/launch_log_unitycam")
    def launch_log_unitycam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_UNITY_CAM: True,
                                          })
        proc = pl.open_log_camera_proc(P.SHM_NAME_UNITY_CAM)
        request.app.state.state["procs"]["log_unitycam"] = proc.pid
    
    return app

def attach_UI_endpoint(app):
    @app.get("/ui")
    async def root():
        if os.path.isfile('./../UIRatVR/dist/index.html'):
            return FileResponse('./../UIRatVR/dist/index.html')
        else:
            raise HTTPException(status_code=404)

    # # Mount the 'dist' directory at the root of your app
    app.mount("/ui", StaticFiles(directory="./../UIRatVR/dist"), name="dist")
    app.mount("/assets", StaticFiles(directory="./../UIRatVR/dist/assets"), 
              name="assets")

async def lifespan(app: FastAPI):
    print("Initilizing server state, constructing parameters...")
    P = Parameters()
    app.state.state = {
        "procs": {
            "por2shm2por_sim": 0,
            "por2shm2por": 0,
            "log_portenta": 0,
            "stream_portenta": 0,
            "facecam2shm": 0,
            "bodycam2shm": 0,
            "stream_facecam": 0,
            "log_facecam": 0,
            "log_bodycam": 0,
            "stream_bodycam": 0,
            "log_unity": 0,
            "log_unitycam": 0,
        },
        "shm": {
            P.SHM_NAME_TERM_FLAG: False,
            P.SHM_NAME_BALLVELOCITY: False,
            P.SHM_NAME_PORTENTA_OUTPUT: False,
            P.SHM_NAME_PORTENTA_INPUT: False,
            P.SHM_NAME_UNITY_OUTPUT: False,
            P.SHM_NAME_UNITY_INPUT: False,
            P.SHM_NAME_FACE_CAM: False,
            P.SHM_NAME_BODY_CAM: False,
            P.SHM_NAME_UNITY_CAM: False,
        },
        "initiated": False,
        "termflag_shm_interface": None,
        "unityinput_shm_interface": None,
    }
    yield # application runs (function pauses here)
    print("Experiment Server shutting down.")

def main():
    app = FastAPI(lifespan=lifespan)

    origins = [
    "http://localhost:8000",  # Uncomment this if your FastAPI server is running on localhost
    "http://localhost:5173",  # Allow the Svelte dev server access
    # "http://localhost:tld",  # Replace "tld" with the top-level domain where your app will be hosted
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    attach_UI_endpoint(app)
    attach_endpoints(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()