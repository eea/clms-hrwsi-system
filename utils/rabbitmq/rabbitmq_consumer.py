#!/usr/bin/env python3
"""
RabbitmqConsumer module is used to create the consumer of the RabbitMQ.
"""
import os
import sys
from kombu import Connection

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from utils.rabbitmq.robust_consumer import RobustConsumer
from utils.rabbitmq.rabbitmq_manager import RabbitmqManager
from utils.rabbitmq.robust_rpc_consumer import RobustRPCConsumer

class RabbitmqConsumer(RabbitmqManager):
    """Read data to RabbitMQ"""

    def run(self) -> None:
        """Create and run a consumer"""

        # Connect to RabbitMQ server
        conn = Connection(self.rabbit_url, heartbeat=self.heartbeat)

        # Queue declaration
        self.queue.maybe_bind(conn)
        self.queue.declare()

        # Create Consumer
        queues = [self.queue]
        consumer = RobustRPCConsumer(conn, queues) if self.rpc_mode else RobustConsumer(conn, queues)
        consumer.run() # The run function loops continuously until an error occurs or the process is terminated


if __name__ == "__main__":

    rabbitmqconsumer = RabbitmqConsumer(rpc_mode=True)
    rabbitmqconsumer.run()
