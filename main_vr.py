import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], 'backend'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from Parameters import Parameters

from backend_proc_endpoints import attach_proc_endpoints
from backend_shm_endpoints import attach_shm_endpoints
from backend_general_endpoints import attach_general_endpoints
from backend_general_endpoints import attach_UI_endpoint
from backend_streamer_endpoints import attach_stream_endpoints

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
            "unity": 0,
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
        "unitySessionRunning": False,
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
    attach_general_endpoints(app)
    attach_proc_endpoints(app)
    attach_shm_endpoints(app)
    attach_stream_endpoints(app)
    attach_UI_endpoint(app)
    uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()