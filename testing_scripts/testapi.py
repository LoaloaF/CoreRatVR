import requests
from time import sleep
import time

def test_endpoints():
    base_url = "http://localhost:8001"

    def createshm():
        # POST /initiate
        response = requests.post(f"{base_url}/initiate")
        print("POST /initiate:", response.json())

        # POST /shm/create_termflag_shm
        response = requests.post(f"{base_url}/shm/create_termflag_shm")
        print("POST /shm/create_termflag_shm:", response.json())

        # POST /shm/create_ballvelocity_shm
        response = requests.post(f"{base_url}/shm/create_ballvelocity_shm")
        print("POST /shm/create_ballvelocity_shm:", response.json())

        # POST /shm/create_portentaoutput_shm
        response = requests.post(f"{base_url}/shm/create_portentaoutput_shm")
        print("POST /shm/create_portentaoutput_shm:", response.json())
        
        # POST /shm/create_portentainput_shm
        response = requests.post(f"{base_url}/shm/create_portentainput_shm")
        print("POST /shm/create_portentainput_shm:", response.json())

        # POST /shm/create_unityoutput_shm
        response = requests.post(f"{base_url}/shm/create_unityoutput_shm")
        print("POST /shm/create_unityoutput_shm:", response.json())
        
        # POST /shm/create_unityinput_shm
        response = requests.post(f"{base_url}/shm/create_unityinput_shm")
        print("POST /shm/create_unityinput_shm:", response.json())
        
        # POST /shm/create_unityinput_shm
        response = requests.post(f"{base_url}/shm/create_unitycam_shm")
        print("POST /shm/create_unitycam_shm:", response.json())

    def run():
        
        # # POST /procs/open_por2shm2por_sim_proc
        # response = requests.post(f"{base_url}/procs/launch_por2shm2por_sim")
        # print("POST /procs/open_por2shm2por_sim_proc:", response.json())
        
        # POST /procs/open_por2shm2por_proc
        response = requests.post(f"{base_url}/procs/launch_por2shm2por")
        print("POST /procs/open_por2shm2por_proc:", response.json())
        
        # POST /procs/open_log_portenta_proc
        response = requests.post(f"{base_url}/procs/launch_log_portenta")
        print("POST /procs/open_log_portenta_proc:", response.json())
        
        # POST /procs/open_stream_portenta_proc
        response = requests.post(f"{base_url}/procs/launch_stream_portenta")
        print("POST /procs/open_stream_portenta_proc:", response.json())
        
        # POST /procs/launch_log_unity
        response = requests.post(f"{base_url}/procs/launch_log_unity")
        print("POST /procs/launch_log_unity:", response.json())
        
        # POST /procs/launch_log_unity
        response = requests.post(f"{base_url}/procs/launch_log_unitycam")
        print("POST /procs/launch_log_unity:", response.json())


    def run_cam():
        # POST /initiate
        response = requests.post(f"{base_url}/initiate")
        print("POST /initiate:", response.json())
        time.sleep(1)

        # POST /shm/create_termflag_shm
        response = requests.post(f"{base_url}/shm/create_termflag_shm")
        print("POST /shm/create_termflag_shm:", response.json())

        response = requests.post(f"{base_url}/shm/create_facecam_shm")
        print("POST /shm/create_facecam_shm:", response.json())

        response = requests.post(f"{base_url}/procs/launch_log_facecam")
        print("POST /procs/launch_log_facecam:", response.json())
        
        response = requests.post(f"{base_url}/procs/launch_facecam2shm")
        print("POST /procs/launch_facecam2shm:", response.json())
        
        response = requests.post(f"{base_url}/procs/launch_stream_facecam")
        print("POST /procs/launch_stream_facecam:", response.json())
        
        
        
        
        # response = requests.post(f"{base_url}/shm/create_bodycam_shm")
        # print("POST /shm/create_bodycam_shm:", response.json())

        # response = requests.post(f"{base_url}/procs/launch_bodycam2shm")
        # print("POST /procs/launch_bodycam2shm:", response.json())
        
        # time.sleep(1)
        # response = requests.post(f"{base_url}/procs/launch_stream_bodycam")
        # print("POST /procs/launch_stream_bodycam:", response.json())

    def term():
        # POST /term_session
        response = requests.post(f"{base_url}/raise_term_flag")
        print("POST /raise_term_flag:", response.json())

    def inputloop():
        while True:
            msg = input("Press Enter to send Unity input...")
            requests.post(f"{base_url}/unityinput/{msg}", json={"message": msg})
            
    def test_proc_session():
        
        # POST /initiate
        response = requests.post(f"{base_url}/initiate")
        print("POST /initiate:", response.json())
        
        response = requests.post(f"{base_url}/procs/launch_process_session")
        print("POST /procs/launch_process_session:", response.json())
        
    # POST /initiate
    response = requests.post(f"{base_url}/initiate")
    print("POST /initiate:", response.json())

    # POST /shm/create_termflag_shm
    response = requests.post(f"{base_url}/shm/create_termflag_shm")
    print("POST /shm/create_termflag_shm:", response.json())
    
    # POST /shm/create_ballvelocity_shm
    response = requests.post(f"{base_url}/shm/create_ballvelocity_shm")
    print("POST /shm/create_ballvelocity_shm:", response.json())

    
    term()
    
if __name__ == "__main__":
    test_endpoints()