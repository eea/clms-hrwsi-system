#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Centre National d'Etudes Spatiales (CNES)
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
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from s2snow.snow_detector import detect_snow
from s2snow.fsc_config import (FscConfig, LisConfigurationException,
                               UnknownProductException)
from s2snow.lis_constant import (CONFIGURATION_ERROR, INPUT_PARAMETER_ERROR,
                                 LOG_FILE, OUTPUT_UNDEFINED, TMP_DIR,
                                 UNKNOWN_PRODUCT_EXCEPTION)
from s2snow.parser import create_fsc_argument_parser


def main(args):
    if args.json_config_file is not None:
        with open(args.json_config_file) as json_config_file:
            global_config = json.load(json_config_file)
            input_dir = global_config.get("input_dir", None)
            output_dir = global_config.get("output_dir", None)
            dem = global_config.get("dem", None)
            tcd = global_config.get("tcd", None)
            water_mask = global_config.get("water_mask", None)
            log_level = global_config.get("log", "INFO")
            config_file = global_config.get("config_file", None)
            h2_chain_version = global_config.get("chain_version", None)
            product_counter = global_config.get("product_counter", "1")
            relief_shadow_mask = global_config.get("relief_shadow_mask", None)

    else:
        input_dir = None
        output_dir = None
        config_file = None
        dem = None
        water_mask = None
        tcd = None
        h2_chain_version = None
        product_counter = None
        log_level = None
        relief_shadow_mask = None

    if args.output_dir is not None:
        output_dir = args.output_dir

    if output_dir is None:
        sys.exit(OUTPUT_UNDEFINED)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

        # Create tmp dir
    os.makedirs(output_dir + "/" + TMP_DIR, exist_ok=True)
    tmp_dir = os.path.join(output_dir, TMP_DIR)
    log_file = os.path.join(tmp_dir, LOG_FILE)

    # init logger
    logger = logging.getLogger()
    if args.log_level is not None:
        log_level = args.log_level
    if log_level is None:
        log_level = "INFO"

    level = logging.getLevelName(log_level)
    logger.setLevel(level)

    # file handler
    file_handler = RotatingFileHandler(log_file, 'a', 1000000, 1)
    formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d    %(levelname)s:%(filename)s::%(funcName)s:%(message)s',
                                  datefmt='%Y-%m-%dT%H:%M:%S')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logging.info("output directory : %s", args.output_dir)

    if args.input_dir is not None:
        logging.info("input directory : %s", args.input_dir)
        input_dir = args.input_dir
    if args.config_file is not None:
        logging.info("configuration file : %s", args.config_file)
        config_file = args.config_file
    if args.dem is not None:
        logging.info("dem : %s", args.dem)
        dem = args.dem
    if args.water_mask is not None:
        logging.info("water mask : %s", args.water_mask)
        water_mask = args.water_mask
    if args.tcd is not None:
        logging.info("tree cover density : %s", args.tcd)
        tcd = args.tcd

    if args.relief_shadow_mask is not None:
        logging.info("relief shadow mask : %s", args.relief_shadow_mask)
        relief_shadow_mask = args.relief_shadow_mask

    if args.chain_version is not None:
        logging.info("chain version : %s", args.chain_version)
        h2_chain_version = args.chain_version

    if args.product_counter is not None:
        logging.info("product counter: %s", args.product_counter)
        product_counter = args.product_counter

    let_it_snow_fsc(config_file, input_dir, output_dir, dem, tcd, water_mask, h2_chain_version, product_counter, relief_shadow_mask)


def let_it_snow_fsc(config_file, input_dir, output_dir, dem, tcd, water_mask, h2_chain_version=None,
                    product_counter=None, relief_shadow_mask=None):
    # Check configuration file
    if not os.path.exists(config_file):
        logging.error("Configuration file does not exist.")
        sys.exit(INPUT_PARAMETER_ERROR)

    # Load json_file from json files
    with open(config_file) as json_data_file:
        data = json.load(json_data_file)
        logging.info("Reading configuration = " + config_file)
        try:
            config = FscConfig(data, input_dir, dem, tcd, water_mask, relief_shadow_mask)
            config.dump_configuration(output_dir, config_file, input_dir,
                                      logging.getLevelName(logging.getLogger().getEffectiveLevel()), h2_chain_version,
                                      product_counter)
        except LisConfigurationException:
            sys.exit(CONFIGURATION_ERROR)
        except UnknownProductException:
            sys.exit(UNKNOWN_PRODUCT_EXCEPTION)
        except IOError:
            sys.exit(INPUT_PARAMETER_ERROR)

    if not os.path.exists(output_dir):
        logging.warning("Output directory product does not exist.")
        logging.info("Create directory " + output_dir + "...")
        os.makedirs(output_dir)

    # Run the snow detector
    try:
        logging.info("Launch snow detection.")
        detect_snow(config, output_dir, h2_chain_version, product_counter)
    except Exception as e:
        logging.exception(e)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    args_parser = create_fsc_argument_parser()
    args = args_parser.parse_args(sys.argv[1:])
    main(args)
