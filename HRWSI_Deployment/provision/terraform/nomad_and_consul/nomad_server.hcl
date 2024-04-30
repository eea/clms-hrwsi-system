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