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

from s2snow.cloud_extraction import refine_cloud_mask, extract_all_clouds, extract_cloud_shadows, extract_high_clouds, \
    extract_back_to_cloud_mask
from s2snow.lis_constant import CLOUD_REFINE, ALL_CLOUD_MASK, SHADOW_MASK, HIGH_CLOUD_MASK, MASK_BACK_TO_CLOUD


class MyTestCase(unittest.TestCase):

    def __init__(self, testname, data_test, unit_test, output):
        super(MyTestCase, self).__init__(testname)
        self.data_test = data_test
        self.unit_test = unit_test + "cloud_extraction_test/"
        self.output = output
        if not os.path.exists(self.output):
            os.makedirs(self.output)

    def test_extract_all_clouds(self):
        cloud_mask = self.data_test + "SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0/MASKS/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0_CLM_R2.tif"
        all_cloud_mask_file = extract_all_clouds(cloud_mask, self.output)
        self.assertTrue(ALL_CLOUD_MASK in all_cloud_mask_file)
        self.assertTrue(self.output in all_cloud_mask_file)
        self.assertTrue(os.path.exists(all_cloud_mask_file))

    def test_extract_cloud_shadows(self):
        cloud_mask = self.data_test + "SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0/MASKS/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0_CLM_R2.tif"
        shadow_mask_file = extract_cloud_shadows(cloud_mask, self.output)
        self.assertTrue(SHADOW_MASK in shadow_mask_file)
        self.assertTrue(self.output in shadow_mask_file)
        self.assertTrue(os.path.exists(shadow_mask_file))

    def test_extract_high_clouds(self):
        cloud_mask_file = self.data_test + "SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0/MASKS/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0_CLM_R2.tif"
        high_clouds_mask = extract_high_clouds(cloud_mask_file, self.output)
        self.assertTrue(HIGH_CLOUD_MASK in high_clouds_mask)
        self.assertTrue(self.output in high_clouds_mask)
        self.assertTrue(os.path.exists(high_clouds_mask))

    def test_extract_back_to_cloud_mask(self):
        cloud_mask_file = self.data_test + "SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0/MASKS/SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0_CLM_R2.tif"
        red_band_file = self.unit_test + "red.tif"
        back_t_cloud_mask = extract_back_to_cloud_mask(cloud_mask_file, red_band_file, self.output)
        self.assertTrue(MASK_BACK_TO_CLOUD in back_t_cloud_mask)
        self.assertTrue(self.output in back_t_cloud_mask)
        self.assertTrue(os.path.exists(back_t_cloud_mask))

    def test_refine_cloud_mask(self):
        all_cloud_mask_file = self.unit_test + "all_cloud_mask.tif"
        shadow_mask_file = self.unit_test + "shadow_mask.tif"
        red_nn_file = self.unit_test + "red_nn.tif"
        high_cloud_mask_file = self.unit_test + "high_cloud_mask.tif"
        cloud_pass1_file = self.unit_test + "snow_pass1.tif"
        cloud_refine_file = refine_cloud_mask(all_cloud_mask_file, shadow_mask_file, red_nn_file, high_cloud_mask_file,
                                              cloud_pass1_file, self.output)
        self.assertTrue(CLOUD_REFINE in cloud_refine_file)
        self.assertTrue(self.output in cloud_refine_file)
        self.assertTrue(os.path.exists(cloud_refine_file))


if __name__ == '__main__':
    data_test = sys.argv[1]
    unit_test = sys.argv[2]
    output = sys.argv[3]

    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(MyTestCase)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(MyTestCase(test_name, data_test, unit_test, output))

    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
