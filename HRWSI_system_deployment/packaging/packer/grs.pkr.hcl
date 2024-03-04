# Configures a specific builder plugin, which is then invoked by a build block 
source "docker" "centos" {
  image  = "ubuntu:22.04"
  commit = true
}

build {
  name = "learn-packer"
  sources = [
    "source.docker.centos"
  ]

  # Usefull to copy a file
  provisioner "file" {
    source      = "<source_folder>"
    destination = "<target_folder>"
  }

  
  # Usefull to download tools / run shell cmd / run a script
  provisioner "shell" {
    inline = [
      "apt-get -qq update",
      "apt-get -qq install -y --no-install-recommends gcc gfortran python-is-python3 python3.10 python3-dev python3-pip python3-affine python3-gdal python3-lxml python3-xmltodict gdal-bin libgdal-dev build-essential",
      "rm -rf /var/lib/apt/lists/",
      "python3 -m pip install --upgrade pip",
      "pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir matplotlib numba numpy rasterio 'eoreader<=0.19.4' cdsapi netCDF4 docopt dask dask[array] xmltodict bokeh gdal geopandas pandas pyproj python-dateutil scipy 'xarray<=2023.4.2'",
	  "python setup.py install",
	  "cp -r grsdata /datalake/watcal/GRS/",
    ]
  }

  # Usefull to name the image, add a version and push  it to a repository
  post-processors {
    post-processor "docker-tag" {
      repository = "<my_repository_name>"
      tag        = ["0.0"]
    }
    # post-processor "docker-push" {} 
  }
}