#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging

from common.log_util import LogUtil

def get_logger(log_file_path=None, verbose_level=1):
    """Return a Python logger, depending on the environment.

    Args:
        log_file_path (str, optional): Log file path. If None: do not write a log file. Defaults to None.
        verbose_level (int, optional): Verbose level. Defaults to 1.

    Returns:
        logger: logger created
    """
        
    log_level = None
    assert isinstance(verbose_level, int), 'verbose_level must be an integer'
    if verbose_level == 0:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    # Create and return logger
    return LogUtil.get_logger(
        log_name='wsi',
        log_level=log_level,
        log_file_path=log_file_path)
