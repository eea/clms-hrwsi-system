#!/usr/bin/env python3
"""
RobustConsumer module is used to consume message in message queue.
"""
import os
import sys
import json
import datetime
import logging
import functools
import psycopg2
import kombu.transport.pyamqp
from kombu.mixins import ConsumerProducerMixin

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from utils.logger import LogUtil
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager

class RobustRPCConsumer(ConsumerProducerMixin):
    """Robust consumer quickly recovers when the connection to RabbitMQ is disrupted or dies completely"""

    LOGGER_LEVEL = logging.INFO
    INSERT_PROCESSING_STATUS_WORKFLOW = "INSERT INTO hrwsi.processing_status_workflow (nomad_job_dispatch_fk_id, processing_status_id, date) VALUES (%s, %s, %s);"
    INSERT_PRODUCT = "INSERT INTO hrwsi.products (input_fk_id, product_type_id, product_path, creation_date, catalogued_date) VALUES (%s, %s, %s, %s, %s);"

    def __init__(self, connection: kombu.connection.Connection,
                 queues: list[kombu.entity.Queue]):

        self.connection = connection
        self.queues = queues
        self.logger = LogUtil.get_logger('Log_robustrpcconsumer', self.LOGGER_LEVEL, "log_robustrpcconsumer/logs.log")

    def get_consumers(self, Consumer: functools.partial, channel: kombu.transport.pyamqp.Channel) -> list[kombu.messaging.Consumer]:
        """Returns a list of the Consumers the worker will use"""

        return [Consumer(queues=self.queues,
                         callbacks=[self.on_message])]

    def on_message(self, body: str, message: kombu.transport.pyamqp.Message) -> None:
        """Function that will get called when a Consumer receives a message."""

        # Convert JSON into dict
        json_data = json.loads(body)
        self.logger.info('Got message: %s', json_data)

        # Connect to Database
        conn, cur = HRWSIDatabaseApiManager.connect_to_database()

        # Convert cur in a dict
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        # Check if the message has already been processed
        pt_id = json_data["processing_task_id"]
        check_processing_task_ended = f"SELECT pt.has_ended FROM hrwsi.processing_tasks pt WHERE id = {pt_id};"
        cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, check_processing_task_ended)
        conn.commit()
        for result in cur :
            task_has_ended = result["has_ended"]

        if task_has_ended:
            self.logger.info("Message has already been processed")
        else:
            # Update processing task has_ended to true
            update_processing_task = f"UPDATE hrwsi.processing_tasks SET has_ended = true WHERE id = {pt_id};"
            cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, update_processing_task)
            conn.commit()

            # Insert processing status workflow processed (2)
            now = datetime.datetime.now()
            processing_status_workflow = tuple((int(json_data["nomad_job_id"]),2, now),)
            cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.INSERT_PROCESSING_STATUS_WORKFLOW, (processing_status_workflow,))
            conn.commit()

            # Create and insert product
            input_id = json_data["input_id"]
            product_type_id = json_data["product_type_id"]
            product_path = json_data["product_path"]
            product_tuple = tuple((int(input_id),product_type_id, product_path, now, now),)
            # TODO add kpi_file
            cur = HRWSIDatabaseApiManager.execute_request_in_database(cur, self.INSERT_PRODUCT, (product_tuple,))
            conn.commit()

        self.logger.info("End of process")

        # Send response
        self.producer.publish(
            'Received',
            exchange='',
            routing_key=message.properties['reply_to'],
            correlation_id=message.properties['correlation_id']
        )

        message.ack() # lets the RabbitMQ server know we have dealt with the message
