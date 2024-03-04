# Deploy

This directory is usefull for deploying a cluster on the DIAS and run jobs on this cluster.

We use **Nomad** and **Consul** technologies.

**Nomad** is a flexible workload orchestrator that enables to easily deploy and manage any containerized or legacy application using a single, unified workflow.

**Consul** is a service networking solution that enables teams to manage secure network connectivity between services and across on-prem and multi-cloud environments and runtimes.

To deploy a Nomad cluster with Consul, at least one Nomad server and one Consul server connected to each other on a virtual machine are required. The servers will manage the infrastructure. The [*job_server*](../provision/terraform/core/job_server) directory allows the servers deployment.

On this cluster, virtual machines are added with a Nomad client and a Consul client onboard. The Nomad client is connected to the Consul client. This Consul client is itself connected to the Consul server. Clients execute jobs on workers of the cluster. The *client_dir* directory allows manual and automatic client deployment.

Once the cluster built, you can run jobs on clients thanks to the *job_dir* directory.
