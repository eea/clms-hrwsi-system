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
import sys
import unittest

from s2snow.gdal_wrappers import extract_band, extract_red_band, resample_red_band, resample_red_band_nn, \
    extract_red_nn, initialize_vrt
from s2snow.lis_constant import GREEN, BAND_EXTRACTED, RED_BAND, RED_COARSE, RED_NN, RED, SWIR, IMG_VRT


class MyTestCase(unittest.TestCase):

    def __init__(self, testname, data_test, unit_test, output_dir):
        super(MyTestCase, self).__init__(testname)
        self.data_test = data_test
        self.unit_test = unit_test + "gdal_wrappers_test/"
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def test_extract_band(self):
        band_path = self.data_test + "SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0_FRE_B3.tif"
        band_name = GREEN
        no_band = 1
        green_extracted_band_file = extract_band(band_name, band_path, no_band, self.output_dir)
        self.assertTrue(GREEN in green_extracted_band_file)
        self.assertTrue(BAND_EXTRACTED in green_extracted_band_file)
        self.assertTrue(self.output_dir in green_extracted_band_file)
        self.assertTrue(os.path.exists(green_extracted_band_file))

        band_name = RED
        red_extracted_band_file = extract_band(band_name, band_path, no_band, self.output_dir)
        self.assertTrue(RED in red_extracted_band_file)
        self.assertTrue(BAND_EXTRACTED in red_extracted_band_file)
        self.assertTrue(self.output_dir in red_extracted_band_file)
        self.assertTrue(os.path.exists(red_extracted_band_file))

        band_name = SWIR
        swir_extracted_band_file = extract_band(band_name, band_path, no_band, self.output_dir)
        self.assertTrue(SWIR in swir_extracted_band_file)
        self.assertTrue(BAND_EXTRACTED in swir_extracted_band_file)
        self.assertTrue(self.output_dir in swir_extracted_band_file)
        self.assertTrue(os.path.exists(swir_extracted_band_file))

    def test_extract_red_band(self):
        img_vrt = self.unit_test + "lis.vrt"
        red_band_file = extract_red_band(img_vrt, self.output_dir)
        self.assertTrue(RED_BAND in red_band_file)
        self.assertTrue(self.output_dir in red_band_file)
        self.assertTrue(os.path.exists(red_band_file))

    def test_resample_red_band(self):
        red_band = self.unit_test + RED_BAND
        xSize = 200
        ySize = 200
        red_coarse_file = resample_red_band(red_band, self.output_dir, xSize, ySize)
        self.assertTrue(RED_COARSE in red_coarse_file)
        self.assertTrue(self.output_dir in red_coarse_file)
        self.assertTrue(os.path.exists(red_coarse_file))

    def test_resample_red_band_nn(self):
        red_coarse_file = self.unit_test + RED_COARSE
        xSize = 200
        ySize = 200
        red_nn_file = resample_red_band_nn(red_coarse_file, self.output_dir, xSize, ySize)
        self.assertTrue(RED_NN in red_nn_file)
        self.assertTrue(self.output_dir in red_nn_file)
        self.assertTrue(os.path.exists(red_nn_file))

    def test_extract_red_nn(self):
        red_band_file = self.unit_test + RED_BAND
        red_nn_file = extract_red_nn(red_band_file, self.output_dir)
        self.assertTrue(RED_NN in red_nn_file)
        self.assertTrue(self.output_dir in red_nn_file)
        self.assertTrue(os.path.exists(red_nn_file))

    def test_initialize_vrt(self):
        swir_band_resampled = self.unit_test + "swir_band_extracted.tif"
        red_band_resampled = self.unit_test + "red_band_extracted.tif"
        green_band_resampled = self.unit_test + "green_band_extracted.tif"
        img_vrt = initialize_vrt(swir_band_resampled, red_band_resampled, green_band_resampled, self.output_dir)
        self.assertTrue(IMG_VRT in img_vrt)
        self.assertTrue(self.output_dir in img_vrt)
        self.assertTrue(os.path.exists(img_vrt))


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
