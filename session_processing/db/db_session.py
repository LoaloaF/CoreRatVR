def db_session(L, conn, cursor, df_session):

    # extract the session info stored in the main session table
    paradigm_name = df_session["paradigm_name"][0]
    cursor.execute("SELECT paradigm_id FROM paradigm WHERE paradigm_name=?", (paradigm_name,))
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        cursor.execute("INSERT INTO paradigm (paradigm_name) VALUES (?)", (paradigm_name,))

    animal_name = df_session["animal_name"][0]
    cursor.execute("SELECT animal_id FROM animal WHERE animal_name=?", (animal_name,))
    fetch_result = cursor.fetchall()
    if len(fetch_result) == 0:
        cursor.execute("INSERT INTO animal (animal_name) VALUES (?)", (animal_name,))

    cursor.execute(f"PRAGMA table_info(session)")
    columns_info = cursor.fetchall()
    column_names = [column[1] for column in columns_info]
    session_columns = column_names[1:]

    for each_column in session_columns:
        if each_column not in df_session.columns:
            df_session[each_column] = None
    
    # if the column is not in the desired column, drop it
    for each_column in df_session.columns:
        if each_column not in session_columns:
            df_session = df_session.drop(columns=each_column)

    # check if the session already exists
    # if exists, raise an error
    # if not, add the session and its parameters
    session_name = df_session['session_name'].values[0]
    cursor.execute(f"SELECT * from session WHERE session_name=?", (session_name,))
    if len(cursor.fetchall()) != 0:
        raise ValueError(f"Session {session_name} already exists.")
    else:
        df_session.to_sql('session', conn, if_exists='append', index=False)        
        L.logger.info(f"Session {session_name} added successfully.")


def db_session_parameters(L, conn, cursor, df_session):

    # extract the column names in the session_parameter table
    cursor.execute(f"PRAGMA table_info(session_parameter)")
    columns_info = cursor.fetchall()
    column_names = [column[1] for column in columns_info]
    parameters_full_column = column_names[1:]

    # if the required column in the table is not present in the df_session_parameters, add it
    for each_column in parameters_full_column:
        if each_column not in df_session.columns:
            df_session[each_column] = None
    
    # if the column is not in the desired column, drop it
    for each_column in df_session.columns:
        if each_column not in parameters_full_column:
            df_session = df_session.drop(columns=each_column)
    
    # reformat the dictionary entries to string
    df_session['configuration'] = df_session['configuration'].astype(str)
    df_session['pillars'] = df_session['pillars'].astype(str)
    df_session['pillar_details'] = df_session['pillar_details'].astype(str)
    df_session.to_sql('session_parameter', conn, if_exists='append', index=False)
    L.logger.info(f"Session parameters added successfully.")

