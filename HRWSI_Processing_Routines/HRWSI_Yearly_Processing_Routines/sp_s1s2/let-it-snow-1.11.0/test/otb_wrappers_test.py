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

import unittest
import os
import sys

from s2snow.lis_constant import HISTOGRAM, SNOW_ALL
from s2snow.otb_wrappers import compute_snow_line, compute_snow_mask


class MyTestCase(unittest.TestCase):

    def __init__(self, testname, unit_test, output_dir):
        super(MyTestCase, self).__init__(testname)
        self.unit_test = unit_test + "otb_wrappers_test/"
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def test_compute_snow_line(self):
        img_dem = self.unit_test + "lis.vrt"
        img_snow = self.unit_test + "snow_pass1.tif"
        img_cloud = self.unit_test + "cloud_pass1.tif"
        dz = 100
        fsnowlim = 0.1
        fclearlim = 0.1
        reverse = False
        offset = -2
        center_offset = 50
        outhist = os.path.join(self.output_dir, HISTOGRAM)
        compute_snow_line(img_dem, img_snow, img_cloud, dz, fsnowlim, fclearlim, \
                          reverse, offset, center_offset, outhist)
        self.assertTrue(os.path.exists(outhist))

    def test_compute_snow_mask(self):
        pass1 = self.unit_test + "snow_pass1.tif"
        pass2 = self.unit_test + "snow_pass2.tif"
        cloud_pass1 = self.unit_test + "cloud_pass1.tif"
        cloud_refine = self.unit_test + "cloud_refine.tif"
        initial_clouds = self.unit_test + "all_cloud_mask.tif"
        snow_all_file = os.path.join(self.output_dir, SNOW_ALL)
        compute_snow_mask(pass1, pass2, cloud_pass1, cloud_refine, initial_clouds, snow_all_file)
        self.assertTrue(os.path.exists(snow_all_file))


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
