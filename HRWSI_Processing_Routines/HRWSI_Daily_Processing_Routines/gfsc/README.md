# HRWSI GFSC Processing Routine

Creates GFSC (temporally and spatially gap-filled) and GFSC1 (spatially gap-filled) products from GFSC, FSC and SWS products.

Missing:
- Metadata (XML)
- Statistics

## Inputs:
- YAML Configuration file
- FSC Product(s)
- SWS Product(s)
- GFSC Product(s)
- Water mask

## Folder structure:

There is no fixed folder structure. The scripts handle files and folders according to the YAML configuration file. Parameters used in file paths are the following, as a tree (indent means a subdirectory or file). "_file" parameters can be a relative path, including a folder (see example).

- aux_dir: 
    - water_layer_file
- fsc_dir
    - fsc_id_list
- gfsc_dir
    - gfsc_id_list
- intermediate_dir
- output_dir
    - product_title (later manupilated in processing)
- sws_dir
    - sws_id_list
- tmp_dir
- log_out_file
- log_err_file


## YAML Configuration file
Other than the parameters listed in folder structure, remanining parameters are the following:
- aggregation_timespan : Number of maximum days which the data to be temporally aggregated.
- tile_id : UTM Tile name of the products (e.g. 38TKL)
- log_level : Minimum level of the information to be logged (e.g. INFO) (optional, defaults to DEBUG)
- fsc_id_list : List of input FSC products
- sws_id_list : List of input SWS products
- gfsc_id_list : List of input GFSC products
- obsolete_product_id_list : List of FSC, SWS or GFSC products whom their use are obsolete, due to another input GFSC includes their data.

### An example YAML configuration file content:

    aggregation_timespan: '7'
    aux_dir: /opt/wsi/auxiliaries
    fsc_dir: /opt/wsi/input/fsc
    fsc_id_list:
    - FSC_20210228T080835_S2B_T38TKL_V200_1
    - FSC_20210226T081832_S2A_T38TKL_V200_1
    - FSC_20210223T080836_S2A_T38TKL_V200_1
    gfsc_dir: /opt/wsi/input/gfsc
    gfsc_id_list: []
    intermediate_dir: /opt/wsi/intermediate
    log_err_file: /opt/wsi/logs/gfsc_processing_routine_20210301T38TKL_stderr.log
    log_out_file: /opt/wsi/logs/gfsc_processing_routine_20210301T38TKL_stdout.log
    log_level: DEBUG
    obsolete_product_id_list: []
    output_dir: /opt/wsi/output
    product_title: GFSC_20210301-007_missions_T38TKL_processingBaseline_1715599674
    sws_dir: /opt/wsi/input/sws
    sws_id_list:
    - SWS_20210301T150134_S1B_T38TKL_V200_1
    - SWS_20210228T031612_S1B_T38TKL_V200_1
    - SWS_20210228T151002_S1A_T38TKL_V200_1
    - SWS_20210227T032451_S1A_T38TKL_V200_1
    - SWS_20210223T150201_S1A_T38TKL_V200_1
    tile_id: 38TKL
    tmp_dir: /opt/wsi/temp
    water_layer_file: water_layer/WL_2018_60m_38TKL.tif

## Usage

#### Build docker image

    docker build . -t gf

#### Test docker image

    docker run gf python3 gf.py --help

Output:

    usage: gf.py [-h] parameters_file

    positional arguments:
      parameters_file  Path to the configuration parameters file
    
    optional arguments:
      -h, --help       show this help message and exit

#### Run docker image with correct mounts

    docker run \
            --mount type=bind,\
            source=path_to_parent_dir_in_host,\
            target=path_to_parent_dir_in_container \
            gf python3 gf.py path_to_yaml_file

In the example YAML configuration file above, **/opt/wsi** is the parent directory for the directories. In the host, consider the input files are under the parent directory **/home/users/eouser/processing** and the YAML file is in "processing_routine" in that directory, such as:

    /home/users/eouser/processing
                            ├── auxiliaries
                            │   └── water_layer
                            │       └── WL_2018_60m_38TKL.tif
                            ├── input
                            │   ├── fsc
                            │   │   ├── FSC_20210223T080836_S2A_T38TKL_V200_1
                            │   │   ├── FSC_20210226T081832_S2A_T38TKL_V200_1
                            │   │   └── FSC_20210228T080835_S2B_T38TKL_V200_1
                            │   ├── gfsc
                            │   └── sws
                            │       ├── SWS_20210223T150201_S1A_T38TKL_V200_1
                            │       ├── SWS_20210227T032451_S1A_T38TKL_V200_1
                            │       ├── SWS_20210228T031612_S1B_T38TKL_V200_1
                            │       ├── SWS_20210228T151002_S1A_T38TKL_V200_1
                            │       └── SWS_20210301T150134_S1B_T38TKL_V200_1
                            └── processing_routine
                                └── configuration_file.yml

Correct command then would be:

    docker run --mount type=bind,source=/home/users/eouser/processing,target=/opt/wsi gf python3 gf.py /opt/wsi/processing_routine/configuration_file.yml

After a successful run, output files would be be under **/opt/wsi/output**, such as:

    /home/users/eouser/processing
                            ├── auxiliaries
                            │   └── water_layer
                            │       └── WL_2018_60m_38TKL.tif
                            ├── input
                            │   ├── fsc
                            │   │   ├── FSC_20210223T080836_S2A_T38TKL_V200_1
                            │   │   ├── FSC_20210226T081832_S2A_T38TKL_V200_1
                            │   │   └── FSC_20210228T080835_S2B_T38TKL_V200_1
                            │   ├── gfsc
                            │   └── sws
                            │       ├── SWS_20210223T150201_S1A_T38TKL_V200_1
                            │       ├── SWS_20210227T032451_S1A_T38TKL_V200_1
                            │       ├── SWS_20210228T031612_S1B_T38TKL_V200_1
                            │       ├── SWS_20210228T151002_S1A_T38TKL_V200_1
                            │       └── SWS_20210301T150134_S1B_T38TKL_V200_1
                            ├── intermediate
                            │   ├── GFSC1_20210223_S1-S2_38TKL_V200
                            │   ├── GFSC1_20210227_S1-S2_38TKL_V200
                            │   ├── GFSC1_20210228_S1-S2_38TKL_V200
                            │   └── GFSC1_20210301_S1-S2_38TKL_V200
                            ├── logs
                            │   ├── gfsc_processing_routine_20210301T38TKL_stderr.log
                            │   └── gfsc_processing_routine_20210301T38TKL_stdout.log
                            ├── output
                            │   ├── GFSC_20210301-007_S1-S2_T38TKL_V200_1715599674
                            │   └── output_info.yaml
                            ├── processing_routine
                            │   └── configuration_file.yml
                            └── temp


GFSC_20210916-007_S1-S2_T38TKL_V200_1715599674 would be then the directory of the final product, and gfsc_processing_routine_20210301T38TKL_stderr.log and gfsc_processing_routine_20210301T38TKL_stdout.log would be the software log file.