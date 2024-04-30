# Batch job 
# Writes "Hello, Nomad!" in "/home/eouser/nomad_output.txt"

job "easy_job" {
  datacenters = ["dc1"]

  type = "batch" # For finite task

  group "groupe1" {
    count = 1

    task "simple_task" {
      driver = "raw_exec"
      config {
        command = "/bin/bash"
        args    = ["-c", "echo 'Hello, Nomad!' > /home/eouser/nomad_output.txt"]
      }
    }
  }
}