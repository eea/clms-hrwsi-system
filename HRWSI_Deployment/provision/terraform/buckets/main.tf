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
#~~ Containers deployment ~~#
#~~ Auxiliaries
resource "openstack_objectstorage_container_v1" "aux-bucket" {
  region = var.prod-env-region
  name   = "HRWSI-AUX"
  # We explicitly prevent destruction using terraform. Remove this only if you
  # really know what you're doing.
  lifecycle {
    prevent_destroy = false
  }
}
#~~ logs
resource "openstack_objectstorage_container_v1" "logs-bucket" {
  region = var.prod-env-region
  name   = "HRWSI-LOGS"
  # We explicitly prevent destruction using terraform. Remove this only if you
  # really know what you're doing.
  lifecycle {
    prevent_destroy = false
  }
}
#~~ Intermediate results
resource "openstack_objectstorage_container_v1" "intermediate-results-bucket" {
  region = var.prod-env-region
  name   = "HRWSI-INTERMEDIATE-RESULTS"
  # We explicitly prevent destruction using terraform. Remove this only if you
  # really know what you're doing.
  lifecycle {
    prevent_destroy = false
  }
}
#~~ Processing routines images
resource "openstack_objectstorage_container_v1" "images-bucket" {
  region = var.prod-env-region
  name   = "HRWSI-PROCESSING-ROUTINES-IMAGES"
  # We explicitly prevent destruction using terraform. Remove this only if you
  # really know what you're doing.
  lifecycle {
    prevent_destroy = false
  }
}
#~~ Database backups
resource "openstack_objectstorage_container_v1" "database-backup-bucket" {
  region = var.prod-env-region
  name   = "HRWSI-DATABASE-BACKUP"
  # We explicitly prevent destruction using terraform. Remove this only if you
  # really know what you're doing.
  lifecycle {
    prevent_destroy = false
  }
}
#~~ indexation files
resource "openstack_objectstorage_container_v1" "indexation-files-bucket" {
  region = var.prod-env-region
  name   = "HRWSI-INDEXATION-FILES"
  # We explicitly prevent destruction using terraform. Remove this only if you
  # really know what you're doing.
  lifecycle {
    prevent_destroy = false
  }
}
#~~ KPI files
resource "openstack_objectstorage_container_v1" "kpi-files-bucket" {
  region = var.prod-env-region
  name   = "HRWSI-KPI-FILES"
  # We explicitly prevent destruction using terraform. Remove this only if you
  # really know what you're doing.
  lifecycle {
    prevent_destroy = false
  }
}
