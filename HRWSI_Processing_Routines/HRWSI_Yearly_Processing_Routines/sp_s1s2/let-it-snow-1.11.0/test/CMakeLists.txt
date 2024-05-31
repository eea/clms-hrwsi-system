#
# Copyright (C) 2005-2019 Centre National d'Etudes Spatiales (CNES)
#
# This file is part of Let-it-snow (LIS)
#
#     https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
set(LIS_DATA_ROOT CACHE PATH "The test data directory which contains 3 sub-folders (Baseline/Input-Data-Test/UnitTest)" )
mark_as_advanced(LIS_DATA_ROOT)
if(NOT LIS_DATA_ROOT)
  message(FATAL_ERROR "Please set LIS_DATA_ROOT")
endif()

set(BASELINE ${LIS_DATA_ROOT}/Baseline)
set(DATA_TEST ${LIS_DATA_ROOT}/Input-Data-Test)
set(UNIT_TEST ${LIS_DATA_ROOT}/UnitTest)
set(OUTPUT_TEST ${CMAKE_BINARY_DIR}/Testing/Temporary)

# ########################################
# Unit tests
# ########################################
set(OUTPUT_TEST_UNITEST ${OUTPUT_TEST}/unitest)
add_test(NAME cloud_extraction_unitest
  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/cloud_extraction_test.py
  "${DATA_TEST}/S2/"
  "${UNIT_TEST}/"
  "${OUTPUT_TEST_UNITEST}/cloud_extraction/"
  )

add_test(NAME snow_detector_unitest
  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/snow_detector_test.py
  "${DATA_TEST}/S2/"
  "${UNIT_TEST}/"
  "${OUTPUT_TEST_UNITEST}/snow_detector/"
  )

add_test(NAME otb_wrappers_unitest
  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/otb_wrappers_test.py
  "${UNIT_TEST}/"
  "${OUTPUT_TEST_UNITEST}/otb_wrappers"
  )

add_test(NAME resolution_unitest
  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/resolution_test.py
  "${UNIT_TEST}/"
  "${OUTPUT_TEST_UNITEST}/resolution"
  )

add_test(NAME gdal_wrappers_unitest.py
  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/gdal_wrappers_test.py
  "${DATA_TEST}/S2/"
  "${UNIT_TEST}/"
  "${OUTPUT_TEST_UNITEST}/gdal_wrappers/"
  )

add_test(NAME fsc_config_unitest
  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/fsc_config_test.py
  "${DATA_TEST}/S2/"
  "${UNIT_TEST}/"
  "${OUTPUT_TEST_UNITEST}/fsc_config" 
    )

#add_test(NAME snow_synthesis_unitest
#  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/snow_synthesis_test.py
#  "${OUTPUT_TEST_SYNTHESIS}"
#  "${OUTPUT_TEST_UNITEST}/snow_synthesis"
#    )

# ########################################
# Non regression tests
# ########################################

# -------------------------
# Snow cover - Take5
# -------------------------
add_test(NAME take5_test
  COMMAND ${PYTHON_EXECUTABLE}
  ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
  -c ${DATA_TEST}/Take5/lis_configuration.json
  -i ${DATA_TEST}/Take5/AOI_test_CESNeige/LEVEL2A/Maroc
  -d ${DATA_TEST}/Take5/AOI_test_CESNeige/SRTM/Maroc/Maroc.tif
  -o ${OUTPUT_TEST}/take5
  )
add_test(NAME take5_compare_pass1_test
  COMMAND gdalcompare.py
  ${BASELINE}/take5_test/pass1.tif
  ${OUTPUT_TEST}/take5/tmp/snow_pass1.tif
  )
set_tests_properties(take5_compare_pass1_test PROPERTIES DEPENDS take5_test)

add_test(NAME take5_compare_pass2_test
  COMMAND gdalcompare.py
  ${BASELINE}/take5_test/pass2.tif
  ${OUTPUT_TEST}/take5/tmp/snow_pass2.tif
  )
set_tests_properties(take5_compare_pass2_test PROPERTIES DEPENDS take5_test)

add_test(NAME take5_compare_pass3_test
  COMMAND gdalcompare.py
  ${BASELINE}/take5_test/pass3.tif
  ${OUTPUT_TEST}/take5/tmp/snow_pass3.tif
  )
set_tests_properties(take5_compare_pass3_test PROPERTIES DEPENDS take5_test)

