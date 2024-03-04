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

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~ Resources provisioning ~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~ Volume provisioning ~~#
# Provisions a volume as database. An image is needed to make it a bootable volume.
resource "openstack_blockstorage_volume_v3" "database" {
  region      = var.prod-env-region
  name        = "tf-database-volume"
  size        = var.database-size-gb
  volume_type = var.database-volume-type
  image_id    = var.ubuntu_2204

    # Manage the lifecycle of the volume. As a basis to prevent unwanted deletion,
    # set "prevent_destroy" to true. Set it to false to update the volume.
    # "create_before_destroy" key allows to force a new volume to be up before destroying
    # the old one
    lifecycle {
      create_before_destroy = true
      prevent_destroy       = true
    }
}

#~~ Floating IPs provisioning ~~#
# For database VM
resource "openstack_networking_floatingip_v2" "database-fip" {
  pool = var.external-network-name
  lifecycle {
    prevent_destroy = true
  }
}

#~~ Security groups provisioning ~~#
#~~ Postgresql
resource "openstack_networking_secgroup_v2" "postgrest" {
  name        = "Postgresql"
  description = "Postgresql related security group. To be applied to all VMs with a Postgresql server running on it."
  delete_default_rules = "true"
}
# This security group has no rules provided Postgresql servers do not need any particular network configuration.

#~~ VM provisioning ~~#
# Creates the required ssh-key for conections purposes
resource "openstack_compute_keypair_v2" "database_server_external_ssh_key" {
  name = "database_server_key"
}
# Provisions an instance as database-server
resource "openstack_compute_instance_v2" "database-server" {
    name = "tf-database"
    image_id = var.ubuntu_2204
    flavor_name = var.database-flavor-name
    key_pair = openstack_compute_keypair_v2.database_server_external_ssh_key.name # To allow ssh connection
    security_groups  = [
     "allow_ping_ssh_icmp_rdp",
     "Postgresql" ]

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

  user_data = "${file("install_and_run_nomad_consul_client.sh")}"
}

#~~ Associate floating IPs to VMs ~~#
# admin
resource "openstack_compute_floatingip_associate_v2" "fip_database" {
  floating_ip = openstack_networking_floatingip_v2.database-fip.address
  instance_id = openstack_compute_instance_v2.database-server.id
  fixed_ip    = openstack_compute_instance_v2.database-server.network.0.fixed_ip_v4
}


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~ Outputs definition ~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Those are to be requested for deployment purposes
output "database_ip_address" {
  value = openstack_networking_floatingip_v2.database-fip.address
  description = "The external IP address of the tf-database instance."
}

output "database_external_private_key" {
  sensitive = true
  value = openstack_compute_keypair_v2.database_server_external_ssh_key.private_key
  description = "The private ssh key to connect to the tf-database instance for user 'eouser'."
}
