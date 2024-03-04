#!/bin/bash

# Updates, general install
sudo apt-get update -y
sudo apt-get install -y wget unzip

# Versions of Nomad and Consul
NOMAD_VERSION=1.6.3
CONSUL_VERSION=1.17.0
DOCKER_VERSION=24.0.5-0ubuntu1~22.04.1
CNIPLUGINS_VERSION=1.3.0

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

# Install docker for ulterior use when running nomad jobs
sudo apt-get install -y docker.io=${DOCKER_VERSION}

# Create user for docker
sudo usermod -G docker -a eouser
sudo chmod 666 /var/run/docker.sock
sudo systemctl restart docker

# Install CNI for ulterior needs in jobs network managing
sudo mkdir -p /opt/cni/bin
sudo wget -O /opt/cni/bin/cni-plugins.tgz https://github.com/containernetworking/plugins/releases/download/v${CNIPLUGINS_VERSION}/cni-plugins-linux-amd64-v${CNIPLUGINS_VERSION}.tgz
sudo tar -C /opt/cni/bin -xvf /opt/cni/bin/cni-plugins.tgz

# Create Nomad server config file
cat <<CONF > /home/eouser/nomad_client.hcl
# Configuration file for Nomad Client

datacenter = "dc1"
data_dir   = "/home/eouser/data_nomad"

# Client configuration
client {
    enabled = true
}

# Consul configuration
consul {
    address = "127.0.0.1:8500" # IP of local Consul Client
    client_service_name = "client-a" # Name of the service
}

# Enable raw_exec plugin for raw_exec job
plugin "raw_exec" {
    config {
        enabled = true
    }
}
CONF

# Create Consul server config file
cat <<CONF > /home/eouser/consul_client.hcl
# Configuration file for Consul Client

datacenter = "dc1"
data_dir   = "/home/eouser/data_consul"

server     = false

advertise_addr= "{{ GetPrivateIP }}" # VM IP
bind_addr = "0.0.0.0"


retry_join = ["CONSUL_SERVER_IP"] # Consul Server IP

# Usefull port to use Consul Connect                  
ports {
    grpc = 8502
  }
# Enable Consul Connect
connect {
    enabled = true
}
CONF

# Run Nomad and Consul agents as servers
sudo nohup consul agent -config-file=/home/eouser/consul_client.hcl &
sudo nohup nomad agent -config=/home/eouser/nomad_client.hcl 2>&1 nomad_log.txt &