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