# Configuration file to deploy NRT system infra

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~ Terraform provisioner ~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Configure the OpenStack Provider
terraform {
  required_providers {
    openstack = {
      source = "terraform-provider-openstack/openstack"
      version = "1.53.0"
    }
  }
}

# Provider to use
provider "openstack" {
          user_name = var.user-name
          tenant_name = var.domain-name
          auth_url = "https://keystone.cloudferro.com:5000/v3"
          domain_name = var.domain-name
          token = var.user-token
          }

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~ Resources deployment ~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~ Security groups deployment ~~#
#~~ HTTP-HTTPS
resource "openstack_networking_secgroup_v2" "http_https" {
  name        = "HTTP_HTTPS"
  description = "HTTP/HTTPS connection related security group. To be applied to all VMs to be accessed via HTTP and or HTTPS protocoles."
  delete_default_rules = "true"
}
#~~ Rules to be applied
# For HTTP
resource "openstack_networking_secgroup_rule_v2" "http" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 80
  port_range_max    = 80
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.http_https.id
}
# For HTTPS
resource "openstack_networking_secgroup_rule_v2" "https" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 443
  port_range_max    = 443
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.http_https.id
}

#~~ NOMAD
resource "openstack_networking_secgroup_v2" "nomad" {
  name        = "Nomad"
  description = "Nomad related security group. To be applied to all VMs with a Nomad client or server running on it."
  delete_default_rules = "true"
}
#~~ Rules to be applied
# For Nomad API HTTP access by server & clients
resource "openstack_networking_secgroup_rule_v2" "nomad_http_api_egress" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 4646
  port_range_max    = 4646
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.nomad.id
}
# For internal RPC communication between servers & client agents and inter server traffic
resource "openstack_networking_secgroup_rule_v2" "nomad_rpc_egress" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 4647
  port_range_max    = 4647
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.nomad.id
}
# For Nomad API HTTP access by server & clients
resource "openstack_networking_secgroup_rule_v2" "nomad_http_api_ingress" {
  direction         = "ingress"
  ethertype         = "IPv4"
  port_range_min    = 4646
  port_range_max    = 4646
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.nomad.id
}
# For internal RPC communication between servers & client agents and inter server traffic
resource "openstack_networking_secgroup_rule_v2" "nomad_rpc_ingress" {
  direction         = "ingress"
  ethertype         = "IPv4"
  port_range_min    = 4647
  port_range_max    = 4647
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.nomad.id
}

#~~ CONSUL
resource "openstack_networking_secgroup_v2" "consul" {
  name        = "Consul"
  description = "Consul related security group. To be applied to all VMs with a Consul client or server running on it."
  delete_default_rules = "true"
}
#~~ Rules to be applied
# Consul API HTTP access
resource "openstack_networking_secgroup_rule_v2" "consul_http_API_ipv4" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 80
  port_range_max    = 80
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# Consul API HTTPS access
resource "openstack_networking_secgroup_rule_v2" "consul_https_API_ipv4" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 443
  port_range_max    = 443
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# For RPC communication between clients and servers
resource "openstack_networking_secgroup_rule_v2" "consul_rpc_ingress" {
  direction         = "ingress"
  ethertype         = "IPv4"
  port_range_min    = 8300
  port_range_max    = 8300
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# Used to gossip with server
resource "openstack_networking_secgroup_rule_v2" "consul_server_gossip_egress_tcp" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 8301
  port_range_max    = 8301
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# Used to gossip with server
resource "openstack_networking_secgroup_rule_v2" "consul_server_gossip_egress_udp" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 8301
  port_range_max    = 8301
  protocol          = "udp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# Used to handle gossip between client agents
resource "openstack_networking_secgroup_rule_v2" "consul_agent_gossip_handler_egress_tcp" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 8301
  port_range_max    = 8301
  protocol          = "tcp"
  remote_group_id   = openstack_networking_secgroup_v2.consul.id
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# Used to handle gossip between client agents
resource "openstack_networking_secgroup_rule_v2" "consul_agent_gossip_handler_egress_udp" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 8301
  port_range_max    = 8301
  protocol          = "udp"
  remote_group_id   = openstack_networking_secgroup_v2.consul.id
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# For gRPC communication to servers
resource "openstack_networking_secgroup_rule_v2" "consul_grpc_egress_tcp" {
  direction         = "egress"
  ethertype         = "IPv4"
  port_range_min    = 8502
  port_range_max    = 8502
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# Used to handle gossip from server
resource "openstack_networking_secgroup_rule_v2" "consul_server_gossip_handler_ingress_tcp" {
  direction         = "ingress"
  ethertype         = "IPv4"
  port_range_min    = 8301
  port_range_max    = 8301
  protocol          = "tcp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# Used to handle gossip from server
resource "openstack_networking_secgroup_rule_v2" "consul_server_gossip_handler_ingress_udp" {
  direction         = "ingress"
  ethertype         = "IPv4"
  port_range_min    = 8301
  port_range_max    = 8301
  protocol          = "udp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# Used to handle gossip between agents
resource "openstack_networking_secgroup_rule_v2" "consul_agent_gossip_handler_ingress_tcp" {
  direction         = "ingress"
  ethertype         = "IPv4"
  port_range_min    = 8301
  port_range_max    = 8301
  protocol          = "tcp"
  remote_group_id   = openstack_networking_secgroup_v2.consul.id
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
# Used to handle gossip between agents
resource "openstack_networking_secgroup_rule_v2" "consul_agent_gossip_handler_ingress_udp" {
  direction         = "ingress"
  ethertype         = "IPv4"
  port_range_min    = 8301
  port_range_max    = 8301
  protocol          = "udp"
  remote_group_id   = openstack_networking_secgroup_v2.consul.id
  security_group_id = openstack_networking_secgroup_v2.consul.id
}
