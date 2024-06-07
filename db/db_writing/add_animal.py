import sys
import os
# when executed as a process add parent paroject to path again, needed for logger
sys.path.insert(1, os.path.join(sys.path[0], '..', '..')) # project dir

import sqlite3
from add_utils import dict_to_db

from CustomLogger import CustomLogger as Logger

def add_animal(db_name, animal_dict):
    # -S-
    # I added some basic logging to give you an idea how it should be used,
    # feel free to adjust the details
    # -S-
    L = Logger()
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    animal_name = animal_dict['animal_name']
    cursor.execute("SELECT * from animal WHERE animal_name=?", (animal_name,))
    L.logger.debug(f"Querying animal table, found ..")
    if len(cursor.fetchall()) == 0:
        dict_to_db(cursor, animal_dict, 'animal')
    else:
        L.logger.error(f"Error: Animal {animal_name} already exists in the animal table.")
        raise ValueError(f"Animal {animal_name} already exists in the animal table.")
    
    conn.commit()
    conn.close()


    # -S-
    # I am not quite sure if should have this as an indepdendent process. So far,
    # sub-processess are always explicitily called by the user - they are are being 
    # used if we expect signicant overhead and potential concurrency limitations 
    # To stay within the current design, the proc would be called by the user.
    #
    # You mentioned concerns about typo's which is valid. But i think the easier 
    # way around this is how it's currently handled: In the UI there is a dropdown
    # of options that are hard coded for animals (in Core) or defined by the excel
    # file names for paradigms. This way, the user can't make a typo. Perhaps I
    # don't rmember fully, but I also don't recall hoe this multi-proc approach 
    # prevents this typo issue.
    #
    # One issue for example is related to logging. Each proc has it's own file,
    # and ideally we would like to have a single log file for db wring & validation
    #
    # I think functionality (here db writing & validation) should be encapsulated
    # in a single process if possible (no need for concurrency)
    #
    # -S-


if __name__ == "__main__":

    animal_dict = {
        'animal_name': 'rYL_001',
        'animal_gender': 'f',
        # 'animal_description': ''
    }
    
    # -S-
    # database filename should be a global attribute shared accross the module
    # eaiser to implement if this isn't a subproc but a function actually, 
    # just pass as argument
    # -S-
    add_animal("rat_vr.db", animal_dict)
    add_animal("rat_vr_test.db", animal_dict)
    print("Animal added successfully.")
