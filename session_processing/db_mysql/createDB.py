import argparse
import mysql.connector
from mysql.connector import Error
import os

def create_ratvr_db(db_name):
    # Connect to MySQL server (or create it if it doesn't exist)
    try:
        conn = mysql.connector.connect(
            host='82.130.67.135',  # Replace with your MySQL host
            user='ratVR',  # Replace with your MySQL username
            password='yaniklabratVR2024'  # Replace with your MySQL password
        )
        if conn.is_connected():
            print('Connected to MySQL server')

            cursor = conn.cursor()

            cursor.execute(f"SELECT SCHEMA_NAME FROM information_schema.schemata WHERE SCHEMA_NAME = '{db_name}'")
            result = cursor.fetchone()
            if result:
                raise ValueError(f"{db_fname} already exists. Cannot create a new database.")

            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
            print(f"Database '{db_name}' created successfully")

            # Switch to the created database
            cursor.execute(f"USE {db_name};")

            # SQL statements for creating tables and adding indexes/constraints

            # animal table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS animal (
                    animal_id INT AUTO_INCREMENT PRIMARY KEY,
                    animal_name VARCHAR(255) NOT NULL,
                    animal_gender VARCHAR(10),
                    animal_description TEXT
                );
            """)

            # paradigm table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paradigm_meta (
                    paradigm_meta_id INT AUTO_INCREMENT PRIMARY KEY,
                    paradigm_id INT NOT NULL,
                    paradigm_name VARCHAR(255) NOT NULL,
                    paradigm_description TEXT
                );
            """)

            # session table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session (
                    session_id INT AUTO_INCREMENT PRIMARY KEY,
                    session_name VARCHAR(255) NOT NULL,
                    paradigm_name VARCHAR(255) NOT NULL,
                    animal_name VARCHAR(255) NOT NULL,
                    start_time DATETIME,
                    stop_time DATETIME,
                    duration TEXT,
                    notes TEXT
                );
            """)

            # session_parameter table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_parameter (
                    session_id INT AUTO_INCREMENT PRIMARY KEY,
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
                CREATE TABLE IF NOT EXISTS ballvelocity (
                    ballvelocity_id INT AUTO_INCREMENT PRIMARY KEY,
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
            cursor.execute("CREATE INDEX ballvelocity_session_id_index ON ballvelocity(session_id);")
            cursor.execute("CREATE INDEX ballvelocity_trial_id_index ON ballvelocity(trial_id);")
            cursor.execute("CREATE INDEX ballvelocity_ballvelocity_package_id_index ON ballvelocity(ballvelocity_package_id);")
            cursor.execute("CREATE INDEX ballvelocity_ballvelocity_ephys_timestamp_index ON ballvelocity(ballvelocity_ephys_timestamp);")

            # event table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event (
                    event_id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    trial_id BIGINT NOT NULL,
                    event_name VARCHAR(255) NOT NULL,
                    event_package_id INT NOT NULL,
                    event_portenta_timestamp BIGINT NOT NULL,
                    event_pc_timeStamp BIGINT NOT NULL,
                    event_value INT NOT NULL,
                    event_ephys_timestamp BIGINT,
                    FOREIGN KEY (session_id) REFERENCES session(session_id)
                );
            """)
            cursor.execute("CREATE INDEX event_session_id_index ON event(session_id);")
            cursor.execute("CREATE INDEX event_trial_id_index ON event(trial_id);")
            cursor.execute("CREATE INDEX event_event_ephys_timestamp_index ON event(event_ephys_timestamp);")

            # unity_frame table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unity_frame (
                    unity_frame_id INT AUTO_INCREMENT PRIMARY KEY,
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
                    frame_ephys_timestamp BIGINT,
                    FOREIGN KEY (session_id) REFERENCES session(session_id)
                );
            """)
            cursor.execute("CREATE INDEX unity_frame_session_id_index ON unity_frame(session_id);")
            cursor.execute("CREATE INDEX unity_frame_trial_id_index ON unity_frame(trial_id);")
            cursor.execute("CREATE INDEX unity_frame_frame_id_index ON unity_frame(frame_id);")
            cursor.execute("CREATE INDEX unity_frame_ballvelocity_first_package_index ON unity_frame(ballvelocity_first_package);")
            cursor.execute("CREATE INDEX unity_frame_ballvelocity_last_package_index ON unity_frame(ballvelocity_last_package);")

            # unity_trial table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unity_trial (
                    unity_trial_id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    trial_id INT NOT NULL,
                    trial_start_pc_timestamp BIGINT NOT NULL,
                    trial_start_frame BIGINT NOT NULL,
                    trial_end_pc_timestamp BIGINT NOT NULL,
                    trial_end_frame BIGINT NOT NULL,
                    trial_pc_duration BIGINT NOT NULL,
                    trial_outcome INT NOT NULL,
                    trial_start_ephys_timestamp BIGINT,
                    trial_end_ephys_timestamp BIGINT,
                    FOREIGN KEY (session_id) REFERENCES session(session_id)
                );
            """)
            cursor.execute("CREATE INDEX unity_trial_session_id_index ON unity_trial(session_id);")
            cursor.execute("CREATE INDEX unity_trial_trial_id_index ON unity_trial(trial_id);")
            cursor.execute("CREATE INDEX unity_trial_trial_start_frame_index ON unity_trial(trial_start_frame);")
            cursor.execute("CREATE INDEX unity_trial_trial_end_frame_index ON unity_trial(trial_end_frame);")

            # face_cam table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facecam (
                    facecam_id INT AUTO_INCREMENT PRIMARY KEY,
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
                CREATE TABLE IF NOT EXISTS bodycam (
                    bodycam_id INT AUTO_INCREMENT PRIMARY KEY,
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
                CREATE TABLE IF NOT EXISTS unitycam (
                    unitycam_id INT AUTO_INCREMENT PRIMARY KEY,
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
                CREATE TABLE IF NOT EXISTS paradigm_P0200 (
                    paradigm_P0200_id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    trial_id BIGINT NOT NULL,
                    pillar_distance DOUBLE NOT NULL,
                    pillar_angle DOUBLE NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES session(session_id)
                );
            """)
            cursor.execute("CREATE INDEX paradigm_p0200_session_id_index ON paradigm_P0200(session_id);")
            cursor.execute("CREATE INDEX paradigm_p0200_trial_id_index ON paradigm_P0200(trial_id);")

            # paradigm_P0300 table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paradigm_P0300 (
                    paradigm_P0300_id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    trial_id BIGINT NOT NULL,
                    maximum_reward_number INT NOT NULL,
                    reward_number DOUBLE NULL,
                    FOREIGN KEY (session_id) REFERENCES session(session_id)
                );
            """)
            cursor.execute("CREATE INDEX paradigm_p0300_session_id_index ON paradigm_P0300(session_id);")
            cursor.execute("CREATE INDEX paradigm_p0300_trial_id_index ON paradigm_P0300(trial_id);")

            # paradigm_P0400 table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paradigm_P0400 (
                    paradigm_P0400_id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    trial_id BIGINT NOT NULL,
                    maximum_reward_number INT NOT NULL,
                    reward_number DOUBLE NULL,
                    FOREIGN KEY (session_id) REFERENCES session(session_id)
                );
            """)
            cursor.execute("CREATE INDEX paradigm_p0400_session_id_index ON paradigm_P0400(session_id);")
            cursor.execute("CREATE INDEX paradigm_p0400_trial_id_index ON paradigm_P0400(trial_id);")

            # Commit changes and close the connection
            conn.commit()
            print("Tables created successfully.")
        else:
            print('Failed to connect to MySQL server')

    except Error as e:
        print(e)

    finally:
        # Close connection
        if conn.is_connected():
            cursor.close()
            conn.close()
            print('MySQL connection closed')

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Create rat VR behavior database.")
    argParser.add_argument("--db_name", type=str, default="rat_vr", help="Name of the MySQL database to create.")

    db_fname = argParser.parse_args().db_name
    test_db_fname = db_fname + "_pre"
    
    # Create the real database
    create_ratvr_db(db_fname)

    create_ratvr_db(test_db_fname)
   
