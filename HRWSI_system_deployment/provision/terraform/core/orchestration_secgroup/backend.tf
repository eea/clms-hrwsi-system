terraform {
  backend "http" {
    address="https://gitana-ext.magellium.com/api/v4/projects/548/terraform/state/secgroup-tfstate.tf"
    lock_address="https://gitana-ext.magellium.com/api/v4/projects/548/terraform/state/secgroup-tfstate.tf/lock"
    unlock_address="https://gitana-ext.magellium.com/api/v4/projects/548/terraform/state/secgroup-tfstate.tf/lock"
    username="robura"
    password="<GitLab_token>"
    lock_method="POST"
    unlock_method="DELETE"
    retry_wait_min="5"
  }
}
