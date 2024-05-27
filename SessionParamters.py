import os
import uuid
import json
from Parameters import Parameters
import shutil
import pandas as pd
import numpy as np

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
        cls._instance.paradigm_id = None
        cls._instance.animal = None
        cls._instance.animal_weight = None
        cls._instance.paradigm_df = None
        cls._instance.environment_df = None
        cls._instance.paradigm_pillar_types = None
        
        cls._instance.excel_paradigm_definions = {}

        return cls._instance

    def clear(self):
        self.session_id = None
        self.paradigm_name = None
        self.animal = None
        self.animal_weight = None
        self.paradigm_df = None
        self.paradigm_pillar_types = None
        
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
        self.paradigm_df = pd.read_excel(dst_paradigm_excelfullfname,
                                                sheet_name="SessionParameters").set_index("Session parameters", drop=True)
        environment_df = pd.read_excel(dst_paradigm_excelfullfname,
                                       sheet_name="Environment").set_index("Unnamed: 0")
        env_params_df = pd.read_excel(dst_paradigm_excelfullfname,
                                      sheet_name="EnvParameters")
        self.extract_paradigm_parameters(environment_df, env_params_df)
        
    def extract_paradigm_parameters(self, environment_df, env_params_df):
        # print(environment_df, env_params_df)
        x_indices_pillar, y_indices_pillar = np.where(environment_df.notna())
        pillars = {i: {"id":int(environment_df.iloc[x,y]), "x":int(x), "y":int(y)}
                   for i, (x,y) in enumerate(zip(x_indices_pillar, y_indices_pillar))}
        print(pillars)
        
        pillar_details = env_params_df.iloc[:,:8].dropna(how='all').set_index("pillarIdentifier")
        pillar_details.index = pillar_details.index.astype(int)
        pillar_details.fillna(-1, inplace=True)
        pillar_details = {pillarIdent: dict(columns) for pillarIdent, columns in pillar_details.iterrows()}
        print(pillar_details)
        
        envX_size, envY_size = env_params_df.iloc[0,14:16]
        wallzone_size = env_params_df.iloc[1,14]
        wallzone_collider_size = env_params_df.iloc[2,14]
        print(envX_size,envY_size,wallzone_size,wallzone_collider_size)
        
        # self.excel_paradigm_definions = {
        #     "pillars": pillars,
        #     "pillar_details": pillar_details,
        #     "envX_size": envX_size,
        #     "envY_size": envY_size,
        #     "wallzone_size": wallzone_size,
        #     "wallzone_collider_size": wallzone_collider_size
        # }
        self.excel_paradigm_definions = {
            # "pillars": {int(k): (int(v[0]), int(v[1])) for k, v in pillars.items()},
            "pillars": pillars,
            "pillar_details": {int(k): {str(kk): int(vv) if isinstance(vv, np.int64) else vv for kk, vv in v.items()} for k, v in pillar_details.items()},
            "envX_size": int(envX_size),
            "envY_size": int(envY_size),
            "wallzone_size": int(wallzone_size),
            "wallzone_collider_size": int(wallzone_collider_size)
        }
        
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