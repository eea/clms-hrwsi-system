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
#~~ VMs creation ~~#
# Provisions an instance as orchestrator
resource "openstack_compute_instance_v2" "orchestrator" {
    name = "tf-orchestrator"
    image_id = var.ubuntu_2204
    flavor_name = var.orchestrator-flavor-name
    key_pair = "core_instances_key" # To allow ssh connection
    security_groups  = [ "allow_ping_ssh_icmp_rdp", "Consul", "Nomad" ]

    # Link to private network
    network {
        name = var.private-network-name
        uuid = var.private-network-uuid
    }
    # Link to eodata network
    network {
        name = var.eodata-network-name
        uuid = var.eodata-network-uuid
    }

    user_data = "${file("install_and_run_nomad_consul_client.sh")}"
}
# Provisions an instance as worker-pool-manager
resource "openstack_compute_instance_v2" "worker-pool-manager" {
    name = "tf-worker-pool-manager"
    image_id = var.ubuntu_2204
    flavor_name = var.worker-pool-manager-flavor-name
    key_pair = "core_instances_key" # To allow ssh connection
    security_groups  = [ "allow_ping_ssh_icmp_rdp", "Consul", "Nomad" ]

    # Link to private network
    network {
        name = var.private-network-name
        uuid = var.private-network-uuid
    }

    user_data = "${file("install_and_run_nomad_consul_client.sh")}"
    
}
