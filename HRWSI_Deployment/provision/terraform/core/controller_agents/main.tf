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

#~~ Floating IPs creation ~~#
# For controller VM
resource "openstack_networking_floatingip_v2" "controller-fip" {
  pool = var.external-network-name
  lifecycle {
    prevent_destroy = false
  }
}

#~~ VMs creation ~~#
# Provisions an instance as controller
resource "openstack_compute_instance_v2" "controller" {
    name = "tf-controller"
    image_id = var.ubuntu_2204
    flavor_name = var.controller-flavor-name
    key_pair = "core_instances_key" # To allow ssh connection
    security_groups  = [ "allow_ping_ssh_icmp_rdp", "Consul", "Nomad", "Postgresql", "Rabbitmq" ]

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

#~~ Associate floating IPs to VMs ~~#
# controller
resource "openstack_compute_floatingip_associate_v2" "fip_controller" {
  floating_ip = openstack_networking_floatingip_v2.controller-fip.address
  instance_id = openstack_compute_instance_v2.controller.id
  fixed_ip    = openstack_compute_instance_v2.controller.network.0.fixed_ip_v4
}