add_test(NAME take5_compare_snow_all_test
  COMMAND gdalcompare.py
  ${BASELINE}/take5_test/snow_all.tif
  ${OUTPUT_TEST}/take5/tmp/LIS_SNOW_ALL.TIF
  )
set_tests_properties(take5_compare_snow_all_test PROPERTIES DEPENDS take5_test)

add_test(NAME take5_compare_final_mask_test
  COMMAND gdalcompare.py
  ${BASELINE}/take5_test/final_mask.tif
  ${OUTPUT_TEST}/take5/tmp/LIS_SEB.TIF
  )
set_tests_properties(take5_compare_final_mask_test PROPERTIES DEPENDS take5_test)

# -------------------------
# Snow cover - L8
# -------------------------
add_test(NAME l8_test
  COMMAND ${PYTHON_EXECUTABLE}
  ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
  -c ${DATA_TEST}/Landsat/lis_configuration.json
  -i ${DATA_TEST}/Landsat/LANDSAT8_OLITIRS_XS_20170308_N2A_France-MetropoleD0004H0001
  -d ${DATA_TEST}/Landsat/LANDSAT8_OLITIRS_XS_20170308_N2A_France-MetropoleD0004H0001/SRTM/dem.tif
  -o ${OUTPUT_TEST}/l8
  )

add_test(NAME l8_compare_pass1_test
  COMMAND gdalcompare.py
  ${BASELINE}/l8_test/pass1.tif
  ${OUTPUT_TEST}/l8/tmp/snow_pass1.tif
  )
set_tests_properties(l8_compare_pass1_test PROPERTIES DEPENDS l8_test)

add_test(NAME l8_compare_pass2_test
  COMMAND gdalcompare.py
  ${BASELINE}/l8_test/pass2.tif
  ${OUTPUT_TEST}/l8/tmp/snow_pass2.tif
  )
set_tests_properties(l8_compare_pass2_test PROPERTIES DEPENDS l8_test)

add_test(NAME l8_compare_pass3_test
  COMMAND gdalcompare.py
  ${BASELINE}/l8_test/pass3.tif
  ${OUTPUT_TEST}/l8/tmp/snow_pass3.tif
  )
set_tests_properties(l8_compare_pass3_test PROPERTIES DEPENDS l8_test)

add_test(NAME l8_compare_snow_all_test
  COMMAND gdalcompare.py
  ${BASELINE}/l8_test/snow_all.tif
  ${OUTPUT_TEST}/l8/tmp/LIS_SNOW_ALL.TIF
  )
set_tests_properties(l8_compare_snow_all_test PROPERTIES DEPENDS l8_test)

add_test(NAME l8_compare_final_mask_test
  COMMAND gdalcompare.py
  ${BASELINE}/l8_test/final_mask.tif
  ${OUTPUT_TEST}/l8/tmp/LIS_SEB.TIF
  )
set_tests_properties(l8_compare_final_mask_test PROPERTIES DEPENDS l8_test)

# -------------------------
# Snow cover - L8 - Shaded Snow
# -------------------------
add_test(NAME l8_shaded_snow_test
  COMMAND ${PYTHON_EXECUTABLE}
  ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
  -c ${DATA_TEST}/Landsat/shaded_snow/lis_configuration_shaded_snow_with_rastertools.json
  -i ${DATA_TEST}/Landsat/LANDSAT8-OLITIRS-XS_20200325-103612-548_L2A_T31TCH_C_V3-1
  -d /work/datalake/static_aux/MNT/COP-DEM_GLO-30-DGED_extracted/dem_cubic.vrt
  -o ${OUTPUT_TEST}/l8_shaded_snow
  -V 1.11.0
  )

add_test(NAME l8_shaded_snow_compare_pass1_test
  COMMAND gdalcompare.py
  ${BASELINE}/l8_test/shaded_snow/LIS_L8-SNOW-MSK_V3-1_T31TCH_1.11.0.tif
  ${OUTPUT_TEST}/l8_shaded_snow/LIS_L8-SNOW-MSK_V3-1_T31TCH_1.11.0.tif
  )
set_tests_properties(l8_shaded_snow_compare_pass1_test PROPERTIES DEPENDS l8_shaded_snow_test)

