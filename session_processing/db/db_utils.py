import os
import pandas as pd

# def dict_to_db(cursor, dict, table):
#    # put a dictionary into a database
#    columns = ', '.join(dict.keys())
#    placeholders = ', '.join('?' * len(dict))
#    sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table, columns, placeholders)
#    cursor.execute(sql, tuple(dict.values()))

def add_session_into_df(cursor, df):
   # based on the last entry of the session table, add the session_id into the dataframe
   cursor.execute("SELECT session_id FROM session ORDER BY session_id DESC LIMIT 1")
   df["session_id"] = cursor.fetchall()[0][0]
   df["session_id"] = df["session_id"].astype(int)

   return df


def read_file_from_hdf5(L, session_dir, file_name):
   try:
      behavior_fpath = os.path.join(session_dir, 'behavior.hdf5')
   except:
      raise FileNotFoundError(f"Failed to find behavior file in {session_dir}")
   
   try:
      df = pd.read_hdf(behavior_fpath, key=file_name)
   except:
      L.logger.error(f"Failed to read {file_name} from behavior file: {behavior_fpath}")
      return None
   
   return df


def add_file_from_hdf5_to_db(L, conn, cursor, session_dir, file_name):
   # read the file from hdf5
   df = read_file_from_hdf5(L, session_dir, file_name)

   if df is None:
      return
   
   # add session and trial info into df
   df = add_session_into_df(cursor, df)

   df.to_sql(file_name, conn, if_exists='append', index=False)

   L.logger.info(f"{file_name} added to db successfully.")
   