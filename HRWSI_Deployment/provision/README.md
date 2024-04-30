# Provision

The provisioning of an infrastructure with hardware resources adequate to the system needs is a crucial step of the system deployment procedure.  
Thus, to deploy the processing chain on the DIAS, we need to know how to allocate virtual machine, manage networks, and create buckets. All that can be done manually on the WEkEO Web UI, by using Openstack CLI, or by using **Terraform** to deploy multiple instances simultaneously.  

**Terraform** creates and manages resources on cloud platforms and other services through their application programming interfaces. Its strengh is that it saves the provisioned infrastructure state in a file it refers to when called again. Thus, it garantees to apply as little modifications to the previously provisioned infrastructure whan called multiple times. Moreover, because it is designed to be infrastructure as code, it is easy to maintain, organized and integrate into a CI-CD chain.  

Hereafter, we are describing hte file tree for the provisionning, the GitLab backend use and the intended use of the provisioning files aka through the CI-CD chain. We will also explain below how to manually deploy a server VM, access it via ssh and also how to deploy multiple clients with Terraform.

## HRWSI provisioning procedure

### File tree

There are 3 folders to host Terraform files below:

- buckets
- core
- database

They are all organized identically and are independent from one another. One could suggest that we could have used Terrafomr modules to link them all to a single root.tf module file. This was tested and faced failure to discriminate destruction-prevented modules from free-to-destroy ones. Thus this methodology has been disregarded.  

A provisionning folder includes:

- `main.tf`: holding the resources to be provisioned (VMs, floating IPs, security groups,...)
- `variable.tf`: the parameter file, including the VM flavours, Docker images IDs,... While main.tf holds the infra structure, variable.tf holds its range and application.
- `backend.tf`: targets the GitLab repository where the provisionning state is stored and referenced to every time a provisioning occures.

The provision root folder also holds a `.tfvars` file which detains project wide variables definition. It is to be referenced to everytime a deployment is achieved using `-var-file`.

### Provisionning using the CI-CD

The CI-CD is able to validate, provision and destroy the infrastructure. It can be only be done on the main branch.  
WARNING: We are not supposed to destroy the infrastructure at any time, the provisionning already updates it accordingly to the tf files modifications. Moreover, the admin, buckets and database provision are protected against destruction, thus cannot be destroyed using Terraform if their lifecycle has not been altered priorly.  
**DO NOT DESTROY ANYTHING YOU HAVE NOT BACKUPED PRIORLY, IF YOU ARE NOT ADAMANT THEIR IS NO OTHER SOLUTION, OR THAT THE DESTROYED RESOURCES IS NEVER TO BE MISSED.**
The CI-CD behaviour is self-explenatory and documented in the gitlab-ci.yml file.

## Deploy VM on Web UI

Login to Web UI then do Compute > Instances > Launch Instance and follow the instructions :

- Give it a name

- Choose a instance source (like Ubuntu 22.04)

- Choose the flavor

- Add networks