# -------------------------
# Snow cover - S2 small
# -------------------------
add_test(NAME s2-small_test
  COMMAND ${PYTHON_EXECUTABLE}
  ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
  -c ${DATA_TEST}/S2-SMALL/lis_configuration.json
  -i ${DATA_TEST}/S2-SMALL/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0
  -d ${DATA_TEST}/S2-SMALL/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0/SRTM/S2__TEST_AUX_REFDE2_T29RNQ_0001_ALT_R2.TIF
  -o ${OUTPUT_TEST}/s2-small
  )
add_test(NAME s2-small_compare_pass1_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2-small_test/pass1.tif
  ${OUTPUT_TEST}/s2-small/tmp/snow_pass1.tif
  )
set_tests_properties(s2-small_compare_pass1_test PROPERTIES DEPENDS s2-small_test)

add_test(NAME s2-small_compare_pass2_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2-small_test/pass2.tif
  ${OUTPUT_TEST}/s2-small/tmp/snow_pass2.tif
  )
set_tests_properties(s2-small_compare_pass2_test PROPERTIES DEPENDS s2-small_test)

add_test(NAME s2-small_compare_pass3_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2-small_test/pass3.tif
  ${OUTPUT_TEST}/s2-small/tmp/snow_pass3.tif
  )
set_tests_properties(s2-small_compare_pass3_test PROPERTIES DEPENDS s2-small_test)

add_test(NAME s2-small_compare_snow_all_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2-small_test/snow_all.tif
  ${OUTPUT_TEST}/s2-small/tmp/LIS_SNOW_ALL.TIF
  )
set_tests_properties(s2-small_compare_snow_all_test PROPERTIES DEPENDS s2-small_test)

add_test(NAME s2-small_compare_final_mask_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2-small_test/final_mask.tif
  ${OUTPUT_TEST}/s2-small/tmp/LIS_SEB.TIF
  )
set_tests_properties(s2-small_compare_final_mask_test PROPERTIES DEPENDS s2-small_test)

# -------------------------
# Snow cover - S2
# -------------------------
add_test(NAME s2_test
  COMMAND ${PYTHON_EXECUTABLE}
  ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
  -c ${DATA_TEST}/S2/lis_configuration.json
  -i ${DATA_TEST}/S2/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0
  -d ${DATA_TEST}/S2/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0/SRTM/S2__TEST_AUX_REFDE2_T29RNQ_0001_ALT_R2.TIF
  -o ${OUTPUT_TEST}/s2
  )

add_test(NAME s2_compare_pass1_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2_test/pass1.tif
  ${OUTPUT_TEST}/s2/tmp/snow_pass1.tif
  )
set_tests_properties(s2_compare_pass1_test PROPERTIES DEPENDS s2_test)

add_test(NAME s2_compare_pass2_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2_test/pass2.tif
  ${OUTPUT_TEST}/s2/tmp/snow_pass2.tif
  )
set_tests_properties(s2_compare_pass2_test PROPERTIES DEPENDS s2_test)

add_test(NAME s2_compare_pass3_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2_test/pass3.tif
  ${OUTPUT_TEST}/s2/tmp/snow_pass3.tif
  )
set_tests_properties(s2_compare_pass3_test PROPERTIES DEPENDS s2_test)

add_test(NAME s2_compare_snow_all_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2_test/snow_all.tif
  ${OUTPUT_TEST}/s2/tmp/LIS_SNOW_ALL.TIF
  )
set_tests_properties(s2_compare_snow_all_test PROPERTIES DEPENDS s2_test)

add_test(NAME s2_compare_final_mask_test
  COMMAND gdalcompare.py
  ${BASELINE}/s2_test/final_mask.tif
  ${OUTPUT_TEST}/s2/tmp/LIS_SEB.TIF
  )
set_tests_properties(s2_compare_final_mask_test PROPERTIES DEPENDS s2_test)

add_test(NAME s2_hysope2
  COMMAND ${PYTHON_EXECUTABLE}
  ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
  -j ${DATA_TEST}/S2/hysope2/param.json
  -o ${OUTPUT_TEST}/hysope2
  )

add_test(NAME dem_builder_test
  COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_SOURCE_DIR}/python/s2snow/dem_builder.py
  "${DATA_TEST}/SRTM/sud_ouest.vrt"
  "${DATA_TEST}/Landsat/LANDSAT8_OLITIRS_XS_20150312_N2A_ORTHO_SURF_CORR_PENTE_France-MetropoleD0005H0001.TIF"
  "${OUTPUT_TEST}/landsat_bassies_srtm.tif"
  )

