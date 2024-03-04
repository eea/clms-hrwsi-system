# Services deployment

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

Two patterns are present in this folder.

## One service, one job

Each service (_i-e_ the orchestrator, the worker-pool-manager service and the database service) has a dedicated job, with one group and one task. The only exception is the database as both the postgres database and the postgrest server must be deployed.

## One node, one job

Three "meta-services" exist (_i-e_ database, worker-pool-manager, orchestrator). These meta services might need to be subdivised in smaller groups or tasks.

As the postgres database and the postgrest server are to be deployed on the same instance, hence the same node (tf-database) they share the same constraint section, at the job level. As all tasks within a group must be deployed on the same node the two tasks might be in the same group, instead of being in two separate groups with one task each ?

The three services from the orchestrator "meta-service" are meant to be deployed on the same instance (tf-orchestrator), and could be grouped in one job with the same constraint, and one group. Then one task per service is implemented.
