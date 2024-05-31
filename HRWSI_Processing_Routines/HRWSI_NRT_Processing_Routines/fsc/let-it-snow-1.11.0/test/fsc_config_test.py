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


class MyTestCase(unittest.TestCase):

    def __init__(self, testname, data_test, unit_test, output):
        super(MyTestCase, self).__init__(testname)
        self.data_test = data_test
        self.unit_test = unit_test + "fsc_config_test/"
        self.output = output
        if not os.path.exists(self.output):  
            os.makedirs(self.output)   
          


    def test_load_metadata_from_input_dir(self):
        config_file = self.unit_test + "lis_configuration.json"
        with open(config_file) as json_data_file:
            data = json.load(json_data_file)
            input_dir = self.data_test + "SENTINEL2A_20210415-105910-624_L2A_T30TYN_C_V2-2"
            config = FscConfig(data, input_dir, None, None, None)
            self.assertIsNotNone(config.metadata)
            self.assertTrue(input_dir in config.metadata)
            self.assertTrue(os.path.exists(config.metadata))
    
    def test_load_metadata_from_configuration(self):
        config_file = self.unit_test + "lis_configuration_metadata_overriden.json"
        with open(config_file) as json_data_file:
            data = json.load(json_data_file)
            input_dir = self.data_test + "SENTINEL2A_20210415-105910-624_L2A_T30TYN_C_V2-2"
            config = FscConfig(data, input_dir, None, None, None)
            self.assertIsNotNone(config.metadata)
            self.assertTrue(input_dir not in config.metadata)
            self.assertTrue("SENTINEL2A_20160217-111843-605_L2A_T29RNQ_D_V1-0_MTD_ALL.xml" in config.metadata)
            self.assertTrue(os.path.exists(config.metadata))