import os
import asyncio
import sys
sys.path.insert(1, os.path.join(sys.path[0], 'SHM'))
sys.path.insert(1, os.path.join(sys.path[0], 'backend'))

from time import sleep
import json
from fastapi import HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from typing import Any
import subprocess

from Parameters import Parameters
from SessionParamters import SessionParamters
from CustomLogger import CustomLogger as Logger

from backend_helpers import patch_parameter
from backend_helpers import init_save_dir
from backend_helpers import check_base_dirs
from backend_helpers import init_logger
from backend_helpers import validate_state
from backend_helpers import check_processes
from backend_helpers import state2serializable

from SHM.shm_creation import delete_shm


def attach_general_endpoints(app):
    # singlton class - reference to instance created in lifespan
    P = Parameters()
    session_paramters = SessionParamters()

    @app.get('/statestream')
    async def message_stream(request: Request):
        STREAM_DELAY = .1  # second
        async def event_generator():
            prv_state = None
            while True:
                # If client closes connection, stop sending events
                if await request.is_disconnected():
                    break

                # Checks if state has changed or first time request
                check_processes(request.app)
                cur_state = state2serializable(request.app.state.state)
                if prv_state is None or prv_state != cur_state:
                    prv_state = cur_state#.copy()
                    yield {"data": cur_state}
                
                await asyncio.sleep(STREAM_DELAY)
        return EventSourceResponse(event_generator())
            
    @app.get("/state")
    def get_state(request: Request):
        return state2serializable(request.app.state.state)

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
                       valid_shm_created={P.SHM_NAME_UNITY_INPUT: True,
                                          })
        if msg.startswith("Paradigm,"):
            session_paramters.paradigm_name = msg.split(",")[1]
        if msg == "Start":
            request.app.state.state["unitySessionRunning"] = True
            session_paramters.handle_start_session()
        elif msg == "Stop":
            request.app.state.state["unitySessionRunning"] = False
            session_paramters.handle_stop_session()
        request.app.state.state["unityinput_shm_interface"].push(msg.encode())
    
    @app.post("/raise_term_flag")
    def raise_term_flag(request: Request):
        Logger().logger.debug("Handling raised term flag")

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

        session_paramters.clear()

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
        P.SESSION_DATA_DIRECTORY = "set-at-init"
        request.app.state.state["initiated"] = False

    @app.get("/paradigms")
    def paradigms():
        dirname = os.path.join(P.PROJECT_DIRECTORY, "UnityRatVR", "Paradigms")
        paradigms = [f for f in os.listdir(dirname) if f.endswith(".xlsx")]
        return paradigms

    @app.get("/animals")
    def animals():
        static_animals = ["rYL_001","rYL_002","rYL_003","rYL_004","rYL_005"]
        return static_animals

    @app.get("/paradigm_fsm")
    def paradigm_fsm():
        path = os.path.join(P.PROJECT_DIRECTORY, "UnityRatVR", "builds", "paradigmFSMs")
        if not os.path.exists(os.path.join(path, "fsm_states.json")):
            msg = ("FSM structure has not been extracted from Unity Assets yet."
                   " Run extractParadigmFSM.py first.")
            raise HTTPException(status_code=400, detail=msg)
        
        if session_paramters.paradigm_name is None:
            raise HTTPException(status_code=400, detail="Paradigm has not been set yet")
        
        paradigm = session_paramters.paradigm_name
        paradigm_id = session_paramters.paradigm_id
        with open(os.path.join(path, "fsm_states.json")) as f:
            fsm_states = {key: val for key, val in json.load(f).items() 
                          if val["paradigm"] == paradigm_id}
        with open(os.path.join(path, "fsm_transitions.json")) as f:
            fsm_transitions = json.load(f)
        with open(os.path.join(path, "fsm_decisions.json")) as f:
            fsm_decisions = json.load(f)
        with open(os.path.join(path, "fsm_actions.json")) as f:
            fsm_actions = json.load(f)
        return {"states": fsm_states, "transitions": fsm_transitions, 
                "decisions": fsm_decisions, "actions": fsm_actions}

    @app.get("/paradigm_env")
    def paradigm_environment():
        if session_paramters.paradigm_name is None:
            raise HTTPException(status_code=400, detail="Paradigm has not been set yet")
        return session_paramters.excel_paradigm_definions
        
    @app.post("/session/animal/{msg}")
    def sessionanimal(msg: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_unitySessionRunning=False)
        session_paramters.animal = msg
    
    @app.post("/session/animalweight/{msg}")
    def sessionanimal(msg: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_unitySessionRunning=False)
        session_paramters.animal_weight = msg
    
    @app.post("/session/notes/{msg}")
    def sessionnotes(msg: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_unitySessionRunning=True)
        session_paramters.notes = msg
        print(msg)
    return app

def attach_UI_endpoint(app):
    P = Parameters()
    ui_dir = os.path.join(P.PROJECT_DIRECTORY, 'UIRatVR', 'dist')
    
    @app.get("/ui")
    async def root():
        if os.path.isfile(os.path.join(ui_dir, "index.html")):
            return FileResponse(os.path.join(ui_dir, "index.html"))
        else:
            raise HTTPException(status_code=404)

    # # Mount the 'dist' directory at the root of your app
    app.mount("/ui", StaticFiles(directory=ui_dir), name="dist")
    app.mount("/assets", StaticFiles(directory=os.path.join(ui_dir, "assets")), 
              name="assets")
