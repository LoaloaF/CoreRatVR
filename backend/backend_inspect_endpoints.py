import os

import pandas as pd
import json
from fastapi import  Request

from Parameters import Parameters
from SessionParamters import SessionParamters
from CustomLogger import CustomLogger as Logger

from backend_helpers import init_logger
from backend_helpers import validate_state

from session_loading import get_session_modality
from session_processing import patch_session_data

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
        L.logger.info(f"Initiating session inspection for {session_name}")
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
                                             "NAS_DATA_DIRECTORY"] if k in session_params]
            P.update_from_json(session_params)
            # except Exception as e:
            #     print("Error loading parameter defauls from session: ", e)
        
        else: #DB
            #TODO: implement
            pass
                
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
        
        nas_base_dir, paradigm_subdir = P.SESSION_DATA_DIRECTORY.split("RUN_")
        from_nas = (nas_base_dir, "RUN_"+paradigm_subdir, P.SESSION_NAME[:-5])
        trials = get_session_modality(from_nas=from_nas, modality="unity_trial",
                                      complement_data=True)
        return trials.to_json(orient="records")

    @app.get("/inspect/events")
    def inspect_events(request: Request):
        validate_state(request.app.state.state, valid_initiated_inspect=True)
        
        nas_base_dir, paradigm_subdir = P.SESSION_DATA_DIRECTORY.split("RUN_")
        from_nas = (nas_base_dir, "RUN_"+paradigm_subdir, P.SESSION_NAME[:-5])
        events = get_session_modality(from_nas=from_nas, modality="event",
                                      pct_as_index=True, rename2oldkeys=True,
                                      na2null=True)
        print(events)
        return events.to_json(orient="records")
    
    @app.get("/inspect/forwardvelocity")
    def inspect_forwardvelocity(request: Request):
        validate_state(request.app.state.state, valid_initiated_inspect=True)
        
        nas_base_dir, paradigm_subdir = P.SESSION_DATA_DIRECTORY.split("RUN_")
        from_nas = (nas_base_dir, "RUN_"+paradigm_subdir, P.SESSION_NAME[:-5])
        unityframes = get_session_modality(from_nas=from_nas, modality="unity_frame",
                                           na2null=True, complement_data=True)

        vel = unityframes["z_velocity"].rolling(window=20).mean()
        vel_dsampled = pd.concat([vel, unityframes.frame_pc_timestamp], axis=1).iloc[::10].dropna()
        return vel_dsampled.to_json(orient="records")
    
    @app.get("/inspect/unityframes")
    def inspect_forwardvelocity(request: Request):
        validate_state(request.app.state.state, valid_initiated_inspect=True)

        nas_base_dir, paradigm_subdir = P.SESSION_DATA_DIRECTORY.split("RUN_")
        from_nas = (nas_base_dir, "RUN_"+paradigm_subdir, P.SESSION_NAME[:-5])
        unityframes = get_session_modality(from_nas=from_nas, modality="unity_frame",
                                pct_as_index=True, rename2oldkeys=True, na2null=True)
        return unityframes.to_json(orient="records")