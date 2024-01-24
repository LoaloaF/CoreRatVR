import os
import logging
import datetime
import json
from Parameters import Parameters

class CustomLogger:
    def __init__(self):
        """
        Initialize the logger with the given name and optional log file directory.

        Args:
        - name (str): The name of the logger.
        - write_to_directory (str, optional): The directory where log files will be written.
        """

        # Refer always to the same logger - only one exists per process
        self.logger = logging.getLogger("__main__")
        
    def init_logger(self, logging_fname, logging_dir, logging_level,
                    create_run_sub_dir=False):
        P = Parameters()

        ll = logging_level if logging_level is not None else P.LOGGING_LEVEL
        self.logger.setLevel(ll)

        # setup logging to console
        console_hdlr = self._create_console_logger()
        self.logger.addHandler(console_hdlr)

        # ensusre filenames/ paths exist
        logging_dir = logging_dir if logging_dir is not None else P.LOGGING_DIRECTORY_RUN
        logging_fname = logging_fname if logging_fname is not None else "default"
        if create_run_sub_dir:
            # the first logger from the main script creates a sub dir
            logging_dir = self._create_sub_log_dir(logging_dir)
        
        # setup logging to file
        file_hdlr = self._create_logfile_handler(logging_fname, logging_dir)
        self.logger.addHandler(file_hdlr)
        
        if create_run_sub_dir:
            return logging_dir

    def _create_formatter(self, fmt):
        return logging.Formatter(fmt)
    
    def _create_console_logger(self):
        """
        Set up console logging with the default formatter.
        """
        P = Parameters()
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._create_formatter(P.CONSOLE_LOGGING_FMT))
        return console_handler
    
    def _create_sub_log_dir(self, logging_dir):
        tstamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging_sub_dir = os.path.join(logging_dir, tstamp)
        os.makedirs(logging_sub_dir)
        return logging_sub_dir

    def _create_logfile_handler(self, logging_fname, write_to_directory):
        """
        Set up file-based logging with the default file formatter.

        Args:
        - write_to_directory (str): The directory where log files will be written.
        """
        try:
            P = Parameters()
            log_fullfname = os.path.join(write_to_directory, f"{logging_fname}.log")
            
            file_handler = logging.FileHandler(log_fullfname)
            file_handler.setFormatter(self._create_formatter(P.FILE_LOGGING_FMT))
            return file_handler
        
        except FileNotFoundError as e:
            print(f"{e} Won't log to file.")

    def _switch_spacer_fmt(self):
        """
        Toggle between default formatter and spacer formatter for all handlers.
        """
        P = Parameters()

        is_default = self.logger.handlers[0].formatter._fmt == P.CONSOLE_LOGGING_FMT
        if is_default:
            spacer_fmtr = self._create_formatter(P.SPACER_LOGGING_FMT)
            [han.setFormatter(spacer_fmtr) for han in self.logger.handlers]
        else:
            fmts = P.CONSOLE_LOGGING_FMT, P.FILE_LOGGING_FMT
            [han.setFormatter(self._create_formatter(fmt)) 
             for han, fmt in zip(self.logger.handlers, fmts)]

    # def extend_fmt(self, exten):
    #     P = Parameters()
    #     console_fmt = P.CONSOLE_LOGGING_FMT + exten + P.LOGGING_FMT_MSG
    #     self._default_console_fmtr = self._create_formatter(console_fmt)
    #     self._console_hdlr.setFormatter(self._default_console_fmtr)

    #     file_fmt = P.CONSOLE_LOGGING_FMT + exten + P.LOGGING_FMT_MSG
    #     self._default_file_fmtr = self._create_formatter(file_fmt)
    #     self._file_hdlr.setFormatter(self._default_file_fmtr)

    def spacer(self):
        """
        Insert a separator line in the log to visually separate log entries.
        """
        self._switch_spacer_fmt()
        self.logger.critical('')  # log a separator line
        self._switch_spacer_fmt()

    def fmtmsg(self, msg):
        if isinstance(msg, (list, tuple)):
            msg = [json.dumps(m, indent=2) if isinstance(m, dict) else str(m) 
                   for m in msg]
            msg = ("\n\t".join(msg))
        else:
            msg = msg.replace("\n", "\n\t")
        return msg

if __name__ == "__main__":
    P = Parameters()
    Logger = CustomLogger()
    Logger.init_logger(__name__, "./", 10)
    Logger.spacer()
    Logger.logger.info('This is a regular log message.')
    Logger.spacer()
    Logger.logger.critical(['This is another regular ',"sdfsd"])