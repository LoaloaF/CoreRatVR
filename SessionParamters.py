from datetime import datetime
import os
import uuid
import json
import shutil
import pandas as pd
import numpy as np

from Parameters import Parameters
from CustomLogger import CustomLogger as Logger

class SessionParamters:
    _instance = None

    def __new__(cls):
        if cls._instance:
            return cls._instance
        cls._instance = super(SessionParamters, cls).__new__(cls)

        cls._instance.L = Logger()
        # cls._instance.session_id = None
        
        # this set of parametesr is instantiated at when Start Paradigm button clicked
        cls._instance.paradigm_name = None
        cls._instance.paradigm_id = None
        cls._instance.animal = None
        cls._instance.animal_weight = None
        cls._instance.start_time = None
        
        # at end paradigm button clicked
        cls._instance.stop_time = None
        cls._instance.duration = None
        cls._instance.notes = None

        # These 2 dictionarys stores everything from the 3 excel sheets
        cls._instance.session_parameters_dict = {}
        cls._instance.environment_parameters_dict = {}


        return cls._instance
    
    def clear(self):
        self.paradigm_name = None
        self.paradigm_id = None
        self.animal = None
        self.animal_weight = None
        self.start_time = None
        
        self.session_parameters = None
        self.environment_parameters = None
        
        self.stop_time = None
        self.duration = None
        self.notes = None
        
    def handle_start_session(self):
        self.start_time = datetime.now()
        # UI ensures that POST requests for paradigm_name, animal, animal_weight are made
        self.paradigm_id = int(self.paradigm_name[1:5])
        paradigm_excelfullfname = self._copy_paradigm_excel_to_session_dir()
        self._extract_metadata_from_paradigm_excel(paradigm_excelfullfname)

    def handle_stop_session(self):
        self.stop_time = datetime.now()
        self.duration = self.stop_time - self.start_time
        self._save_session_parameters()

    def _copy_paradigm_excel_to_session_dir(self):
        P = Parameters()
        p = P.PROJECT_DIRECTORY, "UnityRatVR", "Paradigms", self.paradigm_name+".xlsx"
        src_paradigm_excelfullfname = os.path.join(*p)
        dst_paradigm_excelfullfname = os.path.join(P.SESSION_DATA_DIRECTORY, 
                                                   self.paradigm_name+".xlsx")
        shutil.copy(src_paradigm_excelfullfname, dst_paradigm_excelfullfname)
        return dst_paradigm_excelfullfname

    def _extract_metadata_from_paradigm_excel(self, paradigm_excelfullfname):
        # read the 3 excel sheets
        env_df = pd.read_excel(paradigm_excelfullfname,
                               sheet_name="Environment").set_index("Unnamed: 0")
        env_params_df = pd.read_excel(paradigm_excelfullfname,
                                      sheet_name="EnvParameters")
        meatadata_df = pd.read_excel(paradigm_excelfullfname,
                                     sheet_name="SessionParameters")
        meatadata_df = meatadata_df.set_index("Session parameters").iloc[:, 0:1]
        
        # extract environment dictionary from the 1st and 2nd sheets
        self.extract_env_dict(env_df, env_params_df)
        # extract session dictionary from the 3rd sheet
        self.extract_session_dict(meatadata_df)

    def extract_env_dict(self, env_df, env_params_df):
        # print(environment_df, env_params_df)
        x_indices_pillar, y_indices_pillar = np.where(env_df.notna())
        pillars = {i: {"id":int(env_df.iloc[x,y]), "x":int(x), "y":int(y)}
                   for i, (x,y) in enumerate(zip(x_indices_pillar, y_indices_pillar))}
        
        pillar_details = env_params_df.iloc[:,:8].dropna(how='all').set_index("pillarIdentifier")
        pillar_details.index = pillar_details.index.astype(int)
        pillar_details.fillna(-1, inplace=True)
        pillar_details = {pillarIdent: dict(columns) for pillarIdent, columns 
                          in pillar_details.iterrows()}
        pillar_details = {int(k): {str(kk): int(vv) if isinstance(vv, np.int64) else vv for kk, vv in v.items()} 
                          for k, v in pillar_details.items()}
        
        envX_size, envY_size = env_params_df.iloc[0,14:16]
        base_length = env_params_df.iloc[1,14]
        wallzone_size = env_params_df.iloc[2,14]
        wallzone_collider_size = env_params_df.iloc[3,14]
        
        self.environment_parameters_dict = {
            "pillars": pillars,
            "pillar_details": pillar_details,
            "envX_size": int(envX_size),
            "envY_size": int(envY_size),
            "base_length": int(base_length),
            "wallzone_size": int(wallzone_size),
            "wallzone_collider_size": int(wallzone_collider_size)
        }
        self.L.logger.debug("Environment parameters:")
        self.L.logger.debug(self.L.fmtmsg(self.environment_parameters_dict))
        
    def extract_session_dict(self, session_df):
        session_params_dict = session_df.to_dict()
        session_paramsdict = session_params_dict["Values"]
        self.session_parameters_dict = session_paramsdict

        self.L.logger.debug("Session metadata:")
        self.L.logger.debug(self.L.fmtmsg(self.session_parameters_dict))        
        
    def _save_session_parameters(self):
        P = Parameters()
        params = {
            "session_id": None,
            "paradigm_name": self.paradigm_name,
            "animal": self.animal.replace("_", ""),
            "animal_weight": self.animal_weight,
            
            "start_time": self.start_time.strftime("%Y-%m-%d_%H-%M-%S"),
            "stop_time": self.stop_time.strftime("%Y-%m-%d_%H-%M-%S"),
            "duration": f"{int(self.duration.total_seconds()/60)}min",
            "notes": self.notes,
        }
        
        # append the meta data dictionaries from excel sheets
        params.update(self.session_parameters_dict)
        params.update(self.environment_parameters_dict)
        self.L.logger.info(self.L.fmtmsg(params))
        
        fullffname = os.path.join(P.SESSION_DATA_DIRECTORY, "session_parameters.json")
        with open(fullffname, 'w') as f:
            json.dump(params, f)