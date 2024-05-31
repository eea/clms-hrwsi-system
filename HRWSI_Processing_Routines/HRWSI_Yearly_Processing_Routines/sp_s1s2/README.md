# HRWSI SPS1S2 Processing Routine

Creates SP S1+S2 product from GFSC products.

Missing:
- QC Calculation NWSO hreshold
- Logging
- Error codes
- YAML parameterization if need be
- Metadata (XML)
- LAEA outputs (or conversion tool)

## Inputs:
- GFSC Product(s)
- Water mask
- Tree cover density layer
- Forest/Urban/Water mask
- Non-mountain mask

## Folder structure:

    /opt/work
            ├── config
            ├── fuw
            │   └── {tile_id}
            ├── gfsc
            │   └── 2020-2021
            │       └── T{tile_id}
            ├── input
            │   └── 2020-2021
            │       └── T{tile_id}
            ├── nm
            │   └── {tile_id}
            ├── output
            ├── tcd
            │   └── {tile_id}
            ├── tmp
            └── water_mask
                └── {tile_id}

## Usage

#### Build docker image
The processing routine docker image is using LIS software as a base. First, LIS docker image should be built, but rastertools (v33) is missing from this repository. **Copy it to "let-it-snow-1.11.0/rastertools-33-open-source"**

Then build the docker images:

    docker build let-it-snow-1.11.0 -t lis:1.11.0
    docker build . -t sps1s2

#### Test docker image

    docker run sps1s2 echo test

Output:

    test

#### Run docker image with correct mounts

    docker run \
            --mount type=bind,\
            source=path_to_parent_dir_in_host,\
            target=path_to_parent_dir_in_container \
            sps1s2 sh /opt/sp/sps1s2.sh \
            tile_id hydroyear_start date_margin

In the host, consider the working directory will be **/home/users/eouser/processing**.
First, we need two configuration files for LIS software to be copied from the repository to config/ :

    mkdir /home/users/eouser/processing/config
    cp path_to_repository/config/lis_configuration.json /home/users/eouser/processing/config/lis_configuration.json
    cp path_to_repository/config/lis_synthesis_launch_file.json /home/users/eouser/processing/config/lis_synthesis_launch_file.json

Auxiliary and input files should be then in the correct folder structure, as such:

    /home/users/eouser/processing
                            ├── config
                            │   ├── lis_configuration.json
                            │   └── lis_synthesis_launch_file.json
                            ├── fuw
                            │   └── 38TKL
                            │       └── T38TKL_60m_MASK_FOREST_URBAN_WATER_v20240404.tif
                            ├── gfsc
                            │   └── 2020-2021
                            │       └── T38TKL
                            │           └── GFSC_20200901-007_S1-S2_T38TKL_V200_0000000000
                            │           └── GFSC_20200902-007_S1-S2_T38TKL_V200_0000000000
                            │           └── .....
                            │           └── GFSC_20211030-007_S1-S2_T38TKL_V200_0000000000
                            │           └── GFSC_20211031-007_S1-S2_T38TKL_V200_0000000000
                            ├── input
                            │   └── 2020-2021
                            │       └── T38TKL
                            ├── nm
                            │   └── 38TKL
                            │       └── T38TKL_60m_MASK_NON_MOUNTAIN_AREA_V20211119.tif
                            ├── output
                            ├── tcd
                            │   └── 38TKL
                            │       └── TCD_2018_010m_eu_03035_V2_0_60m_38TKL.tif
                            ├── tmp
                            └── water_mask
                                └── 38TKL
                                    └── WL_2018_60m_38TKL.tif

In this example, the S2 tile is **"38TKL"**, the hydro year is between **"01.10.2020 - 31.09.2021"** and the number of days at each side of date interval to be included for interpolation (date_margin) is **30 days**.

Correct command then would be:

    docker run \
            --mount type=bind,\
            source=/home/users/eouser/processing,\
            target=/opt/work \
            sps1s2 sh /opt/sp/sps1s2.sh \
            38TKL 2020 30

After a successful run, output files would be be under **/opt/work/output**, intermediate "FSC-like" products would be under /opt/work/input, and intermediate LIS software output would be under /opt/work/output/LIS, such as:

    /home/users/eouser/processing
                            ├── config
                            │   ├── lis_configuration.json
                            │   └── lis_synthesis_launch_file.json
                            ├── fuw
                            │   └── 38TKL
                            │       └── T38TKL_60m_MASK_FOREST_URBAN_WATER_v20240404.tif
                            ├── gfsc
                            │   └── 2020-2021
                            │       └── T38TKL
                            │           └── GFSC_20200901-007_S1-S2_T38TKL_V200_0000000000
                            │           └── GFSC_20200902-007_S1-S2_T38TKL_V200_0000000000
                            │           └── .....
                            │           └── GFSC_20211030-007_S1-S2_T38TKL_V200_0000000000
                            │           └── GFSC_20211031-007_S1-S2_T38TKL_V200_0000000000
                            ├── input
                            │   └── 2020-2021
                            │       └── T38TKL
                            │           └── FSC_20200901T000000_S2_T38TKL_V200_1
                            │           └── FSC_20200902T000000_S2_T38TKL_V200_1
                            │           └── .....
                            │           └── FSC_20211030T000000_S2_T38TKL_V200_1
                            │           └── FSC_20211031T000000_S2_T38TKL_V200_1
                            ├── nm
                            │   └── 38TKL
                            │       └── T38TKL_60m_MASK_NON_MOUNTAIN_AREA_V20211119.tif
                            ├── output
                            │   └── LIS_2020-2021_T38TKL
                            |       └── preprocessing.log
                            │   └── SP_S1-S2_20201001-20210930_T38TKL_V100_1
                            ├── tcd
                            │   └── 38TKL
                            │       └── TCD_2018_010m_eu_03035_V2_0_60m_38TKL.tif
                            ├── tmp
                            └── water_mask
                                └── 38TKL
                                    └── WL_2018_60m_38TKL.tif

 SP_S1-S2_20201001-20210930_T38TKL_V100_1 would be then the directory of the final product, preprocessing.log is the log file for the preprocessing (GFSC conversion) part.