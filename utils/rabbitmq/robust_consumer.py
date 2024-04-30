#!/usr/bin/env python3
"""
RobustConsumer module is used to consume messages in message queue.
"""
import os
import sys
import json
import logging
import functools
import kombu.transport.pyamqp
from kombu.mixins import ConsumerMixin

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from utils.logger import LogUtil

class RobustConsumer(ConsumerMixin):
    """Robust consumer quickly recovers when the connection to RabbitMQ is disrupted or dies completely"""

    LOGGER_LEVEL = logging.INFO

    def __init__(self, connection: kombu.connection.Connection,
                 queues: list[kombu.entity.Queue]):

        self.connection = connection
        self.queues = queues
        self.logger = LogUtil.get_logger('Log_robustconsumer', self.LOGGER_LEVEL, "log_robustconsumer/logs.log")

    def get_consumers(self, Consumer: functools.partial, channel: kombu.transport.pyamqp.Channel) -> list[kombu.messaging.Consumer]:
        """Returns a list of the Consumers the worker will use"""

        return [Consumer(queues=self.queues,
                         callbacks=[self.on_message])]

    def on_message(self, body: str, message: kombu.transport.pyamqp.Message) -> None:
        """Function that will get called when a Consumer receives a message."""

        # Convert JSON into dict
        json_data = json.loads(body)
        self.logger.info('Got message: %s', json_data)

        # TODO add data in database (change processing status and processing tasks has ended)
        # verify that data not already in database
        message.ack() # lets the RabbitMQ server know we have dealt with the message
