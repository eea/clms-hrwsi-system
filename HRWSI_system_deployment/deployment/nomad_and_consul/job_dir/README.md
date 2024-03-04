# Job deployment

Once a cluster is created, one can deploy jobs on Nomad clients.

This is the general architecture for a job file:

```batch
job
  |_ group
  |     |_ task
  |     |_ task
  |
  |_ group
        |_ task
        |_ task
```

Each job file describes only a single job, however a job may have multiple groups and each group may have multiple tasks. Groups contain a set of tasks that are co-located on the same Nomad client.

Jobs can be of two different types :

* Service : long lived services that run until explicitly stopped. (type by default)

* Batch : short lived jobs that run until they exit successfully. There are two types of batch job :

  * Parameterized who let you configure a batch job to accept required or optional inputs.

  * Periodic who let you schedule a Nomad job to run at set times.

## Communication between services

The advantage of using Consul in addition to Nomad is to allow services to communicate with eachother _via_ proxies thanks to Consul Connect. A service executes one or several tasks. It is positioned on a group or a task block.

If a proxy is added to a service, one or several upstream services can be defined for the proxy to communicate with. Intentions can also be used to control traffic communication between services.

In Consul, the default intention behavior is "allow all", so all service mesh connections are allowed by default. To avoid unexpected behavior, the intention "deny all" shall be added. Explicit intentions between services that need to communicate with each other can then be added too. They will be the only allowded communication streams.  
Intentions can be created be two means :

* On Consul Web UI :
  * Go on Intention > Create
  * Choose Source, Destination and type of Intention (allow or deny)
  * Save intention

* On shell :

```batch
consul intention create -allow service1 service2 # Allow communication service1 > service2

consul intention create -deny service2 service1 # Deny communication service2 > service1
```

You can also delete intentions :

* On Consul Web UI :
  * Go on Intention
  * Click on "..." below Actions
  * Delete

* On shell :

```batch
consul intention delete service1 service2
```

## Run a job

In this directory there are several commented job examples :

* *batch.nomad.hcl* : a batch job that writes "Hello, Nomad!" in "/tmp/nomad_output.txt".

* *connect.nomad.hcl* : a service job with 2 services with proxies.

* *constraints.nomad.hcl* : a batch job with constraints which runs several times.

* *intention.nomad.hcl* : a service job to test intention with 3 services with proxies.

One can run a job on any job constraints compliant VM with a Nomad agent (server VM or client VM) thanks to that command:

```batch
nomad job run path/to/job.nomad.hcl
```

Nomad Web UI displays job status (on Jobs page) and the topology of the server with the current jobs distributed on clients (on Topology page).

> *Congrats your cluster is now operational !*
