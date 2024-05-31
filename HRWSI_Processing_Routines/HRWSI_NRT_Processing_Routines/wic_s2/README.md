# WIC_S2

## Folder structure

``` bash
- output_folder  
    |_ WIC_S2_output_product  
    |    |_ WICS2_MEASUREMENT-DATE_S2X_Tile-Id_V100_0_WIC.tif
    |    |_ WICS2_MEASUREMENT-DATE_S2X_Tile-Id_V100_0_PRB.tif
    |    |_ WIC_METADATA.XML  
    |    |_ tmp  
    |        |_ g_blue.tif  
    |        |_ resampled_B2.tif  
    |        |_ std_g_blue.tif
    |        |_ proba_other_features.tif
    |        |_ proba_snow_ice.tif
    |        |_ proba_water.tif


- input_image_path .../SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0
    |_ MASKS  
    |    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_CLM_R2.tif  
    |    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_MG2_R2.tif  
    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_FRE_BXX.tif  
    |_ SENTINEL2X_MEASUREMENT-DATE_L2A_TTile-Id_C_V1-0_SRE_BXX.tif  
```

## Compute a WIC S2 product

Three steps are done to compute a WIC S2 product :
- compute textures : gradient of blue bands and standard deviation of the gradient of the blue band, which are inputs to the classifier
- classification : using a Random Forest classifier
- post processing : compute QC and QCFLAGS layers

For the WIC computation including both steps, one can run :
``` bash
python processing/l2a_to_WIC_RF.py processing/config_classifier.json
python processing/processing/wics2_post_processing.py processing/config_classifier.json
```
