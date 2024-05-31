# FSC



## Folder structure

``` bash
- path/to/workdir  
    |_ water_mask  
    |    |_ TILE-ID  
    |        |_ WL_2018_20m_TILE-ID.tif  
    |_ tcd  
    |    |_ TILE-ID  
    |        |_ TCD_2018_010m_eu_03035_V2_0_20m_TILE-ID.tif  
    |_ output  
    |    |_ LIS_S2-SNOW-FSC_TTile-Id_MEASUREMENT-DATE_1.11.0_1.tif  
    |    |_ LIS_S2-SNOW-FSC-QCFLAGS_TTile-Id_MEASUREMENT-DATE_1.11.0_1.tif  
    |    |_ LIS_METADATA.XML  
    |    |_ fsc_config.json  
    |    |_ tmp  
    |        |_ hillshade_mask.tif  
    |        |_ LIS_CLD.tif  
    |        |_ LIS_FSCTOCHS.TIF  
    |        |_ LIS_NDSI.TIF  
    |        |_ no_data_mask.tif  
    |        |_ uncalibrated_shaded_snow.tif  
    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0  
        |_ DATA/  
        |_ exec_files  
        |_ MASKS  
        |    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_CLM_R2.tif  
        |    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_MG2_R2.tif  
        |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_FRE_BXX.tif  
        |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_SRE_BXX.tif  
```

## Run LIS container for LIS processing and postprocessing

The simplest way to to run LIS FSC algorithm, then the FSC postprocessing for HR-WSI is to use the LIS docker image.

### Build LIS image

The let-it-snow-1.11.0 folder at the fsc root folder is already a customized version of let-it-snow 1.11.0.

06/03/2024 : the rastertools git repository used by the default Dockerfile from the LIS git repository is not yet public. No easy access is possible without a CNES token. We temporarily use an extraction from rastertools git repository performed by Guillaume Eynard-Bontemps from CNES and Celine Raille from Thales. The corresponding extraction is the folder named rastertools-33-open-source. On the Git repository the zipped version of this folder is stored. It has to be unzipped before building the image. The Dockerfile has been updated accordingly.

```bash
cd let-it-snow-1.11.0
unzip rastertools-33-open-source.zip
docker build -t lis_1-11-0 .
```

### Prepare auxilliary files

To run LIS FSC algorithm the following files are required, stored in the correct folders:

- water mask : water_mask/$TILE_ID/WL_2018_20m_TILE-ID.tif
- tree cover density : tcd/$TILE_ID/TCD_2018_010m_eu_03035_V2_0_20m_TILE-ID.tif
- dem : dem/$TILE_ID/Copernicus_DSM_04_N02_00_00_DEM_20m_Tile-Id.tif

LIS can be launched with arguments or with a json file, similar to launch_configuration_file.json.

Another configuration file is used for system parameters of LIS, lis_configuration.json. The default one found in this repository can be used as it is customized for HR-WSI purposes. The shaded_snow section, "rastertools_window_size" has been updated to 4096 instead of 1024 to prevent LIS from failing on tiles from northern scandinavia, during winter months. this value might be updated again before the launching of the operational chain as there is no certainty that 4096 is high enough of a value to prevent rastertools exceptions.

Sentinel2 L2A is the last input to provide LIS with. Not all the files are usefull in the L2A:
- SENTINEL2B_20211230-103814-445_L2A_TTile-Id_C_V1-0_FRE_B3.tif
- SENTINEL2B_20211230-103814-445_L2A_TTile-Id_C_V1-0_FRE_B4.tif
- SENTINEL2B_20211230-103814-445_L2A_TTile-Id_C_V1-0_FRE_B11.tif
- SENTINEL2B_20211230-103814-445_L2A_TTile-Id_C_V1-0_SRE_B2.tif
- SENTINEL2B_20211230-103814-445_L2A_TTile-Id_C_V1-0_SRE_B8A.tif
- SENTINEL2B_20211230-103814-445_L2A_TTile-Id_C_V1-0_MTD_ALL.xml
- MASKS/SENTINEL2B_20211230-103814-445_L2A_TTile-Id_C_V1-0_CLM_R2.tif
- MASKS/SENTINEL2B_20211230-103814-445_L2A_TTile-Id_C_V1-0_MG2_R2.tif

### Launch LIS container

You can include the fsc postprocessing routine in th eLIS container to execute it after the processing of LIS.

```bash
docker run -it --name lis_1-11-0_container -v path/to/auxilliaries:/workdir -v path/to/fsc:/usr/local --entrypoint /bin/bash lis_1-11-0
```

### Launch LIS processing

From within the LIS container go

```bash
cd /usr/local
```
If you want to launch LIS with the configuration file, run:

```bash
python app/let_it_snow_fsc.py -j /path/to/launch_configuration_file.json
```

If you want to pass arguments

```bash
python app/let_it_snow_fsc.py --input_dir /path/to/workdir/SENTINEL2B_20211130-103814-167_L2A_TTile-Id_C_V1-0/ -o /path/to/workdir/output -l INFO -c /path/to/workdir/lis_configuration.json --dem /path/to/workdir/dem/Tile-Id/Copernicus_DSM_04_N02_00_00_DEM_20m_Tile-Id.tif --tcd /path/to/workdir/tcd/Tile-Id/TCD_2018_010m_eu_03035_V2_0_20m_Tile-Id.tif --water_mask /path/to/workdir/water_mask/Tile-Id/WL_2018_20m_Tile-Id.tif --chain_version 1.11.0 --product_counter 1
```

### Launch LIS postprocessing

```bash
python fsc/lis_fsc_post_processing.py --workdir /path/to/workdir --l2a_name SENTINEL2B_20211130-103814-167_L2A_TTile-Id_C_V1-0
```
