import pandas as pd
from add_utils import *
import os


def add_ball_velocity(L, conn, cursor, folder_path, df_trialPackage):

    # read the dataframe of ball velocity
    df_ball_velocity = pd.read_hdf(os.path.join(folder_path, 'portenta_output.hdf5'), key='ballvelocity')

    # drop the unused identifier column
    df_ball_velocity.drop(columns=['N'], inplace=True)
    df_ball_velocity.reset_index(drop=True, inplace=True)

    # add session and trial info into df
    df_ball_velocity = add_session_into_df(cursor, df_ball_velocity)
    df_ball_velocity = add_trial_into_df(df_trialPackage, df_ball_velocity)

    # rename the columns
    df_ball_velocity.rename(columns={"ID": "ball_velocity_package_id", 
                                     "T": "ball_velocity_t", 
                                     "F": "ball_velocity_f",
                                     "PCT": "ball_velocity_timestamp", 
                                     "Vr": "vr", "Vy": "vy", "Vp":"vp"}, inplace=True)

    df_ball_velocity.to_sql('ball_velocity', conn, if_exists='append', index=False)

    L.logger.info("Ball velocity added successfully.")



def add_event(L, conn, cursor, folder_path, df_trialPackage):
    
    # read the dataframe of event
    df_event = pd.read_hdf(os.path.join(folder_path, 'portenta_output.hdf5'), key='portentaoutput')
    df_event.reset_index(drop=True, inplace=True)

    # add session and trial info into df
    df_event = add_session_into_df(cursor, df_event)
    df_event = add_trial_into_df(df_trialPackage, df_event)

    # rename the columns
    df_event.rename(columns={"ID": "event_package_id", 
                             "T": "event_t", 
                             "PCT": "event_timestamp", 
                             "V": "event_v", 
                             "F": "event_f", 
                             "N": "event_type"}, inplace=True)

    df_event.to_sql('event', conn, if_exists='append', index=False)

    L.logger.info("Event added successfully.")