add_test(NAME s2-small_zip_test
  COMMAND ${PYTHON_EXECUTABLE}
  ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
  -c ${DATA_TEST}/S2-SMALL-ZIP/lis_configuration.json
  -i ${DATA_TEST}/S2-SMALL-ZIP/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0.zip
  -o "${OUTPUT_TEST}/s2-small-zip"
  )
  
# -------------------------
# Shaded snow
# -------------------------
add_test(NAME shaded_snow_test
  COMMAND ${PYTHON_EXECUTABLE}
    ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
    -c ${DATA_TEST}/S2/shaded_snow/global_parameters_shaded_snow.json
    -i ${DATA_TEST}/S2/SENTINEL2B_20210124-103807-070_L2A_T31TGM_C_V1-0
    -d ${DATA_TEST}/S2/SENTINEL2B_20210124-103807-070_L2A_T31TGM_C_V1-0/Leman_dem_merged.tif
    -s ${DATA_TEST}/S2/SENTINEL2B_20210124-103807-070_L2A_T31TGM_C_V1-0/hillshade_mask.tif
    -o ${OUTPUT_TEST}/s2/shaded_snow
    -V 1.11.0
    )

add_test(NAME shaded_compare_test
  COMMAND gdalcompare.py
  ${BASELINE}/shaded_snow_test/shaded_snow/LIS_S2-SNOW-FSC-TOC_T31TGM_20210124T103807_1.11.0.tif
  ${OUTPUT_TEST}/s2/shaded_snow/LIS_S2-SNOW-FSC-TOC_T31TGM_20210124T103807_1.11.0.tif
  )
set_tests_properties(shaded_compare_test PROPERTIES DEPENDS shaded_snow_test)

add_test(NAME shaded_snow_no_relief_shadow_mask_test
  COMMAND ${PYTHON_EXECUTABLE}
    ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
    -c ${DATA_TEST}/S2/shaded_snow/global_parameters_shaded_snow.json
    -i ${DATA_TEST}/S2/SENTINEL2B_20210124-103807-070_L2A_T31TGM_C_V1-0
    -d ${DATA_TEST}/S2/SENTINEL2B_20210124-103807-070_L2A_T31TGM_C_V1-0/Leman_dem_merged.tif
    -o ${OUTPUT_TEST}/s2/shaded_snow_no_relief_shadow_mask
    -V 1.11.0
    )

add_test(NAME shaded_snow_no_relief_shadow_mask_compare_test
  COMMAND gdalcompare.py
  ${BASELINE}/shaded_snow_test/shaded_snow_no_relief_shadow_mask/LIS_S2-SNOW-FSC-TOC_T31TGM_20210124T103807_1.11.0.tif
  ${OUTPUT_TEST}/s2/shaded_snow_no_relief_shadow_mask/LIS_S2-SNOW-FSC-TOC_T31TGM_20210124T103807_1.11.0.tif
  )
set_tests_properties(shaded_snow_no_relief_shadow_mask_compare_test PROPERTIES DEPENDS shaded_snowshaded_snow_no_relief_shadow_mask_test_no_relief_shadow_mask)

add_test(NAME shaded_snow_detect_shaded_snow_false_test
  COMMAND ${PYTHON_EXECUTABLE}
    ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
    -c ${DATA_TEST}/S2/shaded_snow/global_parameters_shaded_snow_false.json
    -i ${DATA_TEST}/S2/SENTINEL2B_20210124-103807-070_L2A_T31TGM_C_V1-0
    -d ${DATA_TEST}/S2/SENTINEL2B_20210124-103807-070_L2A_T31TGM_C_V1-0/Leman_dem_merged.tif
    -o ${OUTPUT_TEST}/s2/shaded_snow_detect_shaded_snow_false
    -V 1.11.0
    )

add_test(NAME shaded_snow_detect_shaded_snow_false_compare_test
  COMMAND gdalcompare.py
  ${BASELINE}/shaded_snow_test/shaded_snow_detect_shaded_snow_false/LIS_S2-SNOW-FSC-TOC_T31TGM_20210124T103807_1.11.0.tif
  ${OUTPUT_TEST}/s2/shaded_snow_detect_shaded_snow_false/LIS_S2-SNOW-FSC-TOC_T31TGM_20210124T103807_1.11.0.tif
  )
set_tests_properties(shaded_snow_detect_shaded_snow_false_compare_test PROPERTIES DEPENDS shaded_snow_detect_shaded_snow_false_test)


