#!/usr/bin/env python3
"""
Api_manager module is used to summarize the processing condition
"""
import os
import sys
import logging
import yaml
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from utils.logger import LogUtil

class ApiManager():
    """Define the conditions of a request"""

    LOGGER_LEVEL = logging.DEBUG

    def __init__(self, processing_condition_name: str,
                 max_day_since_publication_date: int,
                 max_day_since_measurement_date: int = None):

        self.processing_condition_name = processing_condition_name
        self.max_day_since_measurement_date = max_day_since_measurement_date
        self.max_day_since_publication_date = max_day_since_publication_date
        self.logger = LogUtil.get_logger('Log_api_manager', self.LOGGER_LEVEL, "log_api_manager/logs.log")


    def get_candidate_inputs(self) -> tuple[tuple]:
        """Send a request to collect candidate inputs"""
        raise NotImplementedError

    @staticmethod
    def read_config_file() -> dict:
        """Read the yaml config  file and return file data"""

        with open('HRWSI_System/harvester/apimanager/config.yaml', 'r', encoding="utf-8") as config_file:
            file_data = yaml.safe_load(config_file)

        return file_data
