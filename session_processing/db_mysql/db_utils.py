import os
import pandas as pd

from CustomLogger import CustomLogger as Logger

def add_session_into_df(cursor, df):
   # based on the last entry of the session table, add the session_id into the dataframe
   cursor.execute("SELECT session_id FROM session ORDER BY session_id DESC LIMIT 1")
   df["session_id"] = cursor.fetchall()[0][0]
   df["session_id"] = df["session_id"].astype(int)
   return df

def read_file_from_hdf5(session_dir, fname, file_name):

   behavior_fpath = os.path.join(session_dir, fname)

   try:
      df = pd.read_hdf(behavior_fpath, key=file_name)
   except:
      Logger().logger.error(f"Failed to read {file_name} from behavior file: {behavior_fpath}")
      return None
   
   return df

def add_file_from_hdf5_to_db(conn, cursor, engine, session_dir, fname, file_name):
   # read the file from hdf5
   df = read_file_from_hdf5(session_dir, fname, file_name)

   if df is None:
      return
   
   # add session and trial info into df
   df = add_session_into_df(cursor, df)
   df.to_sql(file_name, con=engine, if_exists='append', index=False)
   Logger().logger.info(f"{file_name} added to db successfully.")
   
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