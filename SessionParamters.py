import os
import uuid
import json
from Parameters import Parameters
import shutil
import pandas as pd

# class SessionParamters(object):
#     def __init__(self):
#         self.session_id = None
#         self.paradigm_name = None
#         self.animal = None
#         self.animal_weight = None
#         self.paradigm_dataframe

class SessionParamters:
    _instance = None

    def __new__(cls):
        if cls._instance:
            return cls._instance
        cls._instance = super(SessionParamters, cls).__new__(cls)

        cls._instance.session_id = None
        cls._instance.paradigm_name = None
        cls._instance.animal = None
        cls._instance.animal_weight = None
        cls._instance.paradigm_df = None
        cls._instance.paradigm_pillar_types = None

        return cls._instance
        
    def handle_start_session(self):
        self.session_id = str(uuid.uuid4())[:16]
        self._copy_paradigm_excel_to_session_dir()
    
    def handle_stop_session(self):
        self._save_session_parameters()
    
    def _copy_paradigm_excel_to_session_dir(self):
        P = Parameters()
        p = P.PROJECT_DIRECTORY, "UnityRatVR", "Paradigms", self.paradigm_name+".xlsx"
        src_paradigm_excelfullfname = os.path.join(*p)
        dst_paradigm_excelfullfname = os.path.join(P.SESSION_DATA_DIRECTORY, 
                                                   self.paradigm_name+".xlsx")
        shutil.copy(src_paradigm_excelfullfname, dst_paradigm_excelfullfname)
        self.paradigm_df = pd.read_excel(dst_paradigm_excelfullfname,
                                                sheet_name="SessionParameters").set_index("Session parameters", drop=True)
        self.extract_paradigm_parameters()
        
    def extract_paradigm_parameters(self):
        rp_min = self.paradigm_df.loc["rewardedPillarsMin"].iloc[0]
        rp_max = self.paradigm_df.loc["rewardedPillarsMax"].iloc[0]
        if rp_min == -1 and rp_max == -1:
            self.paradigm_pillar_types = "none"
        else:
            self.paradigm_pillar_types = ",".join([p for p in range(rp_min,rp_max+1)])
        
        
    def _save_session_parameters(self):
        P = Parameters()
        params = {
            "session_id": self.session_id,
            "paradigm_name": self.paradigm_name,
            "animal": self.animal,
            "animal_weight": self.animal_weight,
        }
        fullffname = os.path.join(P.SESSION_DATA_DIRECTORY, "session_parameters.json")
        with open(fullffname, 'w') as f:
            json.dump(params, f)