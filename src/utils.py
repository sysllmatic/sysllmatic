import copy
import logging
import os
import sys
from tqdm import tqdm
from datetime import datetime
import os

class ColoredConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        # Need to make a actual copy of the record
        # to prevent altering the message for other loggers
        myrecord = copy.copy(record)
        levelno = myrecord.levelno
        if(levelno >= 50):  # CRITICAL / FATAL
            color = '\x1b[31m'  # red
        elif(levelno >= 40):  # ERROR
            color = '\x1b[31m'  # red
        elif(levelno >= 30):  # WARNING
            color = '\x1b[33m'  # yellow
        elif(levelno >= 20):  # INFO
            color = '\x1b[36m'  # cyan
        elif(levelno >= 15):  # DEBUG
            color = '\x1b[35m'  # pink
        elif(levelno == 10):  # notification
            color = '\x1b[32m'  # green
        else:  # NOTSET and anything else
            color = '\x1b[0m'  # normal
        myrecord.msg = color + str(myrecord.msg) + '\x1b[0m'  # normal
        logging.StreamHandler.emit(self, myrecord)

class Logger:
    _instance = None

    def __new__(cls, directory, filename):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance.run_start_time = datetime.now()
            cls._instance.logger = cls._instance.setup_logging(directory, filename)
        return cls._instance

    def attach_datetime(self, string):
        return string + self.run_start_time.strftime(f"_%d-%m-%H-%M")

    def setup_logger(self, log_file_path):
        formatter = logging.Formatter(
            '%(asctime)s : %(levelname)s : %(message)s',
            datefmt='%m/%d/%y %I:%M:%S %p'
        )

        file_handler = logging.FileHandler(
            log_file_path,
            mode='w'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        def write(self, x):
            if len(x.rstrip()) > 0:
                tqdm.write(x, file=self.file)
        out_stream = type("TqdmStream", (), {'file': sys.stdout, 'write':write})()

        stdout_handler = ColoredConsoleHandler(out_stream)
        stdout_handler.setFormatter(formatter)
        stdout_handler.setLevel(logging.INFO)

        logger = logging.getLogger()
        logger.addHandler(file_handler)
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.INFO)

        return logger

    def setup_logging(self, directory, filename):
        log_dir = os.path.join(directory, filename)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = os.path.join(log_dir, self.attach_datetime('run') + '.log')
        return self.setup_logger(log_file_path)