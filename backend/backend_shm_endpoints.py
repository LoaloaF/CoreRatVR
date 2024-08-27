from fastapi import Request
from backend_helpers import validate_state
from backend.backend_helpers import shm_struct_fname

from Parameters import Parameters
import SHM.shm_creation as sc

from SHM.FlagSHMInterface import FlagSHMInterface
from SHM.CyclicPackagesSHMInterface import CyclicPackagesSHMInterface

def attach_shm_endpoints(app):
    P = Parameters()
    
    @app.post("/shm/create_termflag_shm")
    def create_termflag_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                               valid_shm_created={P.SHM_NAME_TERM_FLAG: False})
        sc.create_singlebyte_shm(shm_name=P.SHM_NAME_TERM_FLAG)
        request.app.state.state["shm"][P.SHM_NAME_TERM_FLAG] = True

        # create an interface for closing procesces
        shm_interface = FlagSHMInterface(shm_struct_fname(P.SHM_NAME_TERM_FLAG))
        request.app.state.state["termflag_shm_interface"] = shm_interface

    @app.post("/shm/create_paradigm_running_shm")
    def create_termflag_shm(request: Request):
        validate_state(request.app.state.state, valid_initiated=True, 
                       valid_shm_created={P.SHM_NAME_PARADIGM_RUNNING_FLAG: False})
        sc.create_singlebyte_shm(shm_name=P.SHM_NAME_PARADIGM_RUNNING_FLAG)
        request.app.state.state["shm"][P.SHM_NAME_PARADIGM_RUNNING_FLAG] = True

        # create an interface for closing procesces
        shm_interface = FlagSHMInterface(shm_struct_fname(P.SHM_NAME_PARADIGM_RUNNING_FLAG))
        request.app.state.state["paradigm_running_shm_interface"] = shm_interface

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
    return app