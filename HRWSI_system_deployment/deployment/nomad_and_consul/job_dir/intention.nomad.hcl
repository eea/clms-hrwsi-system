# Job for testing intention and proxy 
# service-a talk to service-b
# service-b talk to service-c
# service-c talk to service-b

job "intention_test" {
  datacenters = ["dc1"]

  group "a" {

    # Usefull to use Consul Connect
    network {
      mode = "bridge" # Allocations run in an isolated network namespace and are connected to the bridge
    }

    service {
      name = "service-a"
      port = "9001"

      # Configuration of Consul Connect
      connect {
        sidecar_service {
          proxy {
            # Configure details of each upstream service that this sidecar proxy communicates with
            upstreams { 
              destination_name = "service-b"
              local_bind_port  = 8080
            }
          }
        }
      }
    }

    # Creates an individual unit of work, such as a Docker container, web application, or batch processing
    task "webservice" {
      driver = "docker"
      config {
        image = "redis:7"
        labels {
          group = "webservice-cache"
        }
      }
    }
  }

  group "b" {
    network {
      mode = "bridge"
    }

    service {
      name = "service-b"
      port = "9002"

      connect {
        sidecar_service {
          proxy {
            upstreams { 
              destination_name = "service-c"
              local_bind_port  = 8080
            }
          }
        }
      }
    }

    task "webservice" {
      driver = "docker"
      config {
        image = "redis:7"
        labels {
          group = "webservice-cache"
        }
      }
    }
  }

  group "c" {
    network {
      mode = "bridge"
    }

    service {
      name = "service-c"
      port = "9003"

      connect {
        sidecar_service {
          proxy {
            upstreams {
              destination_name = "service-b"
              local_bind_port  = 8080
            }
          }
        }
      }
    }

    task "webservice" {
      driver = "docker"

      config {
        image = "redis:7"
        labels {
          group = "webservice-cache"
        }
      }
    }
  }
}