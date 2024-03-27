import os
import signal
import sys
sys.path.insert(1, os.path.join(sys.path[0], 'SHM'))

from fastapi import FastAPI, HTTPException
import uvicorn
from typing import Any

from Parameters import Parameters
from CustomLogger import CustomLogger as Logger
import backend

from process_launcher import shm_struct_fname

import process_launcher as pl
import SHM.shm_creation as sc
from SHM.CyclicPackagesSHMInterface import CyclicPackagesSHMInterface

def run_backend(host="0.0.0.0", port=8000):
    P = Parameters()
    app = FastAPI()
    state = {
        "initiated": False,
        P.SHM_NAME_TERM_FLAG: False,
        P.SHM_NAME_BALLVELOCITY: False,
        P.SHM_NAME_PORTENTA_OUTPUT: False,
        P.SHM_NAME_PORTENTA_INPUT: False,
        P.SHM_NAME_UNITY_OUTPUT: False,
        P.SHM_NAME_UNITY_INPUT: False,
        P.SHM_NAME_FACE_CAM: False,
        P.SHM_NAME_BODY_CAM: False,
        P.SHM_NAME_UNITY_CAM: False,
        }
    unityinput_shm = None
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        L = Logger()
        L.spacer()
        L.logger.error(exc)
        L.spacer()
        os.kill(os.getpid(), signal.SIGINT)  # Terminate the server
        raise HTTPException(status_code=500, 
                            detail=f"Server error:{exc} Terminating server.")
    
    @app.get("/parameters")
    def get_parameters():
        return backend.GET_get_parameters()

    @app.patch("/parameters/{key}")
    async def update_parameter(key: str, new_value: Any):
        return backend.PATCH_update_parameter(key, new_value, state["initiated"])

    @app.post("/initiate")
    def initiate():
        backend.validate_state(state, valid_initiated=False)
        session_save_dir = backend.init_save_dir()
        logging_dir = backend.init_logger(session_save_dir)
        P.SESSION_DATA_DIRECTORY = session_save_dir
        P.LOGGING_DIRECTORY = logging_dir
        P.save_to_json(P.SESSION_DATA_DIRECTORY)
        state["initiated"] = True

        L = Logger()
        L.spacer()
        L.logger.info("Session initiated.")
        L.logger.debug(L.fmtmsg(["Parameters", str(Parameters())]))
        L.spacer()
    
    @app.post("/raise_term_flag")
    def raise_term_flag():
        if not state['initiated']:
            # not handled by function below bc logger not initiated yet -> mess
            # backend.validate_state(state, valid_initiated=False)
            raise HTTPException(status_code=400, detail="Not initiated.")

        open_shm_mem_names = []
        for key, value in state.items():
            if value and key in (P.SHM_NAME_TERM_FLAG, P.SHM_NAME_BALLVELOCITY,
                                 P.SHM_NAME_PORTENTA_OUTPUT, P.SHM_NAME_PORTENTA_INPUT,
                                 P.SHM_NAME_UNITY_OUTPUT, P.SHM_NAME_UNITY_INPUT,
                                 P.SHM_NAME_FACE_CAM, P.SHM_NAME_BODY_CAM):
                open_shm_mem_names.append(key)
        backend.POST_raise_term_flag(open_shm_mem_names)

        state["initiated"] = False
        for shm_name in open_shm_mem_names:
            state[shm_name] = False




    ############################################################################
    ############################## create SHM ##################################
    ############################################################################

    @app.post("/shm/create_termflag_shm")
    def create_termflag_shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: False})
        sc.create_singlebyte_shm(shm_name=P.SHM_NAME_TERM_FLAG)
        state[P.SHM_NAME_TERM_FLAG] = True

    @app.post("/shm/create_ballvelocity_shm")
    def create_ballvelocity_shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_BALLVELOCITY: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_BALLVELOCITY, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_BALLVELOCITY, 
                                      npackages=P.SHM_NPACKAGES_BALLVELOCITY)
        state[P.SHM_NAME_BALLVELOCITY] = True
    
    @app.post("/shm/create_portentaoutput_shm")
    def create_portentaoutput_shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_PORTENTA_OUTPUT: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_PORTENTA_OUTPUT, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_PORTENTA_OUTPUT, 
                                      npackages=P.SHM_NPACKAGES_PORTENTA_OUTPUT)
        state[P.SHM_NAME_PORTENTA_OUTPUT] = True
        
    @app.post("/shm/create_portentainput_shm")
    def create_portentainput_shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_PORTENTA_INPUT: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_PORTENTA_INPUT, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_PORTENTA_INPUT, 
                                      npackages=P.SHM_NPACKAGES_PORTENTA_INPUT)
        state[P.SHM_NAME_PORTENTA_INPUT] = True
    
    @app.post("/shm/create_unityinput_shm")
    def create_unityinput_shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_UNITY_INPUT: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_UNITY_INPUT, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_UNITY_INPUT,
                                      npackages=P.SHM_NPACKAGES_UNITY_INPUT)
        state[P.SHM_NAME_UNITY_INPUT] = True
    
    @app.post("/shm/create_unityoutput_shm")
    def create_unityoutput_shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_UNITY_OUTPUT: False})
        sc.create_cyclic_packages_shm(shm_name=P.SHM_NAME_UNITY_OUTPUT, 
                                      package_nbytes=P.SHM_PACKAGE_NBYTES_UNITY_OUTPUT,
                                      npackages=P.SHM_NPACKAGES_UNITY_OUTPUT)
        state[P.SHM_NAME_UNITY_OUTPUT] = True


    @app.post("/shm/create_facecam_shm")
    def create_facecam_shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_FACE_CAM: False})
        sc.create_video_frame_shm(shm_name=P.SHM_NAME_FACE_CAM, 
                                  x_resolution=P.FACE_CAM_X_RES,
                                  y_resolution=P.FACE_CAM_Y_RES,
                                  nchannels=P.FACE_CAM_NCHANNELS)
        state[P.SHM_NAME_FACE_CAM] = True

    @app.post("/shm/create_bodycam_shm")
    def create_bodycam_shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_BODY_CAM: False})
        sc.create_video_frame_shm(shm_name=P.SHM_NAME_BODY_CAM, 
                                  x_resolution=P.BODY_CAM_X_RES,
                                  y_resolution=P.BODY_CAM_Y_RES,
                                  nchannels=P.BODY_CAM_NCHANNELS)
        state[P.SHM_NAME_BODY_CAM] = True
    
    @app.post("/shm/create_unitycam_shm")
    def create_unitycam_shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_UNITY_CAM: False})
        sc.create_video_frame_shm(shm_name=P.SHM_NAME_UNITY_CAM, 
                                  x_resolution=P.UNITY_CAM_X_RES,
                                  y_resolution=P.UNITY_CAM_Y_RES,
                                  nchannels=P.UNITY_CAM_NCHANNELS)
        state[P.SHM_NAME_UNITY_CAM] = True




    ############################################################################
    ############################## create procs ################################
    ############################################################################
        
    @app.post("/procs/launch_por2shm2por_sim")
    def launch_por2shm2por_sim():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_PORTENTA_OUTPUT: True,
                                                  P.SHM_NAME_BALLVELOCITY: True,
                                                  })
        proc = pl.open_por2shm2por_sim_proc()
        return {"pid": proc.pid} 

    @app.post("/procs/launch_por2shm2por")
    def launch_por2shm2por():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_PORTENTA_OUTPUT: True,
                                                  P.SHM_NAME_BALLVELOCITY: True,
                                                  P.SHM_NAME_PORTENTA_INPUT: True,
                                                  })
        proc = pl.open_por2shm2por_proc()
        return {"pid": proc.pid} 
        
    @app.post("/procs/launch_log_portenta")
    def launch_log_portenta():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_PORTENTA_OUTPUT: True,
                                                  P.SHM_NAME_BALLVELOCITY: True,
                                                  })
        proc = pl.open_log_portenta_proc()
        return {"pid": proc.pid} 

    @app.post("/procs/launch_stream_portenta")
    def launch_stream_portenta():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_PORTENTA_OUTPUT: True,
                                                  P.SHM_NAME_BALLVELOCITY: True,
                                                  })
        proc = pl.open_stream_portenta_proc()
        return {"pid": proc.pid} 
    
    @app.post("/procs/launch_facecam2shm")
    def launch_facecam2shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_FACE_CAM: True,
                                                  })
        proc = pl.open_camera2shm_proc(P.SHM_NAME_FACE_CAM)
        return {"pid": proc.pid} 
    
    @app.post("/procs/launch_bodycam2shm")
    def launch_bodycam2shm():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_BODY_CAM: True,
                                                  })
        proc = pl.open_camera2shm_proc(P.SHM_NAME_BODY_CAM)
        return {"pid": proc.pid}
    
    @app.post("/procs/launch_stream_facecam")
    def launch_stream_facecam():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_FACE_CAM: True,
                                                  })
        proc = pl.open_shm2cam_stream_proc(P.SHM_NAME_FACE_CAM)
        return {"pid": proc.pid}

    @app.post("/procs/launch_log_facecam")
    def launch_log_facecam():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_FACE_CAM: True,
                                                  })
        proc = pl.open_log_camera_proc(P.SHM_NAME_FACE_CAM)
        return {"pid": proc.pid}
    
    @app.post("/procs/launch_stream_bodycam")
    def launch_stream_bodycam():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_BODY_CAM: True,
                                                  })
        proc = pl.open_shm2cam_stream_proc(P.SHM_NAME_BODY_CAM)
        return {"pid": proc.pid}
    
    @app.post("/procs/launch_log_unity")
    def launch_log_unity():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_UNITY_OUTPUT: True,
                                                  })
        proc = pl.open_log_unity_proc()
        return {"pid": proc.pid}

    @app.post("/procs/launch_log_unitycam")
    def launch_log_unitycam():
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_UNITY_CAM: True,
                                                  })
        proc = pl.open_log_camera_proc(P.SHM_NAME_UNITY_CAM)
        return {"pid": proc.pid}

    @app.post("/unityinput/{msg}")
    def unityinput(msg: str):
        backend.validate_state(state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: True,
                                                  P.SHM_NAME_UNITY_INPUT: True,
                                                  })
        struct_fname = shm_struct_fname(P.SHM_NAME_UNITY_INPUT)
        unityinput_shm = CyclicPackagesSHMInterface(struct_fname)
        unityinput_shm.push(msg.encode())
        unityinput_shm.close_shm()
        
    uvicorn.run(app, host=host, port=port)
def main():
    # atexit.register(backend.handle_exit)
    run_backend(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
    
    