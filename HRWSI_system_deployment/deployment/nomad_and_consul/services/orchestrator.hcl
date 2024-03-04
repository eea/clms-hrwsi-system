job "orchestrator" {
  type        = "service"
  datacenters = ["dc1"]

  constraint {
    attribute = "${attr.unique.hostname}"
    value = "tf-orchestrator"
  }

  group "orchestrator" {

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

    task "processing-tasks" {
      driver = "docker"

      config {
        image = "postgres:latest" # to be replaced
      }

      service {
        name = "processing-tasks"
        provider = "nomad"

        check {
          type     = "tcp"
          interval = "2s"
          timeout  = "2s"
        }
      }
    }

    task "products" {
      driver = "docker"

      config {
        image = "postgres:latest" # to be replaced
      }

      service {
        name = "products"
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

