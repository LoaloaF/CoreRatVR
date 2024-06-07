import os
import sqlite3
import pandas as pd


def add_session(df, conn, cursor):
    session_columns = ["session_name", "session_time", "session_path", "paradigm_id", "animal_id", "animal_weight"]
    df_session = df[session_columns]

    session_time = df_session['session_time'].values[0]
    cursor.execute("SELECT * from session WHERE session_time=?", (session_time,))
    if len(cursor.fetchall()) != 0:
        raise ValueError(f"Session recorded at {session_time} already exists.")
    else:
        df_session.to_sql('session', conn, if_exists='append', index=False)
        add_session_parameters(conn, df)
        print(f"Session at {session_time} added successfully.")

def add_session_parameters(conn, df):
    session_columns = ["session_name", "session_time", "session_path", "paradigm_id", "animal_id", "animal_weight"]
    df_session_parameters = df.drop(columns=session_columns)

    parameters_full_column = ["reward_post_sound_delay", "reward_amount", "punishment_length", "punishment_inactivation_length",
                              "on_wall_zone_entry", "on_inter_trial_interval", "inter_trial_interval_length",
                              "abort_inter_trial_interval_length", "success_sequence_length", "maxium_trial_length",
                              "trial_package_variables", "trial_package_variables_default", "session_description",
                              "pillars", "pillar_details", "env_x_size", "env_y_size", "base_length", "wallzone_size",
                              "wallzone_collider_size"]

    for each_column in parameters_full_column:
        if each_column not in df_session_parameters.columns:
            df_session_parameters[each_column] = None
    
    for each_column in df_session_parameters.columns:
        if each_column not in parameters_full_column:
            df_session_parameters.drop(columns=each_column, inplace=True)
    
    df_session_parameters['pillars'] = df_session_parameters['pillars'].astype(str)
    df_session_parameters['pillar_details'] = df_session_parameters['pillar_details'].astype(str)
    df_session_parameters.to_sql('session_parameter', conn, if_exists='append', index=False)

    print("Session parameters added successfully.")