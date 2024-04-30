job "processing-tasks" {
  type        = "service"
  datacenters = ["dc1"]

  constraint {
    attribute = "${attr.unique.hostname}"
    value = "tf-controller"
  }

  group "processing-tasks" {

    task "processing-tasks" {
      driver = "docker"

      config {
        image = "redacted:latest" # to be replaced
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
  }
}

