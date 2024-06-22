import os

def merge_into_hdf5(L, session_dir, df, hdf5_key):

   behavior_hdf5 = os.path.join(session_dir, 'behavior.hdf5')
   df.to_hdf(behavior_hdf5, key=hdf5_key, mode='a', format='table', append=True)
   L.logger.info(f"{hdf5_key} merged into hdf5 successfully.")
   print(f"{hdf5_key} merged into hdf5 successfully.")

def camel_to_snake(camel_case_string):
   # transform camel case to snake case
   snake_case_string = ""
   for i, c in enumerate(camel_case_string):
      if i == 0:
         snake_case_string += c.lower()
      elif c.isupper():
         snake_case_string += "_" + c.lower()
      else:
         snake_case_string += c

   return snake_case_string

def generate_trialID_start_timestamps(which_time):
   pass
   # which_time can be PCT or ET
   # function below has the issue that the timestamp is unreliable (PCT) - 
   # it should use ET (ephys timestamp) instead if available 
   # return trial_start_tstamps
   
def get_trialID_from_timestamp(trial_start_tstamps, timestamps):
   pass
   # trial_start_tstamps is an array like [[trial_id, start_timestamp], ...] with n = number of trials
   # timestamps are the timestamp of the events
   # function should be vectorized to handle timestamps arr
   # return trial_ids
   
def add_trial_into_df(df_trialPackage, df):
   # based on the timestamp of each trial, add the trial_id into the dataframe

   # df.drop(df[(df['PCT'] < min_PCT) | (df['PCT'] > max_PCT)].index, inplace=True)
   
   trial_time_list = list(zip(df_trialPackage['trial_start_timestamp'], 
                              df_trialPackage['trial_end_timestamp'], 
                              df_trialPackage['trial_id']))

   for trial_time_pair in trial_time_list:
      df.loc[(df['PCT'] >= trial_time_pair[0]) & 
            (df['PCT'] <= trial_time_pair[1]), 'trial_id'] = trial_time_pair[2]

   df['trial_id'] = df['trial_id'].fillna(-1)
   df['trial_id'] = df['trial_id'].astype(int)

   df.reset_index(drop=True, inplace=True)
   return df