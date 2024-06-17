import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], 'db', 'db_writing'))

import argparse
import shutil

from CustomLogger import CustomLogger as Logger
from session2DB import session2DB

def process_session(session_dir):
    
    L = Logger()
    L.logger.info(f"Processing session {session_dir}")
    #-S-
    # other things will go here
    # -S-
    # session_dir = '/home/ntgroup/Project/DBRatVR/SQLite/TestData/2024-06-04_12-06-04_goodone_Tuesday_1'
    # session2DB(session_dir)
    
    # renamce sesion dir to session_dir but without ending on active
    
    # S
    # 1. check which files exists
    # 2. critical warnings and erros in logs?
    
    #H
    # 2.1 check hdf5 files, rename keys,
    # 3. merge hdf5s into one, meatadata everything in there, potentially even proc log files
    # 4. get ephys TLLs timestamps and integrate into merged hdf5 
    # needs intesive checking - bc this is super important
    # 4. add to db, add paradigm, addainmal check
    # last one: move data to NAS
    
    
    
    
    shutil.move(session_dir, session_dir[:-7])
    
    L.logger.info(f"Processing session {session_dir}")
    

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Validate and add a finished session to DB")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--session_dir")
    kwargs = vars(argParser.parse_args())
    
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    L.logger.debug(L.fmtmsg(kwargs))
            
    process_session(**kwargs)
    