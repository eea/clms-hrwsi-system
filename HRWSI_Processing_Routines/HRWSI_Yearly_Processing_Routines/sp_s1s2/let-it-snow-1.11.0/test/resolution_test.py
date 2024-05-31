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

from osgeo import gdal

from s2snow.lis_constant import GREEN, BAND_RESAMPLED, BAND_EXTRACTED
from s2snow.resolution import adapt_to_target_resolution, define_band_resolution

class MyTestCase(unittest.TestCase):

    def __init__(self, testname, unit_test, output_dir):
        super(MyTestCase, self).__init__(testname)
        self.unit_test = unit_test + "resolution_test/"
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    def test_define_band_resolution(self):
        green_extracted_band = self.unit_test + "green_band_extracted.tif"
        gr_resolution = define_band_resolution(green_extracted_band)
        self.assertTrue(gr_resolution != 0)
        self.assertTrue(gr_resolution is not None)
        self.assertTrue(gr_resolution == 10.0)

        red_extracted_band = self.unit_test + "red_band_extracted.tif"
        red_resolution = define_band_resolution(red_extracted_band)
        self.assertTrue(red_resolution != 0)
        self.assertTrue(red_resolution is not None)
        self.assertTrue(red_resolution == 10.0)

        swir_extracted_band = self.unit_test + "swir_band_extracted.tif"
        swir_resolution = define_band_resolution(swir_extracted_band)
        self.assertTrue(swir_resolution != 0)
        self.assertTrue(swir_resolution is not None)
        self.assertTrue(swir_resolution == 20.0)


    def test_adapt_to_target_resolution(self):
        resolution = 10.0
        target_resolution = resolution
        band_extracted_file = "test"
        green_band_resampled = adapt_to_target_resolution(GREEN, resolution, target_resolution, band_extracted_file,
                                                          self.output_dir)
        self.assertEqual(green_band_resampled, band_extracted_file)

        target_resolution = 120
        band_extracted_file = self.unit_test + "green_band_extracted.tif"
        green_band_resampled = adapt_to_target_resolution(GREEN, resolution, target_resolution, band_extracted_file,
                                                          self.output_dir)
        self.assertTrue(GREEN in green_band_resampled)
        self.assertTrue(BAND_RESAMPLED in green_band_resampled)
        self.assertTrue(self.output_dir in green_band_resampled)
        self.assertTrue(os.path.exists(green_band_resampled))
        gr_resolution = define_band_resolution(green_band_resampled)
        self.assertTrue(gr_resolution == 120)


if __name__ == '__main__':
    unit_test = sys.argv[1]
    output_dir = sys.argv[2]

    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(MyTestCase)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(MyTestCase(test_name, unit_test, output_dir))

    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
