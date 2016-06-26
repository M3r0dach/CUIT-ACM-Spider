import logging
from settings import log_dir, log_level


class Logger:
    def __init__(self, logger_name, level, pathname):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)
        logging.basicConfig()

        # create a file handler
        file_handler = logging.FileHandler(pathname)
        file_handler.setLevel(level)

        # create a stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)

        # create a logging format
        formatter = logging.Formatter(
            '[%(asctime)s] %(filename)s/%(funcname)s'
            ' - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)

    def get_logger(self):
        return self.logger


logger = Logger('app', log_level, log_dir).get_logger()


