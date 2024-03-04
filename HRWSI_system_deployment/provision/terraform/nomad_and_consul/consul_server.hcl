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