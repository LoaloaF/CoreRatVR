import os
import sqlite3
import pandas as pd
from add_utils import dict_to_db

def add_animal(db_name, animal_dict):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    animal_name = animal_dict['animal_name']
    cursor.execute("SELECT * from animal WHERE animal_name=?", (animal_name,))
    if len(cursor.fetchall()) == 0:
        dict_to_db(cursor, animal_dict, 'animal')
    else:
        raise ValueError(f"Animal {animal_name} already exists in the animal table.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":

    animal_dict = {
        'animal_name': 'rYL_001',
        'animal_gender': 'f',
        # 'animal_description': ''
    }

    add_animal("rat_vr.db", animal_dict)
    add_animal("rat_vr_test.db", animal_dict)
    print("Animal added successfully.")
