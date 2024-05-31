# CC



## Folder structure

``` bash
- path/to/workdir
    |_ userconf  
    |    |_ MAJAUserConfig_SENTINEL2.xml
    |    |_ MAJAUserConfig_SENTINEL2_MUSCATE.xml
    |    |_ MAJAUserConfig_SENTINEL2_TM.xml
    |    |_ MAJAUserConfigSystem.xml
    |_ work  
    |    |_ workdir  
    |    |_ maja_inputs
    |         |_ S2A_TEST_GIP_L2COMM_L_ALLSITES_00001_20190626_21000101.EEF
    |         |_ S2B_TEST_GIP_L2COMM_L_ALLSITES_00001_20190626_21000101.EEF
    |         |_ S2(A/B)_L1C.SAFE
    |         |_ SENTINEL2(A/B)_previousL2A
    |         |_ S2A_TEST_GIP_ ... .DBL.DIR
    |         |_ S2A_TEST_GIP_ ... .HDR
    |         .
    |         .
    |         .
    |         |_ S2B_TEST_GIP_ ... .DBL.DIR
    |         |_ S2B_TEST_GIP_ ... .HDR
    |         .
    |         .
    |         .
    |         |_ S2__TEST_AUX_REFDE2_Tile-Id_1001.DBL.DIR
    |         |_ S2__TEST_AUX_REFDE2_Tile-Id_1001.HDR
    |_ output
        |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0  
           |_ DATA/  
           |_ exec_files  
           |_ MASKS  
           |    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_CLM_R2.tif  
           |    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_MG2_R2.tif  
           |    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_EDG_R2.tif  
           |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_FRE_BXX.tif  
           |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_SRE_BXX.tif  
```

## Run CC container for MAJA processing and postprocessing

The CC container is not developed yet. MAJA can be run in any environment, once installed as an executable. The post processing code requires a python3 environment, with certain libraries installed (gdal mostly).

### Build CC image

#TODO

### Prepare auxiliary and input files

#### Auxiliary and input files for MAJA run

The main input file for MAJA run is the Sentinel-2 L1C to be processed to issue an L2A.
Depending on the mode MAJA is used with more input files may be required:

- MAJA_MODE = L2INIT : no more input
- MAJA_MODE = L2NOMINAL : the last available L2A from MAJA issued on the same tile
- MAJA_MODE = L2BACKWARD : a certain number of future L1C (in HR-WSI the 6 next L1C) and no L2A

MAJA requires several auxilliary files to be launched:

- DTM, corresponding on one folder and one file. Always the same for a given tile. Either use one found on HR-WSI Google Drive, or from the S3 buckets, or generate one. To generate a DTM please use the dtmcreation script provided by MAJA, that can be found at MAJA-version/bin/dtmcreation. As an entry it requires a L1C from the  tile of interest and a DEM file covering the corresponding tile. You can specify the coarse resolution with the -c argument (120 or 240 meters, 120 used in HR-WSI). 
- GIPP files. They can be downloaded from Git Repositories maintained by MAJA teams. They can also be found on HR-WSI Google Drive and S3 buckets. The version of the GIPP may differ depending on the version of MAJA you want to use. MAJA also provides a script that takes care of downloading the correct GIPP version.
- CAMS data, if CAMS processing is enabled (not in HR-S&I, most likely in HR-WSI). They need to be retrieved once per day, for all tiles, with the forecast closer to the adquisition time of the S2 images. MAJA also provides a script, camsdownload, to download the correct variables from the Climate Data Store endpoints.
- userconf folder with all its files. The files from the userconf folder allow the user to set up parameters like the RAM allowed, the number of threads (MAJAUserConfigSystem.xml), and to set up the coarse resolution (MAJAUserConfig_SENTINEL2.xml, MAJAUserConfig_SENTINEL2_MUSCATE.xml, MAJAUserConfig_SENTINEL2_TM.xml). The coarse resolution is set up to 120 by default from MAJA version 4.8, to 240 before.

In GIPP files (S2A_TEST_GIP_L2COMM_L_ALLSITES_00001_20190626_21000101.EEF, S2B_TEST_GIP_L2COMM_L_ALLSITES_00001_20190626_21000101.EEF), the user can set up the use of CAMS Data (<Use_Cams_Data>, true to use it, false not to), the maximum value not to generate a L2A, by combining no data pixels, snow and cloud pixels (<Max_No_Data_Percentage>, set to 101 in HR-S&I and HR-WSI to generate L2A even if the tile is fully covered by snow, not the same in CNES configuration), to activate or deactivate the cirrus correction (<Cirrus_Correction_Option>, set to false) and to set up the maximum percentage of cloud beyond which no L2A is generated (<Max_Cloud_Percentage>, set to 90 in both HR-S&I and HR-WSI, and in CNES configuration).

#### Auxiliary files for MAJA CC post processing

No specific auxilliary file is required to run MAJA post processing for CC. All files are from the output of MAJA.

### Launch CC container

#TODO

### Launch MAJA processing

To prepare for MAJA launching:

- create a work/maja_inputs folder
- copy all GIPP files there
- copy the DTM of the tile to process there
- copy the L1C to process there
- if CAMS processing is activated, copy the CAMS files there for the correct day
- create a work/workid folder
- move the userconf folder in the same root folder as the work folder that has just been created

then from the root folder where the work and userconf folders are, run:

```bash
./absolute_path_to_maja_folder/MAJA_version/bin/maja -i work/maja_inputs -ucs userconf -o /absolute/path/to/output/folder -m MAJA_MODE
```

Where MAJA_MODE = L2INIT or L2NOMINAL or L2BACKWARD

### Launch MAJA postprocessing for CC

```bash
python cc/maja_cc_post_processing.py --workdir /path/to/workdir --l2a_name SENTINEL2B_20211130-103814-167_L2A_TTile-Id_C_V1-0
```