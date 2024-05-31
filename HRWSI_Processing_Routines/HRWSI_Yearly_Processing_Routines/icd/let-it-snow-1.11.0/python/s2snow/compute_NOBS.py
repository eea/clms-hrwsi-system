# !/usr/bin/env python
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

import rasterio
import numpy as np
import os, sys
import logging
from importlib.metadata import version


def compute_NOBS(input_file, synthesis_name=None, output_dir=None):
    """
    computes NOBS_xxx.tif, the number of clear observations to compute the SCD, SMOD and SOD syntheses
    :param input_file: the cloud mask vrt generated using run_show_annual_map script, multitemp_cloud_mask.vrt
    :param synthesis_name: synthesis_name
    :param output_dir: outpout directory
    :return:
    """
    logging.debug("compute_NOBS")
    logging.debug("input_file : %s", input_file)
    logging.debug("synthesis_name : %s", synthesis_name)
    logging.debug("output_dir : %s", output_dir)

    if not os.path.isfile(input_file):
        logging.error("Input file does not exist : %s", input_file)
        return

    if output_dir is None:
        output_dir = os.path.split(os.path.split(input_file)[0])[0]
    if synthesis_name is None:
        synthesis_id = os.path.split(output_dir)[1]
        output_file = os.path.join(output_dir, "LIS_SNOW-NOBS_{}.tif".format(synthesis_id))
    else:
        output_file = os.path.join(output_dir, synthesis_name.format("NOBS"))

    src = rasterio.open(input_file, 'r')

    n = src.meta["count"]
    W = src.read(range(1, n + 1))
    S = n - np.sum(W, axis=0)

    with rasterio.Env():
        profile = src.profile
        profile.update(
            dtype=rasterio.uint16,
            driver='GTiff',
            compress='deflate',
            count=1)

        with rasterio.open(output_file, 'w', **profile) as dst:
            dst.write(S.astype(rasterio.uint16), 1)


def show_help():
    """
    Show help for compute_NOBS
    :return:
    """
    print("This script is used to compute NOBS. " \
          + "Input file is the cloud mask vrt generated using run_show_annual_map script, " \
          + "named multitemp_cloud_mask.vrt")
    print("Usage: python compute_NOBS.py nobs_input_file synthesis_id output_dir")
    print("Example: python compute_NOBS.py multitemp_cloud_mask.vrt T31TCH_20160901_20170831 /tmp")
    print("python compute_NOBS.py version to show version")
    print("python compute_NOBS.py help to show help")


def show_version():
    """
    Show LIS version
    :return:
    """
    print("LIS Version : {}".format(version('s2snow')))


def main(argv):
    compute_NOBS(*argv[1:])


if __name__ == "__main__":
    if len(sys.argv) < 1 or len(sys.argv) > 3:
        show_help()
    else:
        if sys.argv[1] == "version":
            show_version()
        elif sys.argv[1] == "help":
            show_help()
        else:
            main(sys.argv)
