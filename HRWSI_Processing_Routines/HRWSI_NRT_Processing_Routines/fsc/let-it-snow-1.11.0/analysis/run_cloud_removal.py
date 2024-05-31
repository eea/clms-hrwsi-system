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

import sys
import os.path as op
import json
import logging
from analysis import cloud_removal
from importlib.metadata import version

def show_help():
    """Show help of the run_cloud_removal script"""
    print("Usage: python run_cloud_removal.py param.json")
    print("python run_cloud_removal.py version to show version")
    print("python run_cloud_removal.py help to show help")

def show_version():
    print(version('s2snow'))

#----------------- MAIN ---------------------------------------------------

def main(argv):
    """ main script of snow extraction procedure"""

    json_file=argv[1]

    #load json_file from json files
    with open(json_file) as json_data_file:
      data = json.load(json_data_file)
    
    general = data["general"]
    pout = general.get("pout")
    
    log = general.get("log", True)
    if log:
        sys.stdout = open(op.join(pout, "stdout.log"), 'w')
        sys.stderr = open(op.join(pout, "stderr.log"), 'w')

    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, \
                        format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    logging.info("Start run_cloud_removal.py")
    logging.info("Input args = " + json_file)

    # Run the cloud removal
    cloud_removal.run(data)
    logging.info("End run_cloud_removal.py")
      
if __name__ == "__main__":
    if len(sys.argv) != 2 :
        show_help()
    else:
        if sys.argv[1] == "version":
            show_version()
        elif sys.argv[1] == "help":
            show_help()
        else:
            main(sys.argv)
