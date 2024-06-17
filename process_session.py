import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], 'db', 'db_writing'))

import argparse

from CustomLogger import CustomLogger as Logger
from session2DB import session2DB

def process_session():
    #-S-
    # other things will go here
    # -S-
    session_dir = '/home/ntgroup/Project/DBRatVR/SQLite/TestData/2024-06-04_12-06-04_goodone_Tuesday_1'
    session2DB(session_dir)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Validate and add a finished session to DB")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    kwargs = vars(argParser.parse_args())
    
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    L.logger.debug(L.fmtmsg(kwargs))
            
    process_session(**kwargs)
    