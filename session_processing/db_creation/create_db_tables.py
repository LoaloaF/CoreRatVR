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
            session_time DATE NOT NULL,
            session_path TEXT NOT NULL,
            paradigm_id INT NOT NULL,
            animal_id INT NOT NULL,
            animal_weight DOUBLE NOT NULL,
            start_time DATE,
            end_time DATE,
            duration DOUBLE,
            notes TEXT,
            FOREIGN KEY (animal_id) REFERENCES animal(animal_id)
            FOREIGN KEY (paradigm_id) REFERENCES paradigm(paradigm_id)
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
            on_wall_zone_entry TEXT,
            on_inter_trial_interval TEXT,
            inter_trial_interval_length SMALLINT,
            abort_inter_trial_interval_length SMALLINT,
            success_sequence_length SMALLINT,
            maxium_trial_length SMALLINT,
            trial_package_variables TEXT,
            trial_package_variables_default TEXT,
            session_description TEXT,
            pillars TEXT,
            pillar_details TEXT,
            env_x_size INT,
            env_y_size INT,
            base_length INT,
            wallzone_size INT,
            wallzone_collider_size INT,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)

    # ball_velocity table
    cursor.execute("""
        CREATE TABLE ball_velocity (
            ball_velocity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id INT NOT NULL,
            ball_velocity_package_id BIGINT NOT NULL,
            ball_velocity_t BIGINT NOT NULL,
            ball_velocity_timestamp BIGINT NOT NULL,
            ball_velocity_f INT NOT NULL,
            vr DOUBLE NOT NULL,
            vy DOUBLE NOT NULL,
            vp DOUBLE NOT NULL,
            ball_velocity_ttl BIGINT,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX ball_velocity_session_id_index ON ball_velocity(session_id);")
    cursor.execute("CREATE INDEX ball_velocity_trial_id_index ON ball_velocity(trial_id);")
    cursor.execute("CREATE INDEX ball_velocity_ball_velocity_ttl_index ON ball_velocity(ball_velocity_ttl);")

    # event table
    cursor.execute("""
        CREATE TABLE event (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id BIGINT NOT NULL,
            event_type TEXT NOT NULL,
            event_package_id INT NOT NULL,
            event_t BIGINT NOT NULL,
            event_timeStamp BIGINT NOT NULL,
            event_v int NOT NULL,
            event_f SMALLINT NOT NULL,
            event_ttl BIGINT,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX event_session_id_index ON event(session_id);")
    cursor.execute("CREATE INDEX event_trial_id_index ON event(trial_id);")
    cursor.execute("CREATE INDEX event_event_ttl_index ON event(event_ttl);")

    # unity_frame table
    cursor.execute("""
        CREATE TABLE unity_frame (
            unity_frame_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id INT NOT NULL,
            frame_id BIGINT NOT NULL,
            frame_timestamp BIGINT NOT NULL,
            x DOUBLE NOT NULL,
            z DOUBLE NOT NULL,
            a DOUBLE NOT NULL,
            s INT NOT NULL,
            fb INT NOT NULL,
            bfp DOUBLE NOT NULL,
            blp DOUBLE NOT NULL,
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
            trial_start_timestamp BIGINT NOT NULL,
            trial_start_frame BIGINT NOT NULL,
            trial_end_timestamp BIGINT NOT NULL,
            trial_end_frame BIGINT NOT NULL,
            trial_duration BIGINT NOT NULL,
            trial_outcome INT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX unity_trial_session_id_index ON unity_trial(session_id);")
    cursor.execute("CREATE INDEX unity_trial_trial_id_index ON unity_trial(trial_id);")
    cursor.execute("CREATE INDEX unity_trial_trial_start_frame_index ON unity_trial(trial_start_frame);")
    cursor.execute("CREATE INDEX unity_trial_trial_end_frame_index ON unity_trial(trial_end_frame);")


    # face_cam table
    cursor.execute("""
        CREATE TABLE face_cam (
            face_cam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id INT NOT NULL,
            face_cam_package_id BIGINT NOT NULL,
            face_cam_timestamp BIGINT NOT NULL,
            face_cam_ttl BIGINT,
            face_cam_data BLOB NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX face_cam_session_id_index ON face_cam(session_id);")
    cursor.execute("CREATE INDEX face_cam_trial_id_index ON face_cam(trial_id);")
    cursor.execute("CREATE INDEX face_cam_face_cam_ttl_index ON face_cam(face_cam_ttl);")

    # body_cam table
    cursor.execute("""
        CREATE TABLE body_cam (
            body_cam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id BIGINT NOT NULL,
            body_cam_package_id BIGINT NOT NULL,
            body_cam_timestamp BIGINT NOT NULL,
            body_cam_ttl BIGINT,
            body_cam_data BLOB NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX body_cam_session_id_index ON body_cam(session_id);")
    cursor.execute("CREATE INDEX body_cam_trial_id_index ON body_cam(trial_id);")
    cursor.execute("CREATE INDEX body_cam_body_cam_ttl_index ON body_cam(body_cam_ttl);")

    # unity_cam table
    cursor.execute("""
        CREATE TABLE unity_cam (
            unity_cam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id INT NOT NULL,
            unity_cam_package_id BIGINT NOT NULL,
            unity_cam_timestamp BIGINT NOT NULL,
            unity_cam_ttl BIGINT,
            unity_cam_data BLOB NOT NULL,
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
    """)
    cursor.execute("CREATE INDEX unity_cam_session_id_index ON unity_cam(session_id);")
    cursor.execute("CREATE INDEX unity_cam_trial_id_index ON unity_cam(trial_id);")
    cursor.execute("CREATE INDEX unity_cam_unity_cam_ttl_index ON unity_cam(unity_cam_ttl);")

    # paradigm_P0200 table
    cursor.execute("""
        CREATE TABLE paradigm_P0200 (
            paradigm_P0200_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            trial_id BIGINT NOT NULL,
            pd DOUBLE NOT NULL,
            pa DOUBLE NOT NULL,
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


if __name__ == "__main__":

    # if os.path.exists('smb://yaniklab-data.ee.ethz.ch/large/Simon/nas_vrdata/rat_vr.db'):
    #     raise ValueError("rat_vr.db already exists.")
    # else:
    #     create_ratvr_db('smb://yaniklab-data.ee.ethz.ch/large/Simon/nas_vrdata/rat_vr.db')
    #     print("rat_vr database created successfully.")
    
    # if os.path.exists('smb://yaniklab-data.ee.ethz.ch/large/Simon/nas_vrdata/rat_vr_test.db'):
    #     raise ValueError("rat_vr_test.db already exists.")
    # else:
    #     create_ratvr_db('smb://yaniklab-data.ee.ethz.ch/large/Simon/nas_vrdata/rat_vr_test.db')
    #     print("rat_vr_test database created successfully.")

    if os.path.exists('rat_vr.db'):
        raise ValueError("rat_vr.db already exists.")
    else:
        create_ratvr_db('rat_vr.db')
        print("rat_vr database created successfully.")

    if os.path.exists('rat_vr_test.db'):
        raise ValueError("rat_vr_test.db already exists.")
    else:
        create_ratvr_db('rat_vr_test.db')
        print("rat_vr_test database created successfully.")
   
