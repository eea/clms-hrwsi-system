#!/usr/bin/env python3
"""Logging utilities"""
import logging
import sys
import os

root_path = os.path.realpath(__file__).split("orchestrator", maxsplit=1)[0]
sys.path.append(root_path)

from utils.file import FileUtil

class LogUtil(object):
    '''Utility functions to manage log messages.'''

    # Logging parameters
    FORMAT = '[%(levelname)s] [%(name)s] %(asctime)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    @staticmethod
    def add_file_handler(logger:logging, log_file_path:str):
        '''
        Add file handler to already existing logger.


        Parameters
        ----------
        logger : logging
            Already existing logging instance.
        log_file_path : str
            File path where to write the logs. The file-tree will be created if required.

        Returns
        -------
        logging
            A logger with a set-up file handler.
        '''

        # Create formatter
        formatter = logging.Formatter(LogUtil.FORMAT)
        formatter.datefmt = LogUtil.DATE_FORMAT

        # Create the file directory
        FileUtil.create_file_path(log_file_path,overwrite=True, error_on_already_existing=False)

        # Create file handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    @staticmethod
    def get_logger(log_name:str, log_level:int=logging.WARNING, log_file_path:str=None):
        '''
        Create and return a logging instacne.

        The logger instance is parametrized to fit the project and class-related standards.

        Parameters
        ----------
        log_name : str
            The name of the logged class
        log_level : int, optional
            The minimal logged level; either logging.CRITICAL, ERROR, WARNING, INFO, or DEBUG, by default logging.WARNING
        log_file_path : str, optional
            If set, will create the file-tree and the files to store the logs, by default None

        Returns
        -------
        _type_
            _description_
        '''

        # Create logger with name
        logger = logging.getLogger(log_name)

        # Remove previously defined handlers, if any
        logger.handlers = []

        # Set minimum log level
        if log_level:
            logger.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(LogUtil.FORMAT)
        formatter.datefmt = LogUtil.DATE_FORMAT

        # DEBUG and INFO go to stdout
        class InfoFilter(logging.Filter):
            def filter(self, rec):
                return rec.levelno in (logging.DEBUG, logging.INFO)
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.addFilter(InfoFilter())
        logger.addHandler(stdout_handler)

        # WARNING and above go to stderr
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)
        stderr_handler.setLevel(logging.WARNING)
        logger.addHandler(stderr_handler)

        if log_file_path:
            LogUtil.add_file_handler(logger, log_file_path)

        return logger

# Temp logger used when no other logger is available
temp_logger = LogUtil.get_logger('temp', log_level=logging.INFO)

if __name__ == '__main__':
    temp_logger.info('Initialized temp_logger')
    log_util_logger = LogUtil.get_logger('Log_util', logging.DEBUG, "log_test/logs.log")
    
    temp_logger.info('Logging examples')
    log_util_logger.debug('Debuging log')
    log_util_logger.info('Info log')
    log_util_logger.warning('Warning log')
    log_util_logger.error('Error log')
    log_util_logger.critical('Critical log')