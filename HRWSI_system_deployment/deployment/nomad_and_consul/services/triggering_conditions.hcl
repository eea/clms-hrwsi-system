job "triggering-conditions" {
  type        = "service"
  datacenters = ["dc1"]

  constraint {
    attribute = "${attr.unique.hostname}"
    value = "tf-orchestrator"
  }

  group "triggering-conditions" {

    task "triggering-conditions" {
      driver = "docker"

      config {
        image = "postgres:latest" # to be replaced
      }

      service {
        name = "triggering-conditions"
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

