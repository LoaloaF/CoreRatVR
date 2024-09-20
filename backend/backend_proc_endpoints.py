import os
import sys

from fastapi import HTTPException, Request

from Parameters import Parameters
from backend_helpers import validate_state

import process_launcher as pl


def attach_proc_endpoints(app):
    # singlton class - reference to instance created in lifespan
    P = Parameters()

    @app.post("/procs/launch_por2shm2por_sim")
    def launch_por2shm2por_sim(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          P.SHM_NAME_BALLVELOCITY: True,
                                          },
                       valid_proc_running={"por2shm2por_sim": False})
        proc = pl.open_por2shm2por_sim_proc()
        request.app.state.state["procs"]["por2shm2por_sim"] = proc.pid

    @app.post("/procs/launch_por2shm2por")
    def launch_por2shm2por(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          P.SHM_NAME_BALLVELOCITY: True,
                                          P.SHM_NAME_PORTENTA_INPUT: True,
                                          },
                       valid_proc_running={"por2shm2por": False})
        proc = pl.open_por2shm2por_proc()
        request.app.state.state["procs"]["por2shm2por"] = proc.pid
        
    @app.post("/procs/launch_log_portenta")
    def launch_log_portenta(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          P.SHM_NAME_BALLVELOCITY: True,
                                          },
                       valid_proc_running={"log_portenta": False})
        proc = pl.open_log_portenta_proc()
        request.app.state.state["procs"]["log_portenta"] = proc.pid
    
    @app.post("/procs/launch_log_ephys")
    def launch_log_ephys(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_PARADIGM_RUNNING_FLAG: True,
                                          },
                       valid_proc_running={"log_ephys": False})
        proc = pl.open_log_ephys_proc()
        request.app.state.state["procs"]["log_ephys"] = proc.pid

    @app.post("/procs/launch_stream_portenta")
    def launch_stream_portenta(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          P.SHM_NAME_BALLVELOCITY: True,
                                          },
                       valid_proc_running={"stream_portenta": False})
        proc = pl.open_stream_portenta_proc()
        request.app.state.state["procs"]["stream_portenta"] = proc.pid
    
    @app.post("/procs/launch_facecam2shm")
    def launch_facecam2shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_FACE_CAM: True,
                                          },
                       valid_proc_running={"facecam2shm": False})
        proc = pl.open_vimbacam2shm_proc(P.SHM_NAME_FACE_CAM)
        request.app.state.state["procs"]["facecam2shm"] = proc.pid
    
    @app.post("/procs/launch_bodycam2shm")
    def launch_bodycam2shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_BODY_CAM: True,
                                          },
                       valid_proc_running={"bodycam2shm": False})
        proc = pl.open_camera2shm_proc(P.SHM_NAME_BODY_CAM)
        request.app.state.state["procs"]["bodycam2shm"] = proc.pid
    
    @app.post("/procs/launch_stream_facecam")
    def launch_stream_facecam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_FACE_CAM: True,
                                          },
                       valid_proc_running={"stream_facecam": False})
        proc = pl.open_shm2cam_stream_proc(P.SHM_NAME_FACE_CAM)
        request.app.state.state["procs"]["stream_facecam"] = proc.pid

    @app.post("/procs/launch_log_facecam")
    def launch_log_facecam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_FACE_CAM: True,
                                          },
                       valid_proc_running={"log_facecam": False})
        proc = pl.open_log_camera_proc(P.SHM_NAME_FACE_CAM)
        request.app.state.state["procs"]["log_facecam"] = proc.pid
    
    @app.post("/procs/launch_log_bodycam")
    def launch_log_bodycam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_BODY_CAM: True,
                                          },
                       valid_proc_running={"log_bodycam": False})
        proc = pl.open_log_camera_proc(P.SHM_NAME_BODY_CAM)
        request.app.state.state["procs"]["log_bodycam"] = proc.pid
    
    @app.post("/procs/launch_stream_bodycam")
    def launch_stream_bodycam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_BODY_CAM: True,
                                          },
                       valid_proc_running={"stream_bodycam": False})
        proc = pl.open_shm2cam_stream_proc(P.SHM_NAME_BODY_CAM)
        request.app.state.state["procs"]["stream_bodycam"] = proc.pid
    
    @app.post("/procs/launch_log_unity")
    def launch_log_unity(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_UNITY_OUTPUT: True,
                                          },
                       valid_proc_running={"log_unity": False})
        proc = pl.open_log_unity_proc()
        request.app.state.state["procs"]["log_unity"] = proc.pid

    @app.post("/procs/launch_log_unitycam")
    def launch_log_unitycam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_UNITY_CAM: True,
                                          },
                       valid_proc_running={"log_unitycam": False})
        proc = pl.open_log_camera_proc(P.SHM_NAME_UNITY_CAM)
        request.app.state.state["procs"]["log_unitycam"] = proc.pid
    
    @app.post("/procs/launch_process_session")
    def launch_log_unitycam(request: Request):
        validate_state(request.app.state.state, valid_initiated=True)
        proc = pl.open_process_session_proc()
        # TODO add process session to state
        # request.app.state.state["procs"]["log_unitycam"] = proc.pid

    @app.post("/procs/launch_unity")
    def launch_unity(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                          P.SHM_NAME_BALLVELOCITY: True,
                                          P.SHM_NAME_PORTENTA_OUTPUT: True,
                                          P.SHM_NAME_PORTENTA_INPUT: True,
                                          P.SHM_NAME_UNITY_OUTPUT: True,
                                          P.SHM_NAME_UNITY_INPUT: True,
                                          P.SHM_NAME_UNITY_CAM: True,
                                          },
                       valid_proc_running={"unity": False})
        proc = pl.open_unity_proc()
        if proc == -1:
            msg = f"Unity binary `{P.UNITY_BUILD_NAME}` not found."
            raise HTTPException(status_code=400, detail=msg)
        else:
            request.app.state.state["procs"]["unity"] = proc.pid
            
            
    return app