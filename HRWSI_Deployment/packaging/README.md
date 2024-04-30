# Package

The code of the processing chain is packed thanks to **Packer**.

**Packer** automates the creation of any type of machine image, including Docker images.

In our case, we use packer to create a docker image of **GRS** and another of **obs2co**. We will explain how to build an image with packer.

You have to download Packer like this :

```batch
packer_version=1.9.4
wget https://releases.hashicorp.com/packer/${packer_version}/packer_${packer_version}_linux_amd64.zip
unzip packer_${packer_version}_linux_amd64.zip
sudo mv packer /usr/bin/
```

You also need docker :

```batch
docker_version=24.0.5-0ubuntu1~22.04.1
sudo apt-get install -y docker.io=${docker_version} 
```

## Build GRS docker image

First and foremost, you must have the coresponding version of s2driver at the same level as grs2.
You should also make sure that the grsdata folder is full (it is a LTS).

You must move *grs.pkr.hcl* file to have a structure as diplayed below.

head_folder  
 ├grs2  
 ├s2driver  
 └grs.pkr.hcl

Note that anything in this folder tree will be added to the Docker build context, so make it light.
You might consider removing the notebooks and all useless files and directories from the grs2 & s2driver folders to make the resulting image as light as possible (.git, illustration, notebook...).

Once all those requirements are met, you can build the Docker image using Packer thanks to following commands :

* Download Packer plugin binaries

```batch
sudo packer init grs.pkr.hcl
```

* Applies a subset of HCL language style conventions

```batch
sudo packer fmt grs.pkr.hcl
```

* Validate the syntax and configuration of a template

```batch
sudo packer validate grs.pkr.hcl
```

* Runs all the builds within it in order to generate a set of artifacts

```batch
sudo packer build grs.pkr.hcl
```

When the compilation has ended, you can access the image with the command:

```batch
docker images
```

To run the Docker image in a container on a S2 raster you can use the *run_docker.sh* script as follow:

```batch
./run_docker.sh <image_ID> <S2_raster_path> <CMAS_data_path> <desired_name_for_output> <desired_path_for_output> <desired_resolution> <surfwater_tif_path>
```

You can find images_ID at the end of *grs.pkr.hcl*, in post-processor "docker-tag" : images_ID = repository:tag.

Example:

```batch
./run_docker.sh grs2:0.0 \
/DATA/S2_raster/S2B_MSIL1C_20220228T102849_N0400_R108_T31TFJ_20220228T123819.SAFE \
/DATA/CAMS/2022-02-28-cams-global-atmospheric-composition-forecasts.nc \
S2B_L2Agrs_20220228T102849_N0400_R108_T31TFJ_20220228T123819 \
/DATA/grs_outputs \
60 \
/DATA/Surfwater/SURFWATER_OPTICAL-SINGLE_T31TFJ_20220228T103850_20220228T103850_1-0-4_06/SURFWATER_OPTICAL-SINGLE_T31TFJ_20220228T103850_20220228T103850_1-0-4_06.tif
```

The docker containers will be called grs2, which mean that you cannot currently launch multiple ones simultaneously.

You can adapt the sh script to modify this behaviour.

> *Congrats you just build GRS docker image with Packer ! You can also build OBS2CO docker image.*

## Build OBS2CO docker image

You must move *obs2co.pkr.hcl* file to have a structure as diplayed below.

head_folder  
 ├obs2co_l2bgen  
 └obs2co.pkr.hcl

Note that anything in this folder tree will be added to the Docker build context, so make it light.
You might consider removing the notebooks and all useless files and directories from the obs2co_l2bgen folder to make the resulting image as light as possible (.git, illustration, notebook...).

Once all those requirements are met, you can compile the Docker image using following commands :

* Download Packer plugin binaries

```batch
sudo packer init obs2co.pkr.hcl
```

* Applies a subset of HCL language style conventions

```batch
sudo packer fmt obs2co.pkr.hcl
```

* Validate the syntax and configuration of a template

```batch
sudo packer validate obs2co.pkr.hcl
```

* Runs all the builds within it in order to generate a set of artifacts

```batch
sudo packer build obs2co.pkr.hcl
```

When the compilation has ended, you can access the image with the command :

```batch
docker images
```

To run the Docker image in a container on a S2 raster you can use the *run_docker.sh* script as follow:

```batch
./run_docker.sh <image_ID> <L2A_raster_name> <L2A_raster_path> <desired_name_for_output> <desired_path_for_output>
```

You can find images_ID at the end of *obs2co.pkr.hcl*, in post-processor "docker-tag" : images_ID = repository:tag.

Example:

```batch
./run_docker.sh obs2co_l2bgen:0.0 \
S2B_L2Agrs_20220228T102849_N0400_R108_T31TFJ_20220228T123819 \
/DATA/grs_outputs \
S2B_L2Bgrs_20220228T102849_N0400_R108_T31TFJ_20220228T123819 \
/DATA/grs_outputs
```

The docker containers will be called l2bgen, which mean that you cannot currently launch multiple ones simultaneously.
You can adapt the sh script to modify this behaviour.

> *Congrats you just build OBS2CO docker image with Packer !*
