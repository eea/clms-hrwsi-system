# Message Queuing

To communicate between the different workers and the database, the system use a message queue in order to be able to manage the data flow from the workers.

Message Queuing allows applications to communicate by sending messages to each other. The Message Queue provides temporary message storage when the destination program is busy or not connected.

**RabbitMQ** is used in order to implement the message queue.

**RabbitMQ** is an open source messaging software that allows you to read messages from and write messages to queues using the Advance Message Queuing Protocol (AMQP). The functioning of RabbitMQ is that an application sends a message to a RabbitMQ server and the server routes that message to a queue. Then, another application listening to that queue receives that message and does whatever it needs to with it. The routing of the messages is done by the exchanges in a RabbitMQ server. Exchanges take a message and route it into zero or more queues. So a producer will tell the server which exchange it wants to use, and the exchange figures out which queue to push message to.

To use it with Python, a library that implements the *AMQP* (Advanced Message Queuing Protocol) is needed. The library chosen is **Kombu**.

**Kombu** is a messaging library for Python. The aim of Kombu is to make messaging in Python as easy as possible by providing an idiomatic high-level interface for the AMQ protocol, and also providing proven and tested solutions to common messaging problems.

## Installation

To install RabbitMQ on Ubuntu, one needs to use apt repositories on a Cloudsmith mirror, that provide a modern version of Erlang. In the [official documentation webpage](https://www.rabbitmq.com/docs/install-debian), there is a script to install RabbitMQ. So, one just has to launch the script like that :

```batch
chmod +x rabbitmq.sh
./rabbitmq.sh
```

Once done, we can check the status of the Rabbit server :

```batch
systemctl status rabbitmq-server
```

We can stop, restart or kill the server with the systemctl command.

An other way to run RabbitMQ is to run the Docker image like that :

```batch
rabbitmq_version=3.13
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:${rabbitmq_version}-management
```

Regarding the Kombu library, the installation is done thanks to pip install :

```batch
kombu_version=5.3.5
pip install kombu==${kombu_version}
```

## Explanation RabbitMQ usage

We can find the UML of the RabbitMQ implementation [here](https://drive.google.com/file/d/1H8sbmAbj9oj8qhR5lwQG__lWGXWYz9qd/view?usp=sharing).

### How launch RabbitMQ ?

After the installation of the RabbitMQ server thanks to [rabbitmq.sh](rabbitmq.sh) script, one launch the consumer ([rabbitmq_consumer.py](rabbitmq_consumer.py)) with the proper configuration (set up in [config.yaml](/home/andusa/hrwsi_watqual_sys/HRWSI_System/harvester/apimanager/config.yaml)).
Then, he can launch the producer ([rabbitmq_producer.py](rabbitmq_producer.py)).
RabbitMQ communication is generally via port 5672, so producers and consumers must be able to communicate via this port.
Producers and consumers can be launched on any machine, since it's the server, and above the exchange, that takes care of routing the message correctly.

### Remote Procedure Call (RPC)

We used RabbitMQ like a RCP (*Remote procedure Call*). A RPC is when a client makes request to a network server and receives a reply containing the results of the procedure's execution.

In our context, a worker sends a JSON with all the usefull information about the product like the task execution status or even the indexation JSON.
The consumer, who can interact with the database, reads and writes the data in Database and then sends a response to the worker to inform that its message has been processed.

### RabbitMQ in a cluster

To use RabbitMQ in a cluster, one has to change the connection URL. In local the URL looks like : **amqp://localhost:5672/**. But in cluster, for distinct machine access to the server, one has to change localhost with server IP.

Nevertheless, RabbitMQ is created with *guest* user and he can only connect from localhost.

So, one has to create an other user, with a password :

```batch
sudo rabbitmqctl add_user '${username}' '${password}'
```

Then, create a virtual hosts, because when a client connects to RabbitMQ, it specifies a virtual host (vhost) name to connect to :

```batch
sudo rabbitmqctl add_vhost ${vhost_name}
```

Next, one has to grant permission to a user :

```batch
sudo rabbitmqctl set_permissions -p "${vhost_name}" "${username}" ".*" ".*" ".*"
```

The first **".*"** is for configure permission on every entity, second one for write permission on every entity and last for read permission on every entity.

At the end, one just has to change the url following this template :

```batch
amqp://${username}:${password}@${server_ip}:5672/${vhost_name}
```

## Usefull command

* Display the queue list :

```batch
sudo rabbitmqctl list_queues
```

* Purge a queue :

```batch
sudo rabbitmqctl purge_queue ${name_queue}
```

* Delete a queue :

```batch
sudo rabbitmqctl delete_queue ${name_queue}
```
