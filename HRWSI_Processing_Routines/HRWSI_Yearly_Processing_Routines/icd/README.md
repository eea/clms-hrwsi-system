# HRWSI ICD Processing Routine

Creates ICD product from WIC products.

**Tested with WIC S1 Input only**

Missing:
- QC Calculation thresholds
- Handling multiproduct day merging
- Metadata (XML)
- LAEA outputs (or conversion tool)

## Inputs:
- WIC S1 Product(s)
- WIC S2 Product(s)
- WIC S1+S2 Product(s)
- Water mask

## Folder structure:

There is no fixed folder structure. The scripts handle files and folders according to the YAML configuration file. Parameters used in file paths are the following, as a tree (indent means a subdirectory or file). "_file" parameters can be a relative path, including a folder (see example).

- aux_dir: 
    - water_layer_file
- wics1_dir
    - wics1_id_list
- wics2_dir
    - wics2_id_list
- wics1s2_dir
    - wics1s2_id_list
- intermediate_dir
- output_dir
    - product_title (later manupilated in processing)
- tmp_dir
- log_out_file
- log_err_file

## YAML Configuration file
Other than the parameters listed in folder structure, remanining parameters are the following:
- tile_id : UTM Tile name of the products (e.g. 38TKL)
- hydroyear_start_date: First day of the hydroyear (e.g. '20201001')
- hydroyear_end_date: Last day of the hydroyear (e.g. '20210930')
- date_margin: Number of days to include at the beginning and end of the hydroyear to include data for interpolation (e.g. 30)
- include_nobs_in_margin: To count number of observations in the date margin (date_margin) or not (e.g. false)
- log_level : Minimum level of the information to be logged (e.g. INFO) (optional, defaults to DEBUG)

### An example YAML configuration file content:

    aux_dir: /opt/wsi/auxiliaries
    product_title: ICD_20201001-20210930_missions_020_T38TKL_processingBaseline_1
    tile_id: 38TKL
    wics1_dir: /opt/wsi/input/wics1
    wics1_id_list:
    - WIC_20200901T031615_S1B_T38TKL_V100_1
    - WIC_20200901T151005_S1A_T38TKL_V100_1
    - WIC_20200902T150137_S1B_T38TKL_V100_1
    # ...
    - WIC_20211026T151012_S1A_T38TKL_V100_1
    - WIC_20211027T150143_S1B_T38TKL_V100_1
    wics2_dir: /opt/wsi/input/wics2
    wics2_id_list: []
    wics1s1_dir: /opt/wsi/input/wics1s2
    wics1s2_id_list: []
    water_layer_file: water_layer/WL_2018_20m_38TKL.tif
    intermediate_dir: /opt/wsi/intermediate
    output_dir: /opt/wsi/output
    tmp_dir: /opt/wsi/temp
    hydroyear_start_date: '20201001'
    hydroyear_end_date: '20210930'
    date_margin: 30
    include_nobs_in_margin: false
    log_out_file: /opt/wsi/logs/icd_processing_routine_38TKL-2020-2021_stdout.log
    log_err_file: /opt/wsi/logs/icd_processing_routine_38TKL-2020-2021_stderr.log

## Usage

#### Build docker image
The processing routine docker image is using LIS software as a base. First, LIS docker image should be built, but rastertools (v33) is missing from this repository. **Copy it to "let-it-snow-1.11.0/rastertools-33-open-source"**

Then build the docker images:

    docker build let-it-snow-1.11.0 -t lis:1.11.0
    docker build . -t icd

#### Test docker image

    docker run icd echo test

Output:

    test

#### Run docker image with correct mounts

    docker run \
            --mount type=bind,\
            source=path_to_parent_dir_in_host,\
            target=path_to_parent_dir_in_container \
            icd python3 icd.py path_to_yaml_file

In the example YAML configuration file above, **/opt/wsi** is the parent directory for the directories. In the host, consider the input files are under the parent directory **/home/users/eouser/processing** and the YAML file is in "processing_routine" in that directory, such as:

    /home/users/eouser/processing
                            ├── auxiliaries
                            │   └── water_layer
                            │       └── WL_2018_20m_38TKL.tif
                            ├── input
                            │   ├── wics1
                            │   │   ├── WIC_20200901T031615_S1B_T38TKL_V100_1
                            │   │   ├── WIC_20200901T151005_S1A_T38TKL_V100_1
                            │   │   ├── WIC_20200902T150137_S1B_T38TKL_V100_1
                            │   │   ├── ...
                            │   │   ├── WIC_20211026T151012_S1A_T38TKL_V100_1
                            │   │   └── WIC_20211027T150143_S1B_T38TKL_V100_1
                            │   ├── wics1s2
                            │   └── wics2
                            └── processing_routine
                                └── configuration_file.yml

Correct command then would be:

    docker run --mount type=bind,source=/home/users/eouser/processing,target=/opt/wsi icd python3 icd.py /opt/wsi/processing_routine/configuration_file.yml

After a successful run, output files would be be under **/opt/work/output**, intermediate "FSC-like" products and LIS software output would be under /opt/work/intermediate, such as:

    /home/users/eouser/processing
                            ├── auxiliaries
                            │   └── water_layer
                            │       └── WL_2018_20m_38TKL.tif
                            ├── input
                            │   ├── wics1
                            │   │   ├── WIC_20200901T031615_S1B_T38TKL_V100_1
                            │   │   ├── WIC_20200901T151005_S1A_T38TKL_V100_1
                            │   │   ├── WIC_20200902T150137_S1B_T38TKL_V100_1
                            │   │   ├── ...
                            │   │   ├── WIC_20211026T151012_S1A_T38TKL_V100_1
                            │   │   └── WIC_20211027T150143_S1B_T38TKL_V100_1
                            │   ├── wics1s2
                            │   └── wics2
                            ├── intermediate
                            │   ├── FSC_20200901T120000_S2_T38TKL_V100_1
                            │   ├── FSC_20200902T120000_S2_T38TKL_V100_1
                            │   ├── ...
                            │   ├── FSC_20211026T120000_S2_T38TKL_V100_1
                            │   ├── FSC_20211027T120000_S2_T38TKL_V100_1
                            │   └── LIS_20201001-20210930_S1-S2_020_T38TKL_V100_1
                            ├── logs
                            │   └── icd_processing_routine_38TKL-2020-2021_stdout.log
                            │   └── icd_processing_routine_38TKL-2020-2021_strerr.log
                            ├── output
                            │   ├── ICD_20201001-20210930_S1-S2_020_T38TKL_V100_1
                            │   └── output_info.yaml
                            ├── processing_routine
                            │   └── configuration_file.yml
                            └── temp

 ICD_20201001-20210930_S1-S2_020_T38TKL_V100_1 would be then the directory of the final product, and icd_processing_routine_38TKL-2020-2021_stderr.log and icd_processing_routine_38TKL-2020-2021_stdout.log would be the software log file.