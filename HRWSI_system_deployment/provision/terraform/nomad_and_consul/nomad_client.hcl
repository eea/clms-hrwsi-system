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