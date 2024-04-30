#!/usr/bin/env python3
"""
RabbitmqProducer module is used in worker to send information to RabbitMQ queue after process data.
"""
import os
import sys
import json
import kombu.transport.pyamqp
from kombu import Connection, Producer, Consumer, Queue, uuid

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from utils.rabbitmq.rabbitmq_manager import RabbitmqManager
from HRWSI_System.harvester.apimanager.api_manager import ApiManager

class RabbitmqProducer(RabbitmqManager):
    """Send data to RabbitMQ"""

    def __init__(self, json_file: str = None,
                 rpc_mode: bool = False) -> None:

        super().__init__(rpc_mode)
        self.json_file = json_file
        self.correlation_id = uuid()

        # Load config file
        config_data = ApiManager.read_config_file()
        self.interval_start = config_data["rabbitmq"]["retry_policy"]["interval_start"]
        self.interval_step = config_data["rabbitmq"]["retry_policy"]["interval_step"]
        self.interval_max = config_data["rabbitmq"]["retry_policy"]["interval_max"]
        self.max_retries = config_data["rabbitmq"]["retry_policy"]["max_retries"]

    def run(self) -> None:
        """Create and run a producer"""

        # Connect to RabbitMQ server
        conn = Connection(self.rabbit_url, heartbeat=self.heartbeat)
        channel = conn.channel()

        if self.rpc_mode:
            reply_queue = Queue(name="amq.rabbitmq.reply-to")

            with Consumer(conn, reply_queue, callbacks=[self.process_message], no_ack=True): # No-ack mode
                producer = Producer(exchange=self.exchange, channel=conn, routing_key=self.routine_key)
                properties = {
                    "reply_to": reply_queue.name,
                    "correlation_id": self.correlation_id,
                    "retry": True, # Set the retry policy
                    "retry_policy": {
                        'interval_start': self.interval_start, # First retry after 10s,
                        'interval_step': self.interval_step,  # then increase by 10s for every retry.
                        'interval_max': self.interval_max,  # but don't exceed 30s between retries.
                        'max_retries': self.max_retries,   # give up after 30 tries.
                    }
                }

                producer.publish(self.json_file, **properties)
                conn.drain_events()

        else:
            # Create Producer
            producer = Producer(exchange=self.exchange, channel=channel, routing_key=self.routine_key)

            # Send json
            producer.publish(self.json_file, retry=True, exchange=self.exchange,
                            routing_key=self.routine_key, declare=[self.queue],
                            retry_policy={
                                'interval_start': self.interval_start, # First retry after 10s,
                                'interval_step': self.interval_step,  # then increase by 10s for every retry.
                                'interval_max': self.interval_max,  # but don't exceed 30s between retries.
                                'max_retries': self.max_retries,   # give up after 30 tries.
                            })

    def process_message(self, body: str, message: kombu.transport.pyamqp.Message) -> None:
        "Process the message received by consumer in RPC mode"

        if message.properties['correlation_id'] == self.correlation_id:
            self.logger.info("Response: %s", body)
            message.ack()

if __name__ == "__main__":

    # Json example
    x = {
        "name": "Blake",
        "age": 30,
        "city": "New York"
        }
    y = json.dumps(x)

    rabbitmqproducer = RabbitmqProducer(json_file=y, rpc_mode=True)
    rabbitmqproducer.run()
