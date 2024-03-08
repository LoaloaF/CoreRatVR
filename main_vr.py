import os
import signal
import sys
import atexit
sys.path.insert(1, os.path.join(sys.path[0], 'SHM'))

from fastapi import FastAPI, HTTPException
import uvicorn
from typing import Any

from Parameters import Parameters
from CustomLogger import CustomLogger as Logger
import backend

import process_launcher as pl

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
        }
    
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
        if state["initiated"]:
            raise HTTPException(status_code=400, detail="Already initiated.")
        session_save_dir = backend.init_save_dir()
        logging_dir = backend.init_logger(session_save_dir)
        P.SESSION_DATA_DIRECTORY = session_save_dir
        P.LOGGING_DIRECTORY = logging_dir
        state["initiated"] = True
        
        L = Logger()
        L.spacer()
        L.logger.info("Session initiated.")
        L.logger.debug(L.fmtmsg(["Parameters", str(Parameters())]))
        L.spacer()
    
    @app.post("/shm/create_termflag_shm")
    def create_termflag_shm():
        if not state["initiated"]:
            raise HTTPException(status_code=400, detail="Not initiated yet")
        if state[P.SHM_NAME_TERM_FLAG]:
            raise HTTPException(status_code=400, detail="SHM already created")

        backend.handle_create_termflag_shm()
        state[P.SHM_NAME_TERM_FLAG] = True

    @app.post("/shm/create_ballvelocity_shm")
    def create_ballvelocity_shm():
        if not state["initiated"]:
            raise HTTPException(status_code=400, detail="Not initiated yet")
        if state[P.SHM_NAME_BALLVELOCITY]:
            raise HTTPException(status_code=400, detail="SHM already created")

        backend.handle_create_ballvelocity_shm()
        state[P.SHM_NAME_BALLVELOCITY] = True
    
    @app.post("/shm/create_portentaoutput_shm")
    def create_portentaoutput_shm():
        if not state["initiated"]:
            raise HTTPException(status_code=400, detail="Not initiated yet")
        if state[P.SHM_NAME_PORTENTA_OUTPUT]:
            raise HTTPException(status_code=400, detail="SHM already created")

        backend.handle_create_portentaoutput_shm()
        state[P.SHM_NAME_PORTENTA_OUTPUT] = True
        
    @app.post("/shm/create_portentainput_shm")
    def create_portentainput_shm():
        if not state["initiated"]:
            raise HTTPException(status_code=400, detail="Not initiated yet")
        if state[P.SHM_NAME_PORTENTA_INPUT]:
            raise HTTPException(status_code=400, detail="SHM already created")

        backend.handle_create_portentainput_shm()
        state[P.SHM_NAME_PORTENTA_INPUT] = True
    
    
    @app.post("/procs/open_por2shm2por_sim_proc")
    def open_por2shm2por_sim_proc():
        if not state[P.SHM_NAME_PORTENTA_OUTPUT]:
            raise HTTPException(status_code=400, 
                                detail="portentaoutput SHM not created")
        elif not state[P.SHM_NAME_PORTENTA_INPUT]:
            raise HTTPException(status_code=400, 
                                detail="portentainput SHM not created")

        backend.handle_open_por2shm2por_sim_proc()
        
    @app.post("/procs/open_por2shm2por_proc")
    def open_por2shm2por_sim_proc():
        if not state[P.SHM_NAME_PORTENTA_OUTPUT]:
            raise HTTPException(status_code=400, 
                                detail="portentaoutput SHM not created")
        elif not state[P.SHM_NAME_PORTENTA_INPUT]:
            raise HTTPException(status_code=400, 
                                detail="portentainput SHM not created")

        backend.handle_open_por2shm2por_proc()
        
    @app.post("/procs/open_log_portenta_proc")
    def open_log_portenta_proc():
        if not state[P.SHM_NAME_PORTENTA_OUTPUT]:
            raise HTTPException(status_code=400, 
                                detail="portentaoutput SHM not created")
        elif not state[P.SHM_NAME_BALLVELOCITY]:
            raise HTTPException(status_code=400, 
                                detail="ballvelocity SHM not created")
        backend.handle_open_log_portenta_proc()
    
    @app.post("/procs/open_stream_portenta_proc")
    def open_log_portenta_proc():
        if not state[P.SHM_NAME_PORTENTA_OUTPUT]:
            raise HTTPException(status_code=400, 
                                detail="portentaoutput SHM not created")
        elif not state[P.SHM_NAME_BALLVELOCITY]:
            raise HTTPException(status_code=400, 
                                detail="ballvelocity SHM not created")
        backend.handle_open_log_portenta_proc()
        proc = pl.open_stream_portenta_proc()
        return {"pid": proc.pid} 

    @app.post("/raise_term_flag")
    def raise_term_flag():
        # do checks
        open_shm_mem_names = []
        for key, value in state.items():
            if value and key in (P.SHM_NAME_TERM_FLAG, P.SHM_NAME_BALLVELOCITY,
                                 P.SHM_NAME_PORTENTA_OUTPUT, P.SHM_NAME_PORTENTA_INPUT,
                                 P.SHM_NAME_UNITY_OUTPUT, P.SHM_NAME_UNITY_INPUT):
                open_shm_mem_names.append(key)
        backend.POST_raise_term_flag(open_shm_mem_names)

        state["initiated"] = False
        for shm_name in open_shm_mem_names:
            state[shm_name] = False

    
    uvicorn.run(app, host=host, port=port)

def main():
    # atexit.register(backend.handle_exit)
    run_backend(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
    
    