- Add security groups (including those for Nomad and Consul)  
It may be necessary to create security groups for Nomad and Consul, you can do that on Web UI (Network > Security Groups > Create Security Group > Add Rules). Here are the necessary rules for Nomad and Consul :
  - [Consul rules](https://developer.hashicorp.com/hcp/docs/hcp/network/hvn-aws/security-groups)
  - Nomad rules : Ingress IPv4 TCP 4646

- Add key pair (usefull to ssh connection), if it's the first time :  
  - Choose Create key Pair
  - Name your key pair
  - Click on Create Keypair
  - Click on Copy Private Key to Clipboard
  - On a new text document, paste the private key
  - Save it on /path/to/your/private/key

- Launch instance

> *Congrats you have a new VM ! Now let's access it in ssh.*

## Access on VM with ssh connection

To do that, you need to associate a floating IP with your VM. You can do this on Web UI by selecting the "Associate Floating IP" option from the action menu of your instance. Afterward, you have to download OpenStack RC File v3 (csi_test-openrc.sh) from the Web UI, located below your username.

On shell, you have to :

- Install Openstack

```batch
sudo apt update
sudo apt install python3-dev python3-pip
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install python-openstackclient
```

- Source your OpenStack RC File and write your password to connect Openstack

```batch
source '/link/to/csi_test-openrc.sh' 
```

- Connect to your VM with ssh connection

```batch
ssh -i /path/to/your/private/key eouser@<floating_IP>
```

> *Congrats you are on your VM ! Now let's run Nomad and Consul server thanks to deploy/server_dir directory. Once done, you can deploy client VM.*

## Deploy Client VM with Terraform

To deploy client VM automatically with Terraform, you don't need Web UI, just do that in a shell :

- Install Openstack

```batch
sudo apt update
sudo apt install python3-dev python3-pip
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install python-openstackclient
```

- Install Terraform

```batch
version=1.6.3
wget https://releases.hashicorp.com/terraform/${version}/terraform_${version}_linux_amd64.zip
unzip terraform_${version}_linux_amd64.zip
sudo mv terraform /usr/bin/
```

- Connect to Openstack

```batch
source '/link/to/csi_test-openrc.sh' 
```

- Change Openstack token in *provision/main.tf*

You can have a token with that command :

```batch
openstack token issue -f shell -c id
```

In *main.tf* we deploy client virtual machine thanks to the script *deploy/client_dir/script_init.sh*, so make sure you’ve changed Consul Server IP in the script :

```batch
retry_join = ["<consul_server_ip>"]
```

The path to the script in *main.tf* may need to be changed :

```batch
user_data = file("path/to/nrt_production_system/deploy/client_dir/script_init.sh")
```

- Use Terraform to deploy virtual machines

```batch
cd path/to/provision
terraform init # Initialize Terraform environment
terraform plan # Optional
terraform apply # Apply Terraform plan main.tf
```

Once VMs' configurations are done, you can see new clients on Nomad Web UI and new services on Consul Web UI.

You can destroy all the virtual machines created in your plan with that command :

```batch
terraform destroy
```

You can customize the type of resources you want and their number by modifying name, image_id, flavor_id, key_pair, security_groups, network and count in the appropriate files.

- Update VM images

You can have an overlook at all available images on the environment your are working on with :

```batch
openstack image list --long
```

You can then update the image id in the correct variable.tf file.

- Update VM flavor

You can have an overlook at all available flavors on the environment you are working on with :

```batch
openstack flavor list --long
```

You can then update the flavor name or id in the correct variable.tf file.

- Create volume

When creating a new volume with terraform, beware that there is no way to force it to be bootable or not. If an image for the volume is provided, it is by default bootable. If not it is not bootable. If a volume is not bootable, there is no way to make it be through terraform scripts. It is though possible to do it manually through Openstack dashboard : Volume > "Modifier le volume" > check "Amorçable".

- Store secret, changing, or local variables

Some values must not be pushed on the GitLab repository (such as passwords, tokens, local paths, etc.) and still be necessary when deploying from your personal computer.
Terraform allows such variables to be externalized in a terraform.tfvars file. The given value is then used by the variable.tf file and used instead of the defualt value.

- Git Ignore some terraform files

terraform.tfstate, terraform.tfstate.backup, terraform.tfvars, .terraform must not be pushed on the Git repository. Please make sure they are included in the .gitignore file before pushing.

> *Congrats you have a Nomad and Consul cluster ! Now you can run job on Nomad. Go to deployment/nomad_and_consul/job_dir.*

## Install Nomad and Consul Cluster

### Install Nomad and Consul server

On tf-job server we aim to install Nomad and Consul agent server.
Before installing them prior basic installation need to be done.

```batch
sudo apt-get update -y
sudo apt-get install -y wget unzip
```

So far the installed version are :

- Nomad v1.6.3
- Consul v1.17.0
Those versions might evolve and be kept up to date on stable releases, at least until the official beginning of the operationnal phase. Later on a strategy of maintainance and update must be decided.

Nomad and consul are retrieved

```batch
wget https://releases.hashicorp.com/nomad/${nomad_version}/nomad_${nomad_version}_linux_amd64.zip
unzip nomad_${nomad_version}_linux_amd64.zip

wget https://releases.hashicorp.com/consul/${consul_version}/consul_${consul_version}_linux_amd64.zip
unzip consul_${consul_version}_linux_amd64.zip

```

It may be moved to /usr/bin for easier access:

```batch
sudo mv nomad /usr/bin/
sudo mv consul /usr/bin/
```

Dedicated repositories are created to store logs, work files, etc...

```batch
sudo mkdir -p /home/eouser/data_nomad
sudo mkdir -p /home/eouser/data_consul
```

Then the ./terraform/nomad_and_consul/nomad_server.hcl and ./terraform/nomad_and_consul/consul_server.hcl are to be applied with nomad and consul command.

```batch
consul agent --config-file=consul_server.hcl &
nomad agent --config=nomad_server.hcl &
```

This operation will deploy the consul and nomad server of the cluster. As the nomad and consul server are parametrized in consul_server.hcl and nomad_server.hcl, the nomad server is directly connected to the consul server. The consul server can see the nomad server and the nomad agents with client role will be linked to the nomad server through the consul cluster.

To visualize the ui dashboard for nomad server you can look for localhost:4646 in a web browser. To do the same with consul server ui dashboard you can go for localhost:8500.

### Install Consul and Nomad agents with client role

On other instance, you can follow the same steps as those used to install the Consul and Nomad servers.

Please use instead the ./terraform/nomad_and_consul/consul_client.hcl and ./terraform/nomad_and_consul/nomad_client.hcl files with:

```batch
consul agent --config-file=consul_client.hcl &
nomad agent --config=nomad_client.hcl &
```

Additional step in the installation can be performed beforehand such as:

```batch
docker_version=24.0.5-0ubuntu1~22.04.1
sudo apt-get install -y docker.io=${docker_version}

sudo usermod -G docker -a eouser
sudo chmod 666 /var/run/docker.sock
sudo systemctl restart docker

cniplugins_version=1.3.0
sudo mkdir -p /opt/cni/bin
sudo wget -O /opt/cni/bin/cni-plugins.tgz https://github.com/containernetworking/plugins/releases/download/v${cniplugins_version}/cni-plugins-linux-amd64-v${cniplugins_version}.tgz
sudo tar -C /opt/cni/bin -xvf /opt/cni/bin/cni-plugins.tgz
```

This will install docker and create a user for it, and install CNI. Both might prove useful for further deployment of jobs on these nomad client nodes, depending on what kind of jobs are to be deployed.

So far going back to the instance on which the Nomad server and the Consul server have been installed and going for localhost:4646 and localhost:8500 on a web browser shall lead to visualize new nodes (depending on how many clients you installed). Please go to "clients" section in nomad ui dashboard to display all the Nomad clients installed previously. Please go to "nodes" section in consul ui dashboard to display all the Consul clients installed previously.

### Automatized installation of Consul and Nomad cluster with Gitlab CI

The Consul and Nomad cluster installation (distinct from the Nomad job deployment) is technically a configuration step of the Terraform provisioning. As such it is performed by the provision Gitlab CI pipeline.

Two main technical solutions have been explored to install the cluster:

- remote installation: after the various instances of the production environment are provisioned, installation scripts, config files, hcl forms are sent to the instances, and they are used remotely. This require a ssh tunel connection from the CI toward the instances. So far this connection is not opened (restriction from Magellium IT).
- installation during the provisioning step: through the user_data section of terraform form files the installation script is passed to the opening instance and run at the start of the instance.

The remote installation would allow an almost complete decorrelation of the two processes (cluster installation and provisioning of the VMs), though the pipeline would become more complex and require more authorisations (hence more error cases). We chose to explore the user_data terraform functionality.

The installation script automatize the installation steps presented in the two previous sections. In addition to these steps, it contains the code of the hcl files, and it takes care of writing them directly on the instance, before running them. The user_data section can only send to the provisioned instance and run one file.

The data_consul and data_nomad repositories are created in the /home/eouser folder, the remaining installation artifacts are cleaned up and the consul and nomad server are started.

In order to perform this complete automatized installation a few crucial steps are to be followed in a specific order:

- on all instances the Consul agent is to be started first as the Nomad agent references it
- apply with terraform the secgroup terraform files so that all instances to provision can access the security groups they need
- the job-server Consul and Nomad agents (ie the Nomad server and Consul server) need to be installed first, as they are contacted by the other agents (specifically the Consul client agents). The clients need the fixed IP of the job-server instance to get in touch
- the tf-job-server needs to be provisioned first so that the fixed IP is known, and the two servers are up before any other agent is installed
- the fixed IP of the ts-job-server has to be retrieved and injected in the Consul client agents hcl files before provisioning any other instance which is part of the cluster.
- to get back the fixed IP : go to the core/job_server folder and run

```batch
terraform output -json job_server_floating_ip | jq -r ''
```

- to replace the server fixed IP in the Consul hcl files run

```batch
sed -i "s/CONSUL_SERVER_IP/$JOB_SERVER_FLOATING_IP/" install_and_run_nomad_consul_client.sh
```