add_test(NAME shaded_snow_detect_shaded_snow_rastertools
  COMMAND ${PYTHON_EXECUTABLE}
    ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
    -c ${DATA_TEST}/S2/shaded_snow/global_parameters_shaded_snow_rastertools.json
    -i ${DATA_TEST}/S2/SENTINEL2B_20210124-103807-070_L2A_T31TGM_C_V1-0
    -d ${DATA_TEST}/S2/SENTINEL2B_20210124-103807-070_L2A_T31TGM_C_V1-0/Leman_dem_merged.tif
    -o ${OUTPUT_TEST}/s2/shaded_snow_detect_shaded_snow_rastertools
    -V 1.11.0
    )
    
add_test(NAME shaded_snow_detect_shaded_snow_rastertools_compare_test
  COMMAND gdalcompare.py
  ${BASELINE}/shaded_snow_test/shaded_snow_detect_shaded_snow_rastertools/LIS_S2-SNOW-FSC-TOC_T31TGM_20210124T103807_1.11.0.tif
  ${OUTPUT_TEST}/s2/shaded_snow_detect_shaded_snow_rastertools/LIS_S2-SNOW-FSC-TOC_T31TGM_20210124T103807_1.11.0.tif
  )
set_tests_properties(shaded_snow_detect_shaded_snow_rastertools_compare_test PROPERTIES DEPENDS shaded_snow_detect_shaded_snow_rastertools)

# -------------------------
# Synthesis
# -------------------------
add_test(NAME snow_synthesis_test
  COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/app/let_it_snow_synthesis.py
  -i ${DATA_TEST}/SNOW_PRODUCTS/SENTINEL2A_20180101-105435-457_L2A_T31TCH_D_V1-4
  -i ${DATA_TEST}/SNOW_PRODUCTS/SENTINEL2A_20180131-105416-437_L2A_T31TCH_D_V1-4
  -d ${DATA_TEST}/SNOW_PRODUCTS/LANDSAT8-OLITIRS-XS_20180115-103629-617_L2A_T31TCH_D_V1-9
  -d ${DATA_TEST}/SNOW_PRODUCTS/LANDSAT8-OLITIRS-XS_20180131-103619-890_L2A_T31TCH_D_V1-9
  -c ${DATA_TEST}/SYNTHESIS/synthesis_configuration.json
  -j ${DATA_TEST}/SYNTHESIS/synthesis_launch.json
  -V 1.11.0
  -o ${OUTPUT_TEST}/SNOW_SYNTHESIS
  )

add_test(NAME snow_synthesis_compare_scd_test
  COMMAND gdalcompare.py
  "${BASELINE}/snow_synthesis_test/LIS_S2L8-SNOW-SCD_T31TCH_20180101_20180131_1.11.0_1.tif"
  "${OUTPUT_TEST}/SNOW_SYNTHESIS/LIS_S2L8-SNOW-SCD_T31TCH_20180101_20180131_1.11.0_1.tif"
  )
set_tests_properties(snow_synthesis_compare_scd_test PROPERTIES DEPENDS snow_synthesis_test)

add_test(NAME snow_synthesis_compare_ccd_test
  COMMAND gdalcompare.py
  "${BASELINE}/snow_synthesis_test/CLOUD_OCCURENCE_T31TCH_20180101_20180131.tif"
  "${OUTPUT_TEST}/SNOW_SYNTHESIS/tmp/CLOUD_OCCURENCE_T31TCH_20180101_20180131.tif"
  )
set_tests_properties(snow_synthesis_compare_ccd_test PROPERTIES DEPENDS snow_synthesis_test)

add_test(NAME snow_synthesis_compare_nobs_test
  COMMAND gdalcompare.py
  "${BASELINE}/snow_synthesis_test/LIS_S2L8-SNOW-NOBS_T31TCH_20180101_20180131_1.11.0_1.tif"
  "${OUTPUT_TEST}/SNOW_SYNTHESIS/LIS_S2L8-SNOW-NOBS_T31TCH_20180101_20180131_1.11.0_1.tif"
  )
set_tests_properties(snow_synthesis_compare_nobs_test PROPERTIES DEPENDS snow_synthesis_test)

add_test(NAME snow_synthesis_compare_sod_test
  COMMAND gdalcompare.py
  "${BASELINE}/snow_synthesis_test/LIS_S2L8-SNOW-SOD_T31TCH_20180101_20180131_1.11.0_1.tif"
  "${OUTPUT_TEST}/SNOW_SYNTHESIS/LIS_S2L8-SNOW-SOD_T31TCH_20180101_20180131_1.11.0_1.tif"
  )
