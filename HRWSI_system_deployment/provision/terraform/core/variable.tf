# Variable file to Terraform deployment

variable "keypair" {
  type    = string
  default = "test-keys"
}

variable "database-flavor-name" {
  type    = string
  default = "eo1.xsmall"
}

variable "orchestrator-flavor-name" {
  type    = string
  default = "eo1.xsmall"
}

variable "job-server-flavor-name" {
  type    = string
  default = "eo1.xsmall"
}

variable "worker-pool-manager-flavor-name" {
  type    = string
  default = "eo1.xsmall"
}

################################################
####### DEPENDENCIES FROM ROOT VARIABLES #######
################################################
#~~ NETWORKS ~~#
#~~ External
variable "external-network-name" {
  type    = string
}
#~~ Private
variable "private-network-name" {
  type    = string
}
variable "private-network-uuid" {
  type    = string
}
#~~ EODATA
variable "eodata-network-name" {
  type    = string
}
variable "eodata-network-uuid" {
  type    = string
}
#~~ OPENSTACK PROJECT ~~#
variable "prod-env-region" {
  type    = string
}
variable "domain-name" {
  type = string
}
variable "user-name" {
  type    = string
}
# Use openstack image list --long to display all available images and their corresponding ids.
variable "ubuntu_2204" {
  type = string
}
#~~ OPENSTACK CONNECTION ~~#
variable "user-token" {
  type    = string
}
