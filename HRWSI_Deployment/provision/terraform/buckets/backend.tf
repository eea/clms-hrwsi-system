terraform {
  backend "http" {
    address="redacted/terraform/state/buckets-tfstate.tf"
    lock_address="redacted/terraform/state/buckets-tfstate.tf/lock"
    unlock_address="redacted/terraform/state/buckets-tfstate.tf/lock"
    username="redacted"
    password="redacted"
    lock_method="POST"
    unlock_method="DELETE"
    retry_wait_min="5"
  }
}