set_tests_properties(snow_synthesis_compare_sod_test PROPERTIES DEPENDS snow_synthesis_test)

add_test(NAME snow_synthesis_compare_smod_test
  COMMAND gdalcompare.py
  "${BASELINE}/snow_synthesis_test/LIS_S2L8-SNOW-SMOD_T31TCH_20180101_20180131_1.11.0_1.tif"
  "${OUTPUT_TEST}/SNOW_SYNTHESIS/LIS_S2L8-SNOW-SMOD_T31TCH_20180101_20180131_1.11.0_1.tif"
  )
set_tests_properties(snow_synthesis_compare_smod_test PROPERTIES DEPENDS snow_synthesis_test)

if(NOT GITLAB_CI_BUILD MATCHES "true")
  add_test(NAME snow_synthesis_muscate_test
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/app/let_it_snow_synthesis.py
    -t T31TDJ
    -i ${DATA_TEST}/SNOW_PRODUCTS/SENTINEL2A_20200410-105852-276_L2B-SNOW_T31TDJ_C_V1-7
    -d ${DATA_TEST}/SNOW_PRODUCTS/LANDSAT8-OLITIRS-XS_20200410-103540-665_L2B-SNOW_T31TDJ_C_V1-7
    -b 01/09/2019
    -e 31/08/2020
    -l DEBUG
    -c ${DATA_TEST}/SYNTHESIS/synthesis_configuration.json
    -o ${OUTPUT_TEST}/SNOW_SYNTHESIS_MUSCATE
    )
  set_tests_properties(snow_synthesis_muscate_test PROPERTIES TIMEOUT 3000)
endif()

add_test(NAME snow_synthesis_without_densification_test
  COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/app/let_it_snow_synthesis.py
  -t T31TCH
  -i ${DATA_TEST}/SNOW_PRODUCTS/SENTINEL2A_20180101-105435-457_L2A_T31TCH_D_V1-4
  -i ${DATA_TEST}/SNOW_PRODUCTS/SENTINEL2A_20180131-105416-437_L2A_T31TCH_D_V1-4
  -b 01/01/2018
  -e 31/01/2018
  -m 10
  -l DEBUG
  -c ${DATA_TEST}/SYNTHESIS/synthesis_configuration.json
  -o ${OUTPUT_TEST}/SNOW_SYNTHESIS_WITHOUT_DENSIFICATION
  )


