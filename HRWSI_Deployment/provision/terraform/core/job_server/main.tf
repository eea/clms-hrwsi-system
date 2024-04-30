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
# Creates the required ssh-key for connections purposes
resource "openstack_compute_keypair_v2" "core_external_ssh_key" {
  name = "core_instances_key"
}

#~~ Floating IPs creation ~~#
# For admin VM
resource "openstack_networking_floatingip_v2" "job-server-fip" {
  pool = var.external-network-name
  lifecycle {
    prevent_destroy = false
  }
}

#~~ VMs creation ~~#
# Provisions an instance as job-server
resource "openstack_compute_instance_v2" "job-server" {
    name = "tf-job-server"
    image_id = var.ubuntu_2204
    flavor_name = var.job-server-flavor-name
    key_pair = openstack_compute_keypair_v2.core_external_ssh_key.name # To allow ssh connection
    security_groups  = [ "allow_ping_ssh_icmp_rdp", "HTTP_HTTPS", "Consul", "Nomad" ]

    # Link to private network
    network {
        name = var.private-network-name
        uuid = var.private-network-uuid
    }

    user_data = "${file("install_and_run_nomad_consul_server.sh")}"
}

#~~ Associate floating IPs to VMs ~~#
# job-server
resource "openstack_compute_floatingip_associate_v2" "fip_job-server" {
  floating_ip = openstack_networking_floatingip_v2.job-server-fip.address
  instance_id = openstack_compute_instance_v2.job-server.id
  fixed_ip    = openstack_compute_instance_v2.job-server.network.0.fixed_ip_v4
}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#~~~~~ Outputs definition ~~~~~#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

output "job_server_floating_ip" {
  sensitive = true
  value = openstack_networking_floatingip_v2.job-server-fip.address
  description = "The floating ip of the tf_job_server, to connect with ssh"
}

output "job_server_fixed_ip" {
  sensitive = true
  value = openstack_compute_instance_v2.job-server.access_ip_v4 
  description = "The fixed ip of the tf_job_server, to set up Consul clients connection with Consul server"
}

output "core_external_private_key" {
  sensitive = true
  value = openstack_compute_keypair_v2.core_external_ssh_key.private_key
  description = "The private ssh key to connect to the tf-job-server, tf-worker-pool-manager and tf-controller instance for user 'eouser'."
}
