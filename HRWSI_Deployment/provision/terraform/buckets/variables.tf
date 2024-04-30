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

#~~ OPENSTACK CONNECTION ~~#
variable "user-token" {
  type    = string
}