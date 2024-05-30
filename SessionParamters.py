import os
import uuid
import json
from Parameters import Parameters
import shutil
import pandas as pd
import numpy as np

class SessionParamters:
    _instance = None

    def __new__(cls):
        if cls._instance:
            return cls._instance
        cls._instance = super(SessionParamters, cls).__new__(cls)

        cls._instance.session_id = None
        cls._instance.paradigm_name = None
        cls._instance.paradigm_id = None
        cls._instance.animal = None
        cls._instance.animal_weight = None

        # These 2 dictionarys stores everything from the 3 excel sheets
        cls._instance.session_parameters_dict = {}
        cls._instance.environment_parameters_dict = {}

        # the below code is temporary due to the execuation order problem; now is hard coded
        cls._instance.session_parameters_dict["trialPackageVariables"] = "PA,PD"

        return cls._instance

    def clear(self):
        self.session_id = None
        self.paradigm_name = None
        self.animal = None
        self.animal_weight = None

        self._instance.session_parameters = None
        self._instance.environment_parameters = None
        
    def handle_start_session(self):
        self.session_id = str(uuid.uuid4())[:16]
        self._copy_paradigm_excel_to_session_dir()
        self.paradigm_id = int(self.paradigm_name[1:5])
    
    def handle_stop_session(self):
        self._save_session_parameters()
    

    def _copy_paradigm_excel_to_session_dir(self):
        P = Parameters()
        p = P.PROJECT_DIRECTORY, "UnityRatVR", "Paradigms", self.paradigm_name+".xlsx"
        src_paradigm_excelfullfname = os.path.join(*p)
        dst_paradigm_excelfullfname = os.path.join(P.SESSION_DATA_DIRECTORY, 
                                                   self.paradigm_name+".xlsx")
        shutil.copy(src_paradigm_excelfullfname, dst_paradigm_excelfullfname)

        # read the 3 excel sheets
        env_df = pd.read_excel(dst_paradigm_excelfullfname,
                                       sheet_name="Environment").set_index("Unnamed: 0")
        env_params_df = pd.read_excel(dst_paradigm_excelfullfname,
                                      sheet_name="EnvParameters")
        session_df = pd.read_excel(dst_paradigm_excelfullfname,
                                        sheet_name="SessionParameters").set_index("Session parameters")
        
        # extract environment dictionary from the 1st and 2nd sheets
        self.extract_env_dict(env_df, env_params_df)
        # extract session dictionary from the 3rd sheet
        self.extract_session_dict(session_df)

        
    def extract_env_dict(self, env_df, env_params_df):
        # print(environment_df, env_params_df)
        x_indices_pillar, y_indices_pillar = np.where(env_df.notna())
        pillars = {i: {"id":int(env_df.iloc[x,y]), "x":int(x), "y":int(y)}
                   for i, (x,y) in enumerate(zip(x_indices_pillar, y_indices_pillar))}
        print(pillars)
        
        pillar_details = env_params_df.iloc[:,:8].dropna(how='all').set_index("pillarIdentifier")
        pillar_details.index = pillar_details.index.astype(int)
        pillar_details.fillna(-1, inplace=True)
        pillar_details = {pillarIdent: dict(columns) for pillarIdent, columns in pillar_details.iterrows()}
        print(pillar_details)
        
        envX_size, envY_size = env_params_df.iloc[0,14:16]
        base_length = env_params_df.iloc[1,14]
        wallzone_size = env_params_df.iloc[2,14]
        wallzone_collider_size = env_params_df.iloc[3,14]
        print(envX_size,envY_size, base_length, wallzone_size,wallzone_collider_size)
        
        self.environment_parameters_dict = {
            "pillars": pillars,
            "pillar_details": {int(k): {str(kk): int(vv) if isinstance(vv, np.int64) else vv for kk, vv in v.items()} for k, v in pillar_details.items()},
            "envX_size": int(envX_size),
            "envY_size": int(envY_size),
            "base_length": int(base_length),
            "wallzone_size": int(wallzone_size),
            "wallzone_collider_size": int(wallzone_collider_size)
        }
        
    def extract_session_dict(self, session_df):
        session_params_df = session_df.iloc[1:, 0:1]
        session_params_dict = session_params_df.to_dict()
        session_paramsdict = session_params_dict["Values"]
        self.session_parameters_dict = session_paramsdict
        
        
    def _save_session_parameters(self):
        P = Parameters()
        params = {
            "session_id": self.session_id,
            "paradigm_name": self.paradigm_name,
            "animal": self.animal,
            "animal_weight": self.animal_weight,
        }

        # here we also append the session parameter dictionary we generated before
        params.update(self.session_parameters_dict)

        fullffname = os.path.join(P.SESSION_DATA_DIRECTORY, "session_parameters.json")
        with open(fullffname, 'w') as f:
            json.dump(params, f)