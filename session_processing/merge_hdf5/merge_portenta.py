import pandas as pd
import merge_utils as utils
import os


def merge_ball_velocity_hdf5(L, session_dir, df_trialPackage):

    # read the dataframe of ball velocity
    portenta_output_hdf5 = os.path.join(session_dir, 'portenta_output.hdf5')

    if not os.path.exists(portenta_output_hdf5):
        L.logger.error(f"Failed to find portenta_output.hdf5 file: {portenta_output_hdf5}")
        return

    try:
        df_ball_velocity = pd.read_hdf(portenta_output_hdf5, key='ballvelocity')
    except:
        L.logger.error(f"Failed to read ballvelocity from portenta_output.hdf5 file: {portenta_output_hdf5}")
        return

    # drop the unused identifier column
    df_ball_velocity.drop(columns=['N'], inplace=True)
    df_ball_velocity.reset_index(drop=True, inplace=True)

    # add session and trial info into df
    df_ball_velocity = utils.add_trial_into_df(df_trialPackage, df_ball_velocity)

    # rename the columns
    df_ball_velocity.rename(columns={"ID": "ball_velocity_package_id", 
                                     "T": "ball_velocity_t", 
                                     "F": "ball_velocity_f",
                                     "PCT": "ball_velocity_timestamp", 
                                     "Vr": "vr", "Vy": "vy", "Vp":"vp"}, inplace=True)


    utils.merge_into_hdf5(L, session_dir, df_ball_velocity, 'ball_velocity')



def merge_event_hdf5(L, session_dir, df_trialPackage):
    
    portenta_output_hdf5 = os.path.join(session_dir, 'portenta_output.hdf5')

    if not os.path.exists(portenta_output_hdf5):
        L.logger.error(f"Failed to find portenta_output.hdf5 file: {portenta_output_hdf5}")
        return

    # read the dataframe of event
    try:
        df_event = pd.read_hdf(portenta_output_hdf5, key='portentaoutput')
    except:
        L.logger.error(f"Failed to read portentaoutput from portenta_output.hdf5 file: {portenta_output_hdf5}")
        return
    
    df_event.reset_index(drop=True, inplace=True)

    # add session and trial info into df
    df_event = utils.add_trial_into_df(df_trialPackage, df_event)

    # rename the columns
    df_event.rename(columns={"ID": "event_package_id", 
                             "T": "event_t", 
                             "PCT": "event_timestamp", 
                             "V": "event_v", 
                             "F": "event_f", 
                             "N": "event_type"}, inplace=True)


    utils.merge_into_hdf5(L, session_dir, df_event, 'event')