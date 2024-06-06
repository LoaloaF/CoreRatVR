import sqlite3


def dict_to_db(cursor, dict, table):
    columns = ', '.join(dict.keys())
    placeholders = ', '.join('?' * len(dict))
    sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table, columns, placeholders)
    cursor.execute(sql, tuple(dict.values()))

def camel_to_snake(camel_case_string):
   snake_case_string = ""
   for i, c in enumerate(camel_case_string):
      if i == 0:
         snake_case_string += c.lower()
      elif c.isupper():
         snake_case_string += "_" + c.lower()
      else:
         snake_case_string += c

   return snake_case_string

def add_session_into_df(cursor, df):
    cursor.execute("SELECT session_id FROM session ORDER BY session_id DESC LIMIT 1")
    df["session_id"] = cursor.fetchall()[0][0]
    df["session_id"] = df["session_id"].astype(int)

    return df

def add_trial_into_df(df_trialPackage, df):
    min_PCT = df_trialPackage['trial_start_timestamp'].min()
    max_PCT = df_trialPackage['trial_end_timestamp'].max()

    df.drop(df[(df['PCT'] < min_PCT) | (df['PCT'] > max_PCT)].index, inplace=True)
    
    trial_time_list = list(zip(df_trialPackage['trial_start_timestamp'], df_trialPackage['trial_end_timestamp'], df_trialPackage['trial_id']))

    for trial_time_pair in trial_time_list:
        df.loc[(df['PCT'] >= trial_time_pair[0]) & (df['PCT'] <= trial_time_pair[1]), 'trial_id'] = trial_time_pair[2]

    # df.dropna(subset=['trial_id'], inplace=True)
    df['trial_id'] = df['trial_id'].fillna(-1)
    df['trial_id'] = df['trial_id'].astype(int)

    df.reset_index(drop=True, inplace=True)
    return df