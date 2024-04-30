# HR-WSI

The objective of this project is to make water snow and ice detection products available in NRT, daily, yearly or multi-yearly for the EEA38 + UK territory.

This project contains multiple processing chains using Sentinel-1 or Sentinel-2 rasters or products processed by this same system.
This project handles the processing routines automatic launch and dispatching on a worker array.

The entire system is deployed on virtual machines on WEkEO, an European DIAS.

## Storage

The project contains several directories:

1. *[HRWSI_Database](HRWSI_Database)* : Everything related to NRT system database content, deployment and use.
2. *[HRWSI_System](HRWSI_System)* : Everything related to NRT system Python core.
3. *[HRWSI_System_deployment](HRWSI_System_deployment)* : Everything related to NRT system infrastructure provisioning, deployment and packaging, including network configuration, VMs, buckets, etc.

## Third party software versions

Openstack 6.3.0  
Terraform 1.6.2  
Nomad 1.6.3  
Consul 1.17.0  
Docker 24.0.5  
cni-plugins 1.3.0
