import os
import sqlite3
import pandas as pd
from add_utils import dict_to_db


def add_paradigm(db_name, paradigm_dict):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    paradigm_name = paradigm_dict['paradigm_name']
    cursor.execute("SELECT * from paradigm WHERE paradigm_name=?", (paradigm_name,))
    if len(cursor.fetchall()) == 0:
        dict_to_db(cursor, paradigm_dict, 'paradigm')
    else:
        raise ValueError(f"Paradigm {paradigm_name} already exists in the paradigm table.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":

    paradigm_dict = {
        'paradigm_name': 'P0200_GoalDirectedMovement',
        # 'paradigm_name': 'P0000_AutoLickReward',
        # 'paradigm_name': 'P0100_SpoutAssoc',
        # 'paradigm_description': ''
    }


    add_paradigm("/home/vrmaster/projects/ratvr/VirtualReality/data/rat_vr.db", paradigm_dict)
    add_paradigm("/home/vrmaster/projects/ratvr/VirtualReality/data/rat_vr_test.db", paradigm_dict)
    print("Paradigm added successfully.")
