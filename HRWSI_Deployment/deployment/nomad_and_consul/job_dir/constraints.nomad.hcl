# Batch job with constraints executed several times

job "docs" {
  type = "batch"

  # Constraint on kernel name
  constraint { 
    attribute = "${attr.kernel.name}"
    value     = "linux"
  }

  # Constraint on CPU number 
  constraint {
    attribute = "${attr.cpu.numcores}"
    operator  = "="
    value     = "2"
  }

  group "constained_jobs" {

    # Constraint on distinct hosts
    constraint {
      operator  = "distinct_hosts"
      value     = "true"
    }

    count = 10 # Number of times the task is running
    task "uptime" {
      driver = "exec"
      config {
        command = "uptime"
      }
    }
  }
}