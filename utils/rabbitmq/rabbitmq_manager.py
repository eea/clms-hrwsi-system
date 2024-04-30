#!/usr/bin/env python3
"""
RabbitmqManager module is used to store the RabbitMQ information.
"""
import os
import sys
import logging
from kombu import Exchange, Queue

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from utils.logger import LogUtil
from HRWSI_System.harvester.apimanager.api_manager import ApiManager

class RabbitmqManager():
    """Connect to RabbitMQ queue"""

    LOGGER_LEVEL = logging.INFO

    def __init__(self, rpc_mode: bool = False) -> None:

        self.rpc_mode = rpc_mode

        # Load config file
        config_data = ApiManager.read_config_file()

        self.rabbit_url = config_data["rabbitmq"]["url"]
        self.heartbeat = config_data["rabbitmq"]["heartbeat"]

        # Create exchange
        exchange_name = "rpc_" + config_data["rabbitmq"]["exchange_name"] if self.rpc_mode else config_data["rabbitmq"]["exchange_name"]
        exchange_type = config_data["rabbitmq"]["exchange_type"]
        self.exchange = Exchange(exchange_name, type=exchange_type)

        # Create queue
        queue_name = "rpc_" + config_data["rabbitmq"]["queue_name"] if self.rpc_mode else config_data["rabbitmq"]["queue_name"]
        time_to_live_in_queue = config_data["rabbitmq"]["seconds_to_live_in_queue"]
        self.routine_key = config_data["rabbitmq"]["routine_key"]
        self.queue = Queue(name=queue_name, exchange=self.exchange, routing_key=self.routine_key, message_ttl=time_to_live_in_queue)

        self.logger = LogUtil.get_logger('Log_rabbitmq', self.LOGGER_LEVEL, "log_rabbitmq/logs.log")

    def run(self) -> None:
        """Create and run a RabbitMQ object"""

        raise NotImplementedError

if __name__ == "__main__":

    rabbitmq = RabbitmqManager(rpc_mode=True)
    rabbitmq.run()
