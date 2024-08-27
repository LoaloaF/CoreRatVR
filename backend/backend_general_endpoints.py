import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], 'SHM'))
sys.path.insert(1, os.path.join(sys.path[0], 'backend'))

import pandas as pd
import asyncio
import shutil
from send2trash import send2trash
from time import sleep
import json
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from typing import Any, Dict
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
from backend_helpers import access_session_data

from SHM.shm_creation import delete_shm

import process_launcher


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
        validate_state(app.state.state, valid_initiated=False, 
                       valid_initiated_inspect=False)
        session_save_dir = check_base_dirs()
        session_save_dir = init_save_dir()
        logging_dir = init_logger(session_save_dir)
        P.SESSION_DATA_DIRECTORY = session_save_dir
        P.SESSION_NAME = os.path.basename(session_save_dir)
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
    
    @app.post("/start_paradigm")
    def start_paradigm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True,
                       valid_paradigmRunning=False,
                       valid_shm_created={P.SHM_NAME_PARADIGM_RUNNING_FLAG: True}
                       )
        # prv requests set animal, paradigm, optinoally animal weight
        session_paramters.handle_start_session()
        paradigm_running_shm_interface = request.app.state.state["paradigm_running_shm_interface"]
        # exclusive raise flag here
        paradigm_running_shm_interface.set()
        request.app.state.state["paradigmRunning"] = True
        
    @app.post("/stop_paradigm")
    def stop_paradigm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True,
                       valid_paradigmRunning=True,
                       valid_shm_created={P.SHM_NAME_PARADIGM_RUNNING_FLAG: True}
                       )
        session_paramters.handle_stop_session()
        paradigm_running_shm_interface = request.app.state.state["paradigm_running_shm_interface"]
        # exclusive lower flag here
        paradigm_running_shm_interface.reset()
        request.app.state.state["paradigmRunning"] = False

    @app.post("/unityinput/{msg}")
    def unityinput(msg: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_UNITY_INPUT: True})
        # send message to unity through shared memory
        request.app.state.state["unityinput_shm_interface"].push(msg.encode())
    
    @app.post("/raise_term_flag")
    def raise_term_flag(body: Dict[str, Any], request: Request):
        L = Logger()
        L.logger.info(L.fmtmsg([f"Handling raised term flag with processing parameters: ", body]))

        validate_state(request.app.state.state, valid_initiated=True, 
                valid_shm_created={P.SHM_NAME_TERM_FLAG: True})
        shm_state = request.app.state.state['shm']
        procs_state = request.app.state.state['procs']
        termflag_shm_interface = request.app.state.state["termflag_shm_interface"]
        unityinput_shm_interface = request.app.state.state["unityinput_shm_interface"]
        paradigm_running_shm_interface = request.app.state.state["paradigm_running_shm_interface"]
        
        # send termination flag to all processes
        termflag_shm_interface.set()
        # reset the termination flag interface
        termflag_shm_interface.close_shm()
        request.app.state.state["termflag_shm_interface"] = None
        
        request.app.state.state['procs'].update({proc_name: 0 for proc_name in procs_state.keys()})

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
                if shm_name == "paradigm_running_shm_interface":
                    paradigm_running_shm_interface.close_shm()
                    request.app.state.state["paradigm_running_shm_interface"] = None
        
        if body.get("deleteVal"):
            session_dir = body.get("sessionDir")
            send2trash(session_dir)
            if os.path.exists(session_dir): # sometimes empty dir left
                os.rmdir(session_dir)

        else:
            session_dir = body.get("sessionDir")
            L.logger.info(f"Processing session {session_dir}")
            
            args = (session_dir, body["rnderCamVal"], body["integrEphysVal"], 
                    body["copy2NASVal"], body["write2DBVal"], body["interactiveVal"])
            proc = process_launcher.open_process_session_proc(*args)
            request.app.state.state["procs"]["process_session"] = proc.pid

        P.initialize_defaults()
        session_paramters.clear()
        sleep(1)
        request.app.state.state["initiated"] = False

    @app.post("/session/paradigm/{msg}")
    def sessionparadigm(msg: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_paradigmRunning=False)
        session_paramters.paradigm_name = msg
    
    @app.post("/session/animal/{msg}")
    def sessionanimal(msg: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_paradigmRunning=False)
        session_paramters.animal = msg
    
    @app.post("/session/animalweight/{msg}")
    def sessionanimal(msg: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_paradigmRunning=False)
        if msg.isnumeric() and int(msg) not in (0, -1):
            session_paramters.animal_weight = msg
    
    @app.post("/session/notes/{msg}")
    def sessionnotes(msg: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_paradigmRunning=True)
        session_paramters.notes = msg
    
    @app.get("/paradigms")
    def paradigms():
        dirname = os.path.join(P.PROJECT_DIRECTORY, "UnityRatVR", "Paradigms")
        paradigms = [f for f in os.listdir(dirname) if f.endswith(".xlsx")]
        return paradigms

    @app.get("/animals")
    def animals():
        static_animals = ["rYL_001","rYL_002","rYL_003","rYL_004","rYL_006","rYL_008","AI_001","dummyAnimal"]
        return static_animals

    @app.get("/trial_variable_names")
    def trial_variable_names():
        if "trialPackageVariables" not in session_paramters.session_parameters_dict:
            raise HTTPException(status_code=400, detail="Trial variables not in Excel sheet")
        
        var_names = session_paramters.session_parameters_dict["trialPackageVariables"]
        if var_names == "none":
            return {}
        full_var_names = session_paramters.session_parameters_dict["trialPackageVariablesFullNames"]
        if full_var_names == "none":
            full_var_names = var_names
        return dict(zip(var_names, full_var_names))

    @app.get("/trial_variable_default_values")
    def trial_variable_default_values():
        if "trialPackageVariablesDefault" not in session_paramters.session_parameters_dict:
            raise HTTPException(status_code=400, detail="Trial variables default values not in Excel sheet")
        
        val = session_paramters.session_parameters_dict["trialPackageVariablesDefault"]
        if val == "none":
            return {}
        return val

    @app.get("/session_start_time")
    def session_start_time(request: Request):
        validate_state(request.app.state.state, valid_paradigmRunning=True)
        return session_paramters.start_time
        
    @app.get("/paradigm_env")
    def paradigm_environment():
        if session_paramters.paradigm_name is None:
            raise HTTPException(status_code=400, detail="Paradigm has not been set yet")
        return session_paramters.environment_parameters_dict
        
    @app.get("/paradigm_fsm")
    def paradigm_fsm():
        path = os.path.join(P.PROJECT_DIRECTORY, "UnityRatVR", "paradigmFSMs")
        if not os.path.exists(os.path.join(path, "fsm_states.json")):
            msg = ("FSM structure has not been extracted from Unity Assets yet."
                   " Run extractParadigmFSM.py first.")
            raise HTTPException(status_code=400, detail=msg)
        
        if session_paramters.paradigm_name is None:
            raise HTTPException(status_code=400, detail="Paradigm has not been set yet")
        
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

    @app.get("/inspect/sessions")
    def sessions(request: Request):
        # get all sessions from NAS
        validate_state(request.app.state.state)
        sessions = []
        
        if not os.path.exists(P.NAS_DATA_DIRECTORY):
            return []
            # raise HTTPException(status_code=400, detail="NAS directory not found")
        
        animal_dirs = [f for f in os.listdir(P.NAS_DATA_DIRECTORY) 
                       if f[:7] in ("RUN_rYL", "RUN_rSS")]
        for an_dir in animal_dirs:
            animal_dir = os.path.join(P.NAS_DATA_DIRECTORY, an_dir)
            
            paradigm_dirs = [f for f in os.listdir(animal_dir) 
                             if os.path.isdir(os.path.join(animal_dir, f))]
            for par_dir in paradigm_dirs:
                paradigm_dir = os.path.join(P.NAS_DATA_DIRECTORY, animal_dir, par_dir)

                session_dirs = [f for f in os.listdir(paradigm_dir) if f.endswith("min")]
                for ses_dir in session_dirs:
                    session_dir = os.path.join(P.NAS_DATA_DIRECTORY, animal_dir, par_dir, ses_dir)
                    fname = [f for f in os.listdir(session_dir) 
                             if f.endswith("min.hdf5")][0]
                    if fname:
                        sessions.append({"animal": an_dir, "paradigm": par_dir[-5:], 
                                         "session": fname})
        return sessions
    
    @app.post("/inspect/initiate_session_selection/{session_name}")
    def session_selection(session_name: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=False, 
                       valid_initiated_inspect=False)
        P = Parameters()
        source, session_name = session_name.split(";", 1)
        if source == "NAS":
            animal, paradigm = session_name.split("_")[-4:-2]
            base_dir = os.path.join(P.NAS_DATA_DIRECTORY, f"RUN_{animal}", f"{animal}_{paradigm}")
            # base_dir = os.path.expanduser("~/local_data") # local hack, cut later
            
            session_dir = os.path.join(base_dir, session_name.replace("behavior_", "")[:-5])
            logging_dir = P.LOGGING_DIRECTORY # the default logging dir on this machine
            
            # attempt to load parameter defaults from session, old sessions might not have this
            # try:
            metadata = pd.read_hdf(os.path.join(session_dir, session_name),
                                    key="metadata")
            session_paramters.load_session_parameters(metadata)
            session_params = json.loads(metadata.loc[:,"configuration"].iloc[0])
            # keep the defalts for thoese params
            [session_params.pop(k) for k in ["LOGGING_LEVEL", "PROJECT_DIRECTORY", 
                                             "NAS_DATA_DIRECTORY"]]
            P.update_from_json(session_params)
            # except Exception as e:
            #     print("Error loading parameter defauls from session: ", e)
        
        else: #DB
            #TODO: implement
            pass
                
        # for inspect some parameters need to changed eg paths
        # P.PROJECT_DIRECTORY = P.get_default_project_directory()
        # P.NAS_DATA_DIRECTORY = P.get_default_nas_directory()
        P.SESSION_DATA_DIRECTORY = session_dir
        P.SESSION_NAME = session_name
        P.LOGGING_DIRECTORY = logging_dir
        P.INSPECT_FROM_DB = source == "db"
        P.LOG_TO_DATA_DIR = False
        
        init_logger(session_save_dir=None)  # log to log dir
        request.app.state.state["initiatedInspect"] = True

        L = Logger()
        L.spacer()
        L.logger.info(f"Session inspection initiated for {session_name}")
        return True
    
    @app.get("/inspect/selected_session")
    def selected_session(request: Request):
        validate_state(request.app.state.state, valid_initiated_inspect=True)
        session_name = [f for f in os.listdir(P.SESSION_DATA_DIRECTORY) if f.endswith("min.hdf5")][0][:-5]
        return session_name
    
    @app.post("/inspect/terminate_inspection")
    def terminate_inspection(request: Request):
        validate_state(request.app.state.state, valid_initiated_inspect=True)
        request.app.state.state["initiatedInspect"] = False
        
        P.initialize_defaults()
        session_paramters.clear()
        return True
    
    @app.get("/inspect/trials")
    def inspect_trials(request: Request):
        validate_state(request.app.state.state, valid_initiated_inspect=True)
        trials = access_session_data("unity_trial").to_json(orient="records")
        return trials
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
