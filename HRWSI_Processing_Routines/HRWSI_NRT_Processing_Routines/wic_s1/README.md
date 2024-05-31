# HRWSI WICS1 Processing Routine

Creates WIC S1 product from SIG0 (preprocessed Sentinel-1 sigma nought backscatter coefficient) product.

Missing:
- Metadata (XML)
- Statistics

## Inputs:
- YAML Configuration file
- Sigma nought (SIG0) Product
- Water layer
- Meteorological data (2m temperature 5-day sum and daily average windspeed)
- Radarshadow/layover/foreshortening mask
- Waterbody category layer
- Classification coefficients layer
- Imperviousness density layer
- Grassland layer
- Tree cover density layer

## Folder structure:

There is no fixed folder structure. The scripts handle files and folders according to the YAML configuration file. Parameters used in file paths are the following, as a tree (indent means a subdirectory or file). "_file" parameters can be a relative path, including a folder (see example).

- aux_dir: 
    - water_file
    - gl_file
    - imd_file
    - tcd_file
- input_dir
    - category_file
    - coefficient_file
    - radarshadow_file
    - sigma0_file
    - tempsum_file
    - windspeed_file
- intermediate_dir
- output_dir
    - product_title (later manupilated in processing)
- tmp_dir
- log_out_file
- log_err_file


## YAML Configuration file
Other than the parameters listed in folder structure, remanining parameters are the following:
- tile_id : UTM Tile name of the products

### An example YAML configuration file content:

    aux_dir: /opt/wsi/auxiliaries
    category_file: waterbody_categories/wc_60m_38TKL.tif
    coefficient_file: classification_coefficients/cc_60m_38TKL.tif
    gl_file: grassland/GRA_2018_010m_eu_03035_V1_0_60m_38TKL.tif
    imd_file: imperviousness/IMD_2018_010m_eu_03035_V2_0_60m_38TKL.tif
    input_dir: /opt/wsi/input
    intermediate_dir: /opt/wsi/intermediate
    log_err_file: /opt/wsi/logs/wics1_processing_routine_S1BT20210920T031622_stderr.log
    log_out_file: /opt/wsi/logs/wics1_processing_routine_S1BT20210920T031622_stdout.log
    output_dir: /opt/wsi/output
    product_title: WIC_20210920T031622_S1B_T38TKL_processingBaseline_1
    radarshadow_file: radarshadow/T38TKL_60m_t050_S1_RADAR_SHADOW_LAYOVER_v20240319.tif
    sigma0_file: sigma0/SIG0_20210920T031622_20210920T031712_036F1E_T38TKL_10m_S1BIWGRDH_ENVEO.tif
    tcd_file: treecover/TCD_2018_010m_eu_03035_V2_0_60m_38TKL.tif
    tempsum_file: temperature/20210920_t2m_sum.nc
    tile_id: 38TKL
    tmp_dir: /opt/wsi/temp
    water_file: water_layer/WL_2018_60m_38TKL.tif
    windspeed_file: wind_speed/20210920_wind_speed.nc


## Usage

#### Build docker image

    docker build . -t wics1

#### Test docker image

    docker run wics1 python3 wics1.py --help

Output:

    usage: wics1.py [-h] parameters_file

    positional arguments:
       parameters_file  Path to the configuration parameters file

    options:
       -h, --help       show this help message and exit

#### Run docker image with correct mounts

    docker run \
            --mount type=bind,\
            source=path_to_parent_dir_in_host,\
            target=path_to_parent_dir_in_container \
            wics1 python3 wisc1.py path_to_yaml_file

In the example YAML configuration file above, **/opt/wsi** is the parent directory for the directories. In the host, consider the input files are under the parent directory **/home/users/eouser/processing** and the YAML file is in "processing_routine" in that directory, such as:

    /home/users/eouser/processing
                        ├── auxiliaries
                        │   ├── grassland
                        │   │   └── GRA_2018_010m_eu_03035_V1_0_60m_38TKL.tif
                        │   ├── imperviousness
                        │   │   └── IMD_2018_010m_eu_03035_V2_0_60m_38TKL.tif
                        │   ├── treecover
                        │   │   └── TCD_2018_010m_eu_03035_V2_0_60m_38TKL.tif
                        │   └── water_layer
                        │       └── WL_2018_60m_38TKL.tif
                        ├── input
                        │   ├── classification_coefficients
                        │   │   └── cc_60m_38TKL.tif
                        │   ├── radarshadow
                        │   │   └── T38TKL_60m_t050_S1_RADAR_SHADOW_LAYOVER_v20240319.tif
                        │   ├── sigma0
                        │   │   └── SIG0_20210920T031622_20210920T031712_036F1E_T38TKL_10m_S1BIWGRDH_ENVEO.tif
                        │   ├── temperature
                        │   │   └── 20210920_t2m_sum.nc
                        │   ├── waterbody_categories
                        │   │   └── wc_60m_38TKL.tif
                        │   └── wind_speed
                        │       └── 20210920_wind_speed.nc
                        └── processing_routine
                            └── configuration_file.yml


Correct command then would be:

    docker run --mount type=bind,source=/home/users/eouser/processing,target=/opt/wsi wics1 python3 wics1.py /opt/wsi/processing_routine/configuration_file.yaml

After a successful run, output files would be be under **/opt/wsi/output**, such as:

    /home/users/eouser/processing
                        ├── auxiliaries
                        │   ├── grassland
                        │   │   └── GRA_2018_010m_eu_03035_V1_0_60m_38TKL.tif
                        │   ├── imperviousness
                        │   │   └── IMD_2018_010m_eu_03035_V2_0_60m_38TKL.tif
                        │   ├── treecover
                        │   │   └── TCD_2018_010m_eu_03035_V2_0_60m_38TKL.tif
                        │   └── water_layer
                        │       └── WL_2018_60m_38TKL.tif
                        ├── input
                        │   ├── classification_coefficients
                        │   │   └── cc_60m_38TKL.tif
                        │   ├── radarshadow
                        │   │   └── T38TKL_60m_t050_S1_RADAR_SHADOW_LAYOVER_v20240319.tif
                        │   ├── sigma0
                        │   │   └── SIG0_20210920T031622_20210920T031712_036F1E_T38TKL_10m_S1BIWGRDH_ENVEO.tif
                        │   ├── temperature
                        │   │   └── 20210920_t2m_sum.nc
                        │   ├── waterbody_categories
                        │   │   └── wc_60m_38TKL.tif
                        │   └── wind_speed
                        │       └── 20210920_wind_speed.nc
                        ├── logs
                        │   └── wics1_processing_routine_S1BT20210920T031622_stdout.log
                        ├── output
                        │   ├── output_info.yaml
                        │   └── WIC_20210920T031622_S1B_T38TKL_V100_1
                        ├── processing_routine
                        │   └── configuration_file.yml
                        └── temp

WIC_20210920T031622_S1B_T38TKL_V100 would be then the directory of the final product, and wics1_processing_routine_S1BT20210920T031622_stderr.log and wics1_processing_routine_S1BT20210920T031622_stdout.log would be the software log files.