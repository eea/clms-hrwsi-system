job "products" {
  type        = "service"
  datacenters = ["dc1"]

  constraint {
    attribute = "${attr.unique.hostname}"
    value = "tf-controller"
  }

  group "products" {

    task "products" {
      driver = "docker"

      config {
        image = "redacted:latest" # to be replaced
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

