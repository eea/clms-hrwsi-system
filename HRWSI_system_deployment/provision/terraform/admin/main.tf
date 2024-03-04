# Configuration file to deploy NRT system persistent infra

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
# For admin VM
resource "openstack_networking_floatingip_v2" "admin-fip" {
  pool = var.external-network-name
  lifecycle {
    prevent_destroy = true
  }
}

# Provisions an instance as admin-server
resource "openstack_compute_instance_v2" "admin-server" {
    name = "tf-admin"
    image_id = var.ubuntu_2204
    flavor_name = var.admin-flavor-name
    key_pair = var.keypair # To allow ssh connection
    security_groups  = [
     "allow_ping_ssh_icmp_rdp" ]

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
    lifecycle {
        prevent_destroy = false
  }
}
#~~ Associate floating IPs to VMs ~~#
# admin
resource "openstack_compute_floatingip_associate_v2" "fip_admin" {
  floating_ip = openstack_networking_floatingip_v2.admin-fip.address
  instance_id = openstack_compute_instance_v2.admin-server.id
  fixed_ip    = openstack_compute_instance_v2.admin-server.network.0.fixed_ip_v4
}
