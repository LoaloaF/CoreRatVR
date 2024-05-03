import os
import uuid
import json
from Parameters import Parameters
import shutil

class SessionParamters(object):
    def __init__(self):
        self.session_id = None
        self.paradigm_name = None
        self.animal = None
        self.animal_weight = None
        
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