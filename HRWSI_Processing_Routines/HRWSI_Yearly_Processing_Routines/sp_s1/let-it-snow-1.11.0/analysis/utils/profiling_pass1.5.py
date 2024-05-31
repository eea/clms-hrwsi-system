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

from __future__ import print_function
import os
import sys
import argparse
from s2snow import snow_detector
import json

def main(argv):

    print(argv)

    json_file = argv[0]
    snow_mask = argv[1]
    cloud_mask = argv[2]
    
    # Load json_file from json files
    with open(json_file) as json_data_file:
        data = json.load(json_data_file)
    
    #dummy json
    sd = snow_detector.snow_detector(data)

    #
    sd.pass1_5(snow_mask, cloud_mask, 1, 0.85)
    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
