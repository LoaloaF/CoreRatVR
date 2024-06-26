import argparse
import sqlite3
import os


def create_ratvr_db(db_name):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # SQL statements for creating tables and adding indexes/constraints

    # animal table
    cursor.execute("""
        CREATE TABLE animal (
            animal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_name TEXT NOT NULL,
            animal_gender TEXT,
            animal_description TEXT
        );
    """)

    #TODO think about states addtions / new table

    # paradigm table
    cursor.execute("""
        CREATE TABLE paradigm (
            paradigm_id INTEGER PRIMARY KEY AUTOINCREMENT,
            paradigm_name TEXT NOT NULL,
            paradigm_description TEXT
        );
    """)

    # session table
    cursor.execute("""
        CREATE TABLE session (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            session_path TEXT NOT NULL,
            paradigm_name TEXT NOT NULL,
            animal_name TEXT NOT NULL,
            start_time DATE,
            stop_time DATE,
            duration DOUBLE,
            notes TEXT
        );
    """)

    # session_parameter table
    cursor.execute("""
        CREATE TABLE session_parameter (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reward_post_sound_delay SMALLINT,
            reward_amount SMALLINT,
            punishment_length SMALLINT,
            punishment_inactivation_length SMALLINT,
            inter_trial_interval_length SMALLINT,
            abort_inter_trial_interval_length SMALLINT,
            success_sequence_length SMALLINT,
            maxium_trial_length SMALLINT,
            session_description TEXT,
            configuration TEXT,
            metadata TEXT,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)

    # ball_velocity table
    cursor.execute("""
        CREATE TABLE ballvelocity (
            ballvelocity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id INT NOT NULL,
            ballvelocity_package_id BIGINT NOT NULL,
            ballvelocity_portenta_timestamp BIGINT NOT NULL,
            ballvelocity_pc_timestamp BIGINT NOT NULL,
            ballvelocity_raw DOUBLE NOT NULL,
            ballvelocity_yaw DOUBLE NOT NULL,
            ballvelocity_pitch DOUBLE NOT NULL,
            ballvelocity_ephys_timestamp BIGINT,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    # double session_id?
    cursor.execute("CREATE INDEX ballvelocity_session_id_index ON ballvelocity(session_id);")
    cursor.execute("CREATE INDEX ballvelocity_trial_id_index ON ballvelocity(trial_id);")
    cursor.execute("CREATE INDEX ballvelocity_ballvelocity_ephys_timestamp_index ON ballvelocity(ballvelocity_ephys_timestamp);")

    # event table
    cursor.execute("""
        CREATE TABLE event (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id BIGINT NOT NULL,
            event_name TEXT NOT NULL,
            event_package_id INT NOT NULL,
            event_portenta_timestamp BIGINT NOT NULL,
            event_pc_timeStamp BIGINT NOT NULL,
            event_value int NOT NULL,
            event_ephys_timestamp BIGINT,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX event_session_id_index ON event(session_id);")
    cursor.execute("CREATE INDEX event_trial_id_index ON event(trial_id);")
    cursor.execute("CREATE INDEX event_event_ephys_timestamp_index ON event(event_ephys_timestamp);")

    # unity_frame table
    cursor.execute("""
        CREATE TABLE unity_frame (
            unity_frame_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id INT NOT NULL,
            frame_id BIGINT NOT NULL,
            frame_pc_timestamp BIGINT NOT NULL,
            frame_x_position DOUBLE NOT NULL,
            frame_z_position DOUBLE NOT NULL,
            frame_angle DOUBLE NOT NULL,
            frame_state INT NOT NULL,
            frame_blinker INT NOT NULL,
            ballvelocity_first_package DOUBLE NOT NULL,
            ballvelocity_last_package DOUBLE NOT NULL,
            frame_ephys_timestamp BIGINT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX unity_frame_session_id_index ON unity_frame(session_id);")
    cursor.execute("CREATE INDEX unity_frame_trial_id_index ON unity_frame(trial_id);")
    cursor.execute("CREATE INDEX unity_frame_frame_id_index ON unity_frame(frame_id);")

    # unity_trial table
    cursor.execute("""
        CREATE TABLE unity_trial (
            unity_trial_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id INT NOT NULL,
            trial_start_pc_timestamp BIGINT NOT NULL,
            trial_start_frame BIGINT NOT NULL,
            trial_end_pc_timestamp BIGINT NOT NULL,
            trial_end_frame BIGINT NOT NULL,
            trial_pc_duration BIGINT NOT NULL,
            trial_outcome INT NOT NULL,
            trial_start_ephys_timestamp BIGINT NOT NULL,
            trial_end_ephys_timestamp BIGINT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX unity_trial_session_id_index ON unity_trial(session_id);")
    cursor.execute("CREATE INDEX unity_trial_trial_id_index ON unity_trial(trial_id);")
    cursor.execute("CREATE INDEX unity_trial_trial_start_frame_index ON unity_trial(trial_start_frame);")
    cursor.execute("CREATE INDEX unity_trial_trial_end_frame_index ON unity_trial(trial_end_frame);")


    # face_cam table
    cursor.execute("""
        CREATE TABLE facecam (
            facecam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id INT NOT NULL,
            facecam_image_id BIGINT NOT NULL,
            facecam_image_pc_timestamp BIGINT NOT NULL,
            facecam_image_ephys_timestamp BIGINT,
            facecam_data BLOB NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX facecam_session_id_index ON facecam(session_id);")
    cursor.execute("CREATE INDEX facecam_trial_id_index ON facecam(trial_id);")
    cursor.execute("CREATE INDEX facecam_facecam_image_ephys_timestamp_index ON facecam(facecam_image_ephys_timestamp);")

    # body_cam table
    cursor.execute("""
        CREATE TABLE bodycam (
            bodycam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id BIGINT NOT NULL,
            bodycam_image_id BIGINT NOT NULL,
            bodycam_image_pc_timestamp BIGINT NOT NULL,
            bodycam_data BLOB NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX bodycam_session_id_index ON bodycam(session_id);")
    cursor.execute("CREATE INDEX bodycam_trial_id_index ON bodycam(trial_id);")

    # unity_cam table
    cursor.execute("""
        CREATE TABLE unitycam (
            unitycam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id INT NOT NULL,
            unitycam_image_id BIGINT NOT NULL,
            unitycam_image_pc_timestamp BIGINT NOT NULL,
            unitycam_image_ephys_timestamp BIGINT,
            unitycam_data BLOB NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX unitycam_session_id_index ON unitycam(session_id);")
    cursor.execute("CREATE INDEX unitycam_trial_id_index ON unitycam(trial_id);")
    cursor.execute("CREATE INDEX unitycam_unitycam_image_ephys_timestamp_index ON unitycam(unitycam_image_ephys_timestamp);")

    # paradigm_P0200 table
    cursor.execute("""
        CREATE TABLE paradigm_P0200 (
            paradigm_P0200_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id BIGINT NOT NULL,
            pillar_distance DOUBLE NOT NULL,
            pillar_angle DOUBLE NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX paradigm_p0200_session_id_index ON paradigm_P0200(session_id);")
    cursor.execute("CREATE INDEX paradigm_p0200_trial_id_index ON paradigm_P0200(trial_id);")

    # -S-
    # Put picture or svg of database schema in  directory 
    # -S-

    # Commit changes and close the connection
    # conn.commit()
    conn.close()
    
#TODO
def insert_new_paradim_table():
    pass
    # take in metadata arguments about paradigm variables
    # cursor.execute("""
    #     CREATE TABLE paradigm_P0200 (
    #         paradigm_P0200_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         session_id INT NOT NULL,
    #         trial_id BIGINT NOT NULL,
    #         pd DOUBLE NOT NULL,
    #         pa DOUBLE NOT NULL,
    #         FOREIGN KEY (session_id) REFERENCES session(session_id)
    #     );


if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Create rat VR behavior database.")
    argParser.add_argument("--path_to_db", type=str, default=".", help="Path to the database.")

    path = argParser.parse_args().path_to_db
    db_fname = "rat_vr.db"
    test_db_fname = "rat_vr_test.db"
    
    db_fullfname = os.path.join(path, db_fname)
    test_db_fullfname = os.path.join(path, test_db_fname)
    
    # Create the real database
    if os.path.exists(db_fullfname):
        raise ValueError(f"{db_fullfname} already exists. Cannot create a new database.")
    else:
        create_ratvr_db(db_fullfname)
        print(f"{db_fname} created successfully in {path}.")

    # Create the test database for test-writing
    if os.path.exists(test_db_fname):
        raise ValueError(f"{test_db_fullfname} already exists. Cannot create a new database.")
    else:
        create_ratvr_db(test_db_fullfname)
        print(f"{test_db_fname} created successfully in {path}.")
   
