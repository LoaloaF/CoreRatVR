import os

import pandas as pd
import json
from fastapi import  Request
from fastapi import HTTPException

from Parameters import Parameters
from SessionParamters import SessionParamters
from CustomLogger import CustomLogger as Logger

from backend_helpers import init_logger
from backend_helpers import validate_state

from analytics_processing.modality_loading import session_modality_from_nas
from analytics_processing.modality_transformations import data_modality_na2null
from analytics_processing.modality_transformations import data_modality_rename2oldkeys
from analytics_processing.modality_transformations import data_modality_pct_as_index

def attach_inspect_endpoints(app):
    # singlton class - reference to instance created in lifespan
    P = Parameters()
    session_paramters = SessionParamters()
    
    
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
        i = 0
        for an_dir in sorted(animal_dirs):
            animal_dir = os.path.join(P.NAS_DATA_DIRECTORY, an_dir)
            
            paradigm_dirs = [f for f in os.listdir(animal_dir) 
                             if os.path.isdir(os.path.join(animal_dir, f))]
            for par_dir in sorted(paradigm_dirs):
                paradigm_dir = os.path.join(P.NAS_DATA_DIRECTORY, animal_dir, par_dir)

                session_dirs = [f for f in os.listdir(paradigm_dir) if f.endswith("min")]
                for ses_dir in sorted(session_dirs):
                    session_dir = os.path.join(P.NAS_DATA_DIRECTORY, animal_dir, par_dir, ses_dir)
                    fnames = [f for f in os.listdir(session_dir) 
                             if f.endswith("min.hdf5")]
                    if len(fnames):
                        for fname in fnames:
                            sessions.append({"animal": an_dir, "paradigm": par_dir[-5:], 
                                            "session": fnames[0]})
                        
                            # print("=============================================")
                            # print(i)
                            # session_fullfname = os.path.join(session_dir, fname)
                            # patch_session_data.convert_hdf5_fixed_to_table(session_fullfname, dummyrun=True)
                            # i += 1
                            # print("=============================================")
                    # else:
                    #     print(session_dir)
        
        return sessions
    
    @app.post("/inspect/initiate_session_selection/{session_name}")
    def session_selection(session_name: str, request: Request):
        validate_state(request.app.state.state, valid_initiated=False, 
                       valid_initiated_inspect=False)
        L = Logger()
        # close any loggers that might be open from `Acquire` usage
        if L.logger.handlers:
            L.reset_logger()
        init_logger(session_save_dir=None)  # log to log dir
        
        L.logger.info(f"Initiating session inspection for {session_name}")
        P = Parameters()

        animal, paradigm = session_name.split("_")[-4:-2]
        base_dir = os.path.join(P.NAS_DATA_DIRECTORY, f"RUN_{animal}", f"{animal}_{paradigm}")
        
        session_dir = os.path.join(base_dir, session_name.replace("behavior_", "")[:-5])
        logging_dir = P.LOGGING_DIRECTORY # the default logging dir on this machine
        
        nas_base_dir, paradigm_subdir = session_dir.split("RUN_")
        session_fullfname = os.path.join(nas_base_dir, "RUN_"+paradigm_subdir, session_name)
        metadata = session_modality_from_nas(session_fullfname, 'metadata')
        # set the parameters and session_parameters from the inspected session
        session_paramters.load_session_parameters(metadata)
        P.update_from_json(metadata["configuration"])
                
        P.SESSION_DATA_DIRECTORY = session_dir
        P.SESSION_NAME = session_name
        P.LOGGING_DIRECTORY = logging_dir
        P.LOG_TO_DATA_DIR = False
        
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
        
        nas_base_dir, paradigm_subdir = P.SESSION_DATA_DIRECTORY.split("RUN_")
        session_fullfname = os.path.join(nas_base_dir, "RUN_"+paradigm_subdir, P.SESSION_NAME)

        trialdata = session_modality_from_nas(session_fullfname, "unity_trial")
        trialdata = data_modality_rename2oldkeys(trialdata, 'unity_trial')
        trialvariable = session_modality_from_nas(session_fullfname, "paradigm_variable")
        trialvariable = data_modality_rename2oldkeys(trialvariable, 'paradigm_variable')
        trialdata = data_modality_na2null(pd.merge(trialdata, trialvariable, on="ID"))
        print(trialdata)
        
        if trialdata is None:
            raise HTTPException(status_code=404, detail="Could not load unity trials")
        return trialdata.to_json(orient="records")

    @app.get("/inspect/events")
    def inspect_events(request: Request):
        validate_state(request.app.state.state, valid_initiated_inspect=True)
        
        nas_base_dir, paradigm_subdir = P.SESSION_DATA_DIRECTORY.split("RUN_")
        session_fullfname = os.path.join(nas_base_dir, "RUN_"+paradigm_subdir, P.SESSION_NAME)
        events = session_modality_from_nas(session_fullfname, "event")
        events = data_modality_pct_as_index(events)
        events = data_modality_rename2oldkeys(events, 'event')
        events = data_modality_na2null(events)
        # print(events)
        
        if events is None:
            raise HTTPException(status_code=404, detail="Could not load events")
        return events.to_json(orient="records")
    
    @app.get("/inspect/forwardvelocity")
    def inspect_forwardvelocity(request: Request):
        validate_state(request.app.state.state, valid_initiated_inspect=True)
        
        # nas_base_dir, paradigm_subdir = P.SESSION_DATA_DIRECTORY.split("RUN_")
        # session_fullfname = os.path.join(nas_base_dir, "RUN_"+paradigm_subdir, P.SESSION_NAME)
        
        # unityframes = session_modality_from_nas(session_fullfname, "unity_frame")
        # unityframes = data_modality_rename2oldkeys(unityframes, 'unity_frame')
        # unityframes = data_modality_na2null(unityframes)
        # print(unityframes)
        
        # nas_base_dir, paradigm_subdir = P.SESSION_DATA_DIRECTORY.split("RUN_")
        # session_dir_tuple = (nas_base_dir, "RUN_"+paradigm_subdir, P.SESSION_NAME[:-5])
        
        # complement_data = False
        # if session_paramters.paradigm_id == 800:
        #     complement_data = True
        # # unityframes = get_session_modality("unity_frame", session_dir_tuple,
        # #                                    na2null=True, complement_data=complement_data)
        # if unityframes is None:
        #     raise HTTPException(status_code=404, detail="Could not load unity frames")
        
        # vel = unityframes["z_velocity"].rolling(window=20).mean()
        # vel_dsampled = pd.concat([vel, unityframes.frame_pc_timestamp], axis=1).iloc[::20].dropna()
        return ""
    
    @app.get("/inspect/unityframes")
    def inspect_forwardvelocity(request: Request):
        validate_state(request.app.state.state, valid_initiated_inspect=True)
        
        nas_base_dir, paradigm_subdir = P.SESSION_DATA_DIRECTORY.split("RUN_")
        session_fullfname = os.path.join(nas_base_dir, "RUN_"+paradigm_subdir, P.SESSION_NAME)
        
        unityframes = session_modality_from_nas(session_fullfname, "unity_frame")
        unityframes = data_modality_rename2oldkeys(unityframes, 'unity_frame')
        unityframes = data_modality_na2null(unityframes)
        print(unityframes)

        if unityframes is None:
            raise HTTPException(status_code=404, detail="Could not load unity frames")
        return unityframes.to_json(orient="records")