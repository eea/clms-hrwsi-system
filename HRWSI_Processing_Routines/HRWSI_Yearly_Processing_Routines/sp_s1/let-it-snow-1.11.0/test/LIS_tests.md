# Let-it-snow tests


## Unit tests
* cloud_extraction_unitest
* snow_detector_unitest
* otb_wrappers_unitest
* resolution_unitest
* gdal_wrappers_unitest
* fsc_config_unitest
* snow_synthesis_unitest

## Snow coverage / FSC
For each case (take5, l8, S2 and S2-small):
* launch let_it_snow_fsc.py with json configuration and input and output directory
* Compare snow_pass1.tif file
* Compare snow_pass2.tif file
* Compare snow_pass3.tif file
* Compare LIS_SNOW_ALL.TIF file
* Compare LIS_SEB.TIF file

Only for l8 :
* launch let_it_snow_fsc.py with snow detection
* Compare snow_pass1.tif file

* hysope2 integration test
* test of dem_builder
* launch let_it_snow_fsc.py on a zip file
* shaded_snow_test
* shaded_snow_no_relief_shadow_mask_test
* shaded_snow_detect_shaded_snow_false_test
* shaded_snow_detect_shaded_snow_rastertools

## Synthesis
* snow_synthesis_test 1.6 snow products
* Compare SCD file
* Compare CCD file
* Compare NOBS file
* Compare SOD file
* Compare SMOD file
* snow_synthesis_muscate_test => synthesis on muscate case
* snow_synthesis_without_densification_test => synthesis without densification


* Snow_synthesis_test from last version snow products
* Snow synthesis with zip files
* Snow synthesis with Copernicus snow products
* Snow synthesis with H2 snow products

