# Variable file to Terraform deployment

variable "keypair" {
  type    = string
  default = "test-keys"
}

################################################
####### DEPENDENCIES FROM ROOT VARIABLES #######
################################################
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
