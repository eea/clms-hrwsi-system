job "database" {
  type        = "service"
  datacenters = ["dc1"]

  constraint {
    attribute = "${attr.unique.hostname}"
    value = "tf-database"
  }

  group "db" {

    network {
      port  "db"{
        static = 5432
      }
    }
    task "db" {
      driver = "docker"

      config {
        image = "redacted/eea_hr-wsi/nrt_production_system/hrwsi-database-prod"
        ports = ["db"]
        auth {
          server_address = "redacted"
          username = "redacted"
          password = "redacted"
        }
      }

      service {
        name = "database"
        port = "db"
        provider = "nomad"

        check {
          type     = "tcp"
          interval = "2s"
          timeout  = "2s"
        }
      }
    
      env {
        POSTGRES_DB = "hrwsi_db"
        POSTGRES_USER = "redacted"
        POSTGRES_PASSWORD = "redacted"
      }
    }
  }

  group "postgrest" {

    network {
        port "postgrest" {
            static = 3000
        }
    }

    task "postgrest" {
      driver = "docker"

      config {
        image = "postgrest/postgrest"
        ports = ["postgrest"]
      }

      service {
        name = "postgrest"
        port = "postgrest"
        provider = "nomad"

        check {
          type     = "tcp"
          interval = "2s"
          timeout  = "2s"
        }
      }

      env {
        PGRST_DB_URI = "redacted://redacted:redacted@db_container:5432/hrwsi_db"
        PGRST_DB_SCHEMA = hrwsi
        PGRST_DB_ANON_ROLE = web_anonymous
      }
    }
  }
}

