#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import os
import unittest
import sys
import shutil

from s2snow.lis_constant import SLOPE_MASK, DEM_RESAMPLED, NO_DATA_MASK, N_GREEN, N_SWIR, SNOW_PASS1, SNOW_PASS2, \
    SNOW_PASS2_VEC, SNOW_PASS3, SNOW_MASK, MISSION_S2, MODE_SENTINEL2, SNOW_VEC
from s2snow.snow_detector import manage_slope_mask, manage_dem, initialize_no_data_mask, \
    compute_snow_pass1, remove_snow_inside_cloud, compute_snow_pass2, compute_snow_pass2_vec, compute_snow_pass3, \
    compute_final_mask, compute_final_fsc_name, compute_final_snow_vec


class MyTestCase(unittest.TestCase):

    def __init__(self, testname, data_test, unit_test, output_dir):
        super(MyTestCase, self).__init__(testname)
        self.data_test = data_test
        self.unit_test = unit_test + "snow_detector_test/"
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def test_manage_slope_mask(self):
        div_slope_threshold = 2
        div_mask = self.data_test + "SENTINEL2A_20210415-105910-624_L2A_T30TYN_C_V2-2/MASKS/" \
                                    "SENTINEL2A_20210415-105910-624_L2A_T30TYN_C_V2-2_MG2_R2.tif"
        slope_mask = manage_slope_mask(div_mask, div_slope_threshold, self.output_dir)
        self.assertTrue(SLOPE_MASK in slope_mask)
        self.assertTrue(self.output_dir in slope_mask)
        self.assertTrue(os.path.exists(slope_mask))

    def test_manage_dem(self):
        img_vrt = self.unit_test + "lis.vrt"
        dem_path = "/work/datalake/static_aux/MNT/Copernicus_DSM/world_absolute_paths.vrt"
        do_preprocessing = False

        dem = manage_dem(img_vrt, dem_path, output_dir, do_preprocessing)
        self.assertEqual(dem_path, dem)

        do_preprocessing = True

        dem = manage_dem(img_vrt, dem_path, output_dir, do_preprocessing)
        self.assertTrue(DEM_RESAMPLED in dem)
        self.assertTrue(self.output_dir in dem)
        self.assertTrue(os.path.exists(dem))

    def test_initialize_no_data_mask(self):
        img_vrt = self.unit_test + "lis.vrt"

        no_data_mask = initialize_no_data_mask(img_vrt, output_dir)
        self.assertTrue(NO_DATA_MASK in no_data_mask)
        self.assertTrue(output_dir in no_data_mask)
        self.assertTrue(os.path.exists(no_data_mask))

    def test_compute_snow_pass1(self):
        img_vrt = self.unit_test + "lis.vrt"
        all_cloud_mask_file = self.unit_test + "all_cloud_mask.tif"
        ndsi_formula = "(im1b" + str(N_GREEN) + "-im1b" + str(N_SWIR) + \
                       ")/(im1b" + str(N_GREEN) + "+im1b" + str(N_SWIR) + ")"
        ndsi_pass1 = 0.4
        red_pass1 = 200
        pass_file_1 = compute_snow_pass1(img_vrt, all_cloud_mask_file,
                                         self.output_dir, ndsi_formula, ndsi_pass1, red_pass1)
        self.assertTrue(SNOW_PASS1 in pass_file_1)
        self.assertTrue(output_dir in pass_file_1)
        self.assertTrue(os.path.exists(pass_file_1))

    def test_remove_snow_inside_cloud(self):
        snow_mask_file_src = self.unit_test + "snow_pass1.tif"
        cloud_mask_file_src = self.unit_test + "cloud_pass1.tif"
        shutil.copy2(snow_mask_file_src, self.output_dir)
        shutil.copy2(cloud_mask_file_src, self.output_dir)
        snow_mask_file = self.output_dir + "snow_pass1.tif"
        cloud_mask_file = self.output_dir + "cloud_pass1.tif"
        remove_snow_inside_cloud(snow_mask_file, cloud_mask_file)
        self.assertTrue(os.path.exists(cloud_mask_file))

    def test_compute_snow_pass2(self):
        img_vrt = self.unit_test + "lis.vrt"
        dem_path = "/work/datalake/static_aux/MNT/Copernicus_DSM/world_absolute_paths.vrt"
        dem = manage_dem(img_vrt, dem_path, output_dir, True)
        cloud_refine_file = self.unit_test + "cloud_refine.tif"
        ndsi_formula = "(im1b" + str(N_GREEN) + "-im1b" + str(N_SWIR) + \
                       ")/(im1b" + str(N_GREEN) + "+im1b" + str(N_SWIR) + ")"
        ndsi_pass2 = 0.15
        red_pass2 = 40
        zs = -1000
        snow_pass_2 = compute_snow_pass2(img_vrt, dem, cloud_refine_file, self.output_dir, ndsi_formula, ndsi_pass2,
                                         red_pass2, zs)
        self.assertTrue(SNOW_PASS2 in snow_pass_2)
        self.assertTrue(self.output_dir in snow_pass_2)
        self.assertTrue(os.path.exists(snow_pass_2))

    def test_compute_snow_pass2_vec(self):
        snow_pass2_file = self.unit_test + SNOW_PASS2
        generate_intermediate_vectors = True
        use_gdal_trace_outline = True
        gdal_trace_outline_min_area = 0
        gdal_trace_outline_dp_toler = 0
        snow_pass2_vec = compute_snow_pass2_vec(snow_pass2_file, self.output_dir, generate_intermediate_vectors,
                                                use_gdal_trace_outline, gdal_trace_outline_min_area,
                                                gdal_trace_outline_dp_toler)
        self.assertTrue(SNOW_PASS2_VEC in snow_pass2_vec)
        self.assertTrue(self.output_dir in snow_pass2_vec)
        self.assertTrue(os.path.exists(snow_pass2_vec))

    def test_compute_snow_pass3(self):
        snow_pass1_file = self.unit_test + "snow_pass1.tif"
        snow_pass2_file = self.unit_test + SNOW_PASS2
        snow_pass_3 = compute_snow_pass3(snow_pass1_file, snow_pass2_file, self.output_dir)
        self.assertTrue(SNOW_PASS3 in snow_pass_3)
        self.assertTrue(self.output_dir in snow_pass_3)
        self.assertTrue(os.path.exists(snow_pass_3))

    def test_compute_final_mask(self):
        cloud_refine_file = self.unit_test + "cloud_refine.tif"
        generic_snow_path = self.unit_test + "snow_pass3.tif"
        mask_back_to_cloud_file = self.unit_test + "mask_back_to_cloud.tif"
        no_data_mask_file = self.unit_test + "no_data_mask.tif"
        strict_cloud_mask = False
        final_mask = compute_final_mask(cloud_refine_file, generic_snow_path, mask_back_to_cloud_file,
                                        no_data_mask_file, self.output_dir,
                                        strict_cloud_mask, mode=MODE_SENTINEL2, ram=512)
        self.assertTrue(SNOW_MASK in final_mask)
        self.assertTrue(self.output_dir in final_mask)
        self.assertTrue(os.path.exists(final_mask))

    def test_compute_final_snow_vec(self):
        final_mask_file = self.unit_test + SNOW_MASK
        generate_vector = True
        use_gdal_trace_outline = True
        gdal_trace_outline_min_area = 0
        gdal_trace_outline_dp_toler = 0
        final_mask_vec = compute_final_snow_vec(final_mask_file, self.output_dir, generate_vector,
                                                use_gdal_trace_outline, gdal_trace_outline_min_area,
                                                gdal_trace_outline_dp_toler)
        self.assertTrue(SNOW_VEC in final_mask_vec)
        self.assertTrue(self.output_dir in final_mask_vec)
        self.assertTrue(os.path.exists(final_mask_vec))

    def test_compute_final_fsc_name(self):
        chain_version = "1.8"
        mission = MISSION_S2
        tile_id = "T31TCH"
        acquisition_date = "20210910"
        product_counter = "001"
        name = compute_final_fsc_name(mission, tile_id, acquisition_date, chain_version, product_counter)
        self.assertEqual(name, "LIS_S2-SNOW-FSC_T31TCH_20210910_1.8_001.tif")
        is_toc = True
        name = compute_final_fsc_name(mission, tile_id, acquisition_date, chain_version, product_counter, is_toc=is_toc)
        self.assertEqual(name, "LIS_S2-SNOW-FSC-TOC_T31TCH_20210910_1.8_001.tif")
        is_qcflags = True
        name = compute_final_fsc_name(mission, tile_id, acquisition_date, chain_version, product_counter,
                                      is_qcflags=is_qcflags)
        self.assertEqual(name, "LIS_S2-SNOW-FSC-QCFLAGS_T31TCH_20210910_1.8_001.tif")


if __name__ == '__main__':
    data_test = sys.argv[1]
    unit_test = sys.argv[2]
    output_dir = sys.argv[3]

    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(MyTestCase)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(MyTestCase(test_name, data_test, unit_test, output_dir))

    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())

