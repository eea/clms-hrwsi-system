job "worker-pool-manager" {
  type        = "service"
  datacenters = ["dc1"]

  constraint {
    attribute = "${attr.unique.hostname}"
    value = "tf-worker-pool-manager"
  }

  group "worker-pool-manager" {

    task "worker-pool-manager" {
      driver = "docker"

      config {
        image = "postgres:latest" # to be replaced
      }

      service {
        name = "worker-pool-manager"
        provider = "nomad"

        check {
          type     = "tcp"
          interval = "2s"
          timeout  = "2s"
        }
      }
    }
  }
}