if(NOT GITLAB_CI_BUILD MATCHES "true")
  # ----------------------------------
  # Synthesis from 1.7 snow product
  # ----------------------------------
  add_test(NAME synthesis_from_l2A_S2_20180101
    COMMAND ${PYTHON_EXECUTABLE}
    ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
    -c ${DATA_TEST}/L2A_PRODUCTS/lis_configuration.json
    -i ${DATA_TEST}/L2A_PRODUCTS/SENTINEL2A_20180101-105435-457_L2A_T31TCH_C_V2-2
    -d "/work/datalake/static_aux/MNT/Copernicus_DSM/world.vrt"
    -t "/work/datalake/static_aux/TreeCoverDensity/31TCH/TCD_31TCH.tif"
    -w "/work/datalake/static_aux/MASQUES/eu_hydro/raster/20m/31TCH/eu_hydro_20m_31TCH.tif"
    -o ${OUTPUT_TEST}/SNOW_PRODUCTS/SENTINEL2A_20180101-105435-457_L2A_T31TCH_C_V2-2
    )

  add_test(NAME synthesis_from_l2A_S2_20180131
    COMMAND ${PYTHON_EXECUTABLE}
    ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
    -c ${DATA_TEST}/L2A_PRODUCTS/lis_configuration.json
    -i ${DATA_TEST}/L2A_PRODUCTS/SENTINEL2A_20180131-105416-437_L2A_T31TCH_C_V2-2
    -d "/work/datalake/static_aux/MNT/Copernicus_DSM/world.vrt"
    -t "/work/datalake/static_aux/TreeCoverDensity/31TCH/TCD_31TCH.tif"
    -w "/work/datalake/static_aux/MASQUES/eu_hydro/raster/20m/31TCH/eu_hydro_20m_31TCH.tif"
    -o ${OUTPUT_TEST}/SNOW_PRODUCTS/SENTINEL2A_20180131-105416-437_L2A_T31TCH_C_V2-2
    )

  add_test(NAME synthesis_from_l2A_L8_20180115
    COMMAND ${PYTHON_EXECUTABLE}
    ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
    -c ${DATA_TEST}/L2A_PRODUCTS/lis_configuration.json
    -i ${DATA_TEST}/L2A_PRODUCTS/LANDSAT8-OLITIRS-XS_20180115-103629-617_L2A_T31TCH_D_V1-9
    -d "/work/datalake/static_aux/MNT/Copernicus_DSM/world.vrt"
    -t "/work/datalake/static_aux/TreeCoverDensity/31TCH/TCD_31TCH.tif"
    -o ${OUTPUT_TEST}/SNOW_PRODUCTS/LANDSAT8-OLITIRS-XS_20180115-103629-617_L2A_T31TCH_D_V1-9
    -l "DEBUG"
    )

  add_test(NAME synthesis_from_l2A_L8_20180131
    COMMAND ${PYTHON_EXECUTABLE}
    ${CMAKE_BINARY_DIR}/app/let_it_snow_fsc.py
    -c ${DATA_TEST}/L2A_PRODUCTS/lis_configuration.json
    -i ${DATA_TEST}/L2A_PRODUCTS/LANDSAT8-OLITIRS-XS_20180131-103619-890_L2A_T31TCH_D_V1-9
    -d "/work/datalake/static_aux/MNT/Copernicus_DSM/world.vrt"
    -t "/work/datalake/static_aux/TreeCoverDensity/31TCH/TCD_31TCH.tif"
    -o ${OUTPUT_TEST}/SNOW_PRODUCTS/LANDSAT8-OLITIRS-XS_20180131-103619-890_L2A_T31TCH_D_V1-9
    -l "DEBUG"
    )

  add_test(NAME snow_synthesis_from_last_version_test
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/app/let_it_snow_synthesis.py
    -i ${OUTPUT_TEST}/SNOW_PRODUCTS/SENTINEL2A_20180101-105435-457_L2A_T31TCH_C_V2-2
    -i ${OUTPUT_TEST}/SNOW_PRODUCTS/SENTINEL2A_20180131-105416-437_L2A_T31TCH_C_V2-2
    -d ${OUTPUT_TEST}/SNOW_PRODUCTS/LANDSAT8-OLITIRS-XS_20180115-103629-617_L2A_T31TCH_D_V1-9
    -d ${OUTPUT_TEST}/SNOW_PRODUCTS/LANDSAT8-OLITIRS-XS_20180131-103619-890_L2A_T31TCH_D_V1-9
    -c ${DATA_TEST}/SYNTHESIS/synthesis_configuration.json
    -j ${DATA_TEST}/SYNTHESIS/synthesis_launch.json
    -o ${OUTPUT_TEST}/SNOW_SYNTHESIS_FROM_LAST_VERSION
    -l "DEBUG"
    )
  set_tests_properties(snow_synthesis_from_last_version_test PROPERTIES DEPENDS synthesis_from_l2A_L8_20180131)
  set_tests_properties(snow_synthesis_from_last_version_test PROPERTIES DEPENDS synthesis_from_l2A_L8_20180115)
  set_tests_properties(snow_synthesis_from_last_version_test PROPERTIES DEPENDS synthesis_from_l2A_S2_20180131)
  set_tests_properties(snow_synthesis_from_last_version_test PROPERTIES DEPENDS synthesis_from_l2A_S2_20180101)

  # ----------------------------------
  # Synthesis with zip files
  # ----------------------------------
  add_test(NAME snow_synthesis_with_zip
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/app/let_it_snow_synthesis.py
    -t T31TCH
    -i ${DATA_TEST}/SNOW_PRODUCTS/SENTINEL2A_20170910-104212-297_L2B-SNOW_T31TCH_D_V1-7
    -i ${DATA_TEST}/SNOW_PRODUCTS/SENTINEL2A_20170913-105335-667_L2B-SNOW_T31TCH_D_V1-7
    -d ${DATA_TEST}/SNOW_PRODUCTS/LANDSAT8-OLITIRS-XS_20170916-104232-708_L2B-SNOW_T31TCH_D_V1-6
    -d ${DATA_TEST}/SNOW_PRODUCTS/LANDSAT8-OLITIRS-XS_20171002-104239-944_L2B-SNOW_T31TCH_D_V1-6
    -b 01/09/2017
    -e 31/10/2017
    -m 10
    -l INFO
    -c ${DATA_TEST}/SYNTHESIS/synthesis_configuration.json
    -o ${OUTPUT_TEST}/SNOW_SYNTHESIS_WITH_ZIP
    )

  # ---------------------------------------
  # Synthesis with Copernicus snow products
  # ---------------------------------------
  add_test(NAME snow_synthesis_with_cosims_snow_products
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/app/let_it_snow_synthesis.py
    -t T31TCH
    -i ${DATA_TEST}/SNOW_PRODUCTS/FSC_20200308T104911_S2A_T31TCH_V100_1
    -i ${DATA_TEST}/SNOW_PRODUCTS/FSC_20200321T105909_S2A_T31TCH_V100_1
    -i ${DATA_TEST}/SNOW_PRODUCTS/FSC_20200326T105910_S2B_T31TCH_V100_1
    -i ${DATA_TEST}/SNOW_PRODUCTS/FSC_20200328T104911_S2A_T31TCH_V100_1
    -i ${DATA_TEST}/SNOW_PRODUCTS/FSC_20200405T105909_S2B_T31TCH_V100_1
    -b 01/03/2020
    -e 10/04/2020
    -m 2
    -l INFO
    -c ${DATA_TEST}/SYNTHESIS/synthesis_cosims_configuration.json
    -o ${OUTPUT_TEST}/SNOW_SYNTHESIS_WITH_COSIMS_SNOW_PRODUCTS
    )

  # ----------------------------------
  # Synthesis with H2 snow products
  # ----------------------------------
  add_test(NAME snow_synthesis_with_h2_snow_products
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/app/let_it_snow_synthesis.py
    -t T32TLQ
    -i ${DATA_TEST}/SNOW_PRODUCTS/LIS_S2-SNOW-FSC_T32TLQ_20220203T103832_2-0_14
    -i ${DATA_TEST}/SNOW_PRODUCTS/LIS_S2-SNOW-FSC_T32TLQ_20220205T102830_2-0_01
    -i ${DATA_TEST}/SNOW_PRODUCTS/LIS_S2-SNOW-FSC_T32TLQ_20220208T103827_2-0_01
    -i ${DATA_TEST}/SNOW_PRODUCTS/LIS_S2-SNOW-FSC_T32TLQ_20220210T102834_2-0_02
    -b 21/01/2022
    -e 19/02/2022
    -m 2
    -l INFO
    -c ${DATA_TEST}/SYNTHESIS/synthesis_h2_configuration.json
    -o ${OUTPUT_TEST}/SNOW_SYNTHESIS_WITH_H2_SNOW_PRODUCTS
    )
endif()

ADD_EXECUTABLE(histo_utils_snowline_internal_test histo_utils_snowline_internal_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_snowline_internal_test histo_utils)

ADD_EXECUTABLE(histo_utils_snow_fraction_test histo_utils_snow_fraction_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_snow_fraction_test histo_utils)

add_test(NAME histo_utils_snowline_internal_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_snowline_internal_test
  0
  100
  20
  0.1
  0
  0
  -2
  -10
  "${BASELINE}/histogram_highcloud.txt"
  40
  )
add_test(NAME histo_utils_snowline_reverse_internal_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_snowline_internal_test
  0
  100
  20
  0.99
  0
  1
  0
  0
  "${BASELINE}/histogram_reverse_highcloud.txt"
  90
  )

add_test(NAME histo_utils_snow_fraction_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_snow_fraction_test
  "${OUTPUT_TEST}/histo_utils_snow_fraction_test.tif"
  11
  )

ADD_EXECUTABLE(itkUnaryCloudMaskImageFilterTest itkUnaryCloudMaskImageFilterTest.cxx)
TARGET_LINK_LIBRARIES(itkUnaryCloudMaskImageFilterTest histo_utils)

add_test(NAME TvitkUnaryCloudMaskImageFilterTest
  COMMAND ${CMAKE_BINARY_DIR}/bin/itkUnaryCloudMaskImageFilterTest
  192
  192
  1)

add_test(NAME TvitkUnaryCloudMaskImageFilterTest2
  COMMAND ${CMAKE_BINARY_DIR}/bin/itkUnaryCloudMaskImageFilterTest
  64
  192
  1
  )

add_test(NAME TvitkUnaryCloudMaskImageFilterTest3
  COMMAND ${CMAKE_BINARY_DIR}/bin/itkUnaryCloudMaskImageFilterTest
  2
  4
  0
  )
