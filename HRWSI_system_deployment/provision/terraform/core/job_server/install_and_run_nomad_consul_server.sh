#!/bin/bash

# Updates, general install
sudo apt-get update -y
sudo apt-get install -y wget unzip

# Versions of Nomad and Consul
NOMAD_VERSION=1.6.3
CONSUL_VERSION=1.17.0

# Install Nomad
wget https://releases.hashicorp.com/nomad/${NOMAD_VERSION}/nomad_${NOMAD_VERSION}_linux_amd64.zip
unzip nomad_${NOMAD_VERSION}_linux_amd64.zip
sudo mv nomad /usr/bin/

# Install Consul
wget https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip
unzip consul_${CONSUL_VERSION}_linux_amd64.zip
sudo mv consul /usr/bin/

# Clean Nomad and Consul archives
rm -rf *.zip

# Set up repositories that will be used by Nomad and Consul
sudo mkdir -p /home/eouser/data_nomad
sudo mkdir -p /home/eouser/data_consul

# Create Nomad server config file
cat <<CONF > /home/eouser/nomad_server.hcl
# Configuration file for Nomad Server

datacenter = "dc1"
data_dir  = "/home/eouser/data_nomad"

bind_addr = "0.0.0.0"

advertise {
  http = "{{ GetPrivateIP }}"
}


# Server configuration
server {
  enabled          = true
  bootstrap_expect = 1 # Number of expected servers in the datacenter
}

# Consul configuration
consul {
  address = "127.0.0.1:8500" # IP of local Consul Server
  client_service_name = "nomad-server"

  # Enables automatically registering the services
  auto_advertise = true

  # Enables automatically registering the server and client
  server_auto_join = true
  client_auto_join = true
}
CONF

# Create Consul server config file
cat <<CONF > /home/eouser/consul_server.hcl
# Configuration file for Consul Server

node_name = "consul-server" # 2 nodes cannot have the same name
datacenter = "dc1"
data_dir = "/home/eouser/data_consul"

server = true
bootstrap_expect = 1 # Number of expected servers in the datacenter

advertise_addr = "{{ GetPrivateIP }}" # VM IP
bind_addr = "0.0.0.0"
client_addr = "0.0.0.0"

# Usefull port to use Consul Connect
ports {
  grpc = 8502
}
# Enable Consul Connect
connect {
  enabled = true
}
# Enable access to Web UI 
ui_config {
  enabled = true
}
CONF

# Run Nomad and Consul agents as servers.
sudo nohup consul agent -config-file=/home/eouser/consul_server.hcl &
sudo nohup nomad agent -config=/home/eouser/nomad_server.hcl 2>&1 /home/eouser/log_nomad.txt &