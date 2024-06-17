def add_session(L, df, conn, cursor):

    # extract the session info stored in the main session table
    session_columns = ["session_name", "session_time", "session_path", 
                       "paradigm_id", "animal_id", "animal_weight"]
    df_session = df[session_columns]

    # check if the session already exists
    # if exists, raise an error
    # if not, add the session and its parameters
    session_time = df_session['session_time'].values[0]
    cursor.execute("SELECT * from session WHERE session_time=?", (session_time,))
    if len(cursor.fetchall()) != 0:
        raise ValueError(f"Session recorded at {session_time} already exists.")
    else:
        df_session.to_sql('session', conn, if_exists='append', index=False)        
        add_session_parameters(L, conn, cursor, df)
        L.logger.info(f"Session at {session_time} added successfully.")

def add_session_parameters(L, conn, cursor, df):

    # drop the columns already stored in the session table
    session_columns = ["session_name", "session_time", "session_path", 
                       "paradigm_id", "animal_id", "animal_weight"]
    df_session_parameters = df.drop(columns=session_columns)

    # extract the column names in the session_parameter table
    cursor.execute(f"PRAGMA table_info(session_parameter)")
    columns_info = cursor.fetchall()
    column_names = [column[1] for column in columns_info]
    parameters_full_column = column_names[1:]

    # if the required column in the table is not present in the df_session_parameters, add it
    for each_column in parameters_full_column:
        if each_column not in df_session_parameters.columns:
            df_session_parameters[each_column] = None
    
    # if the column is not in the desired column, drop it
    for each_column in df_session_parameters.columns:
        if each_column not in parameters_full_column:
            df_session_parameters.drop(columns=each_column, inplace=True)
    
    # reformat the dictionary entries to string
    df_session_parameters['pillars'] = df_session_parameters['pillars'].astype(str)
    df_session_parameters['pillar_details'] = df_session_parameters['pillar_details'].astype(str)
    df_session_parameters.to_sql('session_parameter', conn, if_exists='append', index=False)

    L.logger.info("Session parameters added successfully.")
