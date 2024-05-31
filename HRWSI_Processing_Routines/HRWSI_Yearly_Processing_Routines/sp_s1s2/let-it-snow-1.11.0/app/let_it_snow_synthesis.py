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
import logging
import os
import sys
import json
from logging.handlers import RotatingFileHandler

from s2snow.lis_exception import LisConfigurationException, NoSnowProductFound, NoZipFound, NoProductMatchingSynthesis, \
    UnknownPlatform
from s2snow.snow_synthesis import compute_snow_synthesis
from s2snow.synthesis_config import SynthesisConfig
from s2snow.lis_constant import INPUT_PARAMETER_ERROR, CONFIGURATION_ERROR, TMP_DIR, LOG_FILE, NO_SNOW_PRODUCT_FOUND, \
    NO_ZIP_FOUND, NO_PRODUCT_MATCHING_SYNTHESIS, UNKNOWN_PLATFORM, OUTPUT_UNDEFINED
from s2snow.parser import create_synthesis_argument_parser


def main(args):
    if args.json_config_file is not None:
        with open(args.json_config_file) as json_config_file:
            global_config = json.load(json_config_file)
            tile_id = global_config.get("tile_id", None)
            input_products_list = global_config.get("input_products_list", None)
            densification_products_list = global_config.get("densification_products_list", None)
            output_dir = global_config.get("output_dir", None)
            date_start = global_config.get("date_start", None)
            date_stop = global_config.get("date_stop", None)
            date_margin = global_config.get("date_margin", None)
            log_level = global_config.get("log_level", "INFO")
            config_file = global_config.get("config_file", None)
            h2_chain_version = global_config.get("chain_version", None)
            product_counter = global_config.get("product_counter", "1")
    else:
        tile_id = None
        input_products_list = None
        densification_products_list = None
        output_dir = None
        config_file = None
        date_start = None
        date_stop = None
        date_margin = None
        h2_chain_version = None
        product_counter = None
        log_level = None

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
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d    %(levelname)s:%(filename)s:line=%(lineno)s:%(funcName)s:%(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logging.debug("Debug level activated.")
    logging.info("output directory : %s", output_dir)

    if args.tile_id is not None:
        logging.info("input products : %s", args.tile_id)
        tile_id = args.tile_id
    if args.input_products_list is not None:
        logging.info("input products : %s", args.input_products_list)
        input_products_list = args.input_products_list
    if args.config_file is not None:
        logging.info("configuration file : %s", args.config_file)
        config_file = args.config_file
    if args.date_start is not None:
        logging.info("date_start : %s", args.date_start)
        date_start = args.date_start
    if args.date_stop is not None:
        logging.info("date_stop : %s", args.date_stop)
        date_stop = args.date_stop
    if args.date_margin is not None:
        logging.info("date_margin : %s", args.date_margin)
        date_margin = args.date_margin
    if args.densification_products_list is not None:
        logging.info("input densification_products_list : %s", args.densification_products_list)
        densification_products_list = args.densification_products_list
    if args.chain_version is not None:
        logging.info("chain version : %s", args.chain_version)
        h2_chain_version = args.chain_version
    if args.product_counter is not None:
        logging.info("product counter: %s", args.product_counter)
        product_counter = args.product_counter

    let_it_snow_synthesis(config_file, tile_id, input_products_list, densification_products_list, output_dir,
                                 date_start, date_stop, date_margin, h2_chain_version, product_counter)


def let_it_snow_synthesis(config_file, tile_id, input_products_list, densification_products_list, output_dir,
                          date_start, date_stop, date_margin,
                          h2_chain_version=None, product_counter=None):
    # Check configuration file
    if not os.path.exists(config_file):
        logging.error("Configuration file does not exist.")
        sys.exit(INPUT_PARAMETER_ERROR)

    # Load json_file from json files
    with open(config_file) as json_data_file:
        data = json.load(json_data_file)
        logging.info("Reading configuration = " + config_file)
        try:
            config = SynthesisConfig(data, tile_id, input_products_list, date_start, date_stop, date_margin=date_margin,
                                     densification_products_list=densification_products_list)
            config.dump_configuration(output_dir, config_file,
                                      logging.getLevelName(logging.getLogger().getEffectiveLevel()), h2_chain_version,
                                      product_counter)
        except LisConfigurationException:
            sys.exit(CONFIGURATION_ERROR)
        except IOError:
            sys.exit(INPUT_PARAMETER_ERROR)

    # Run the snow detector
    try:
        logging.info("Launch snow synthesis computation.")
        compute_snow_synthesis(config, output_dir, h2_chain_version, product_counter)
    except UnknownPlatform as e:
        logging.error(str(e))
        sys.exit(UNKNOWN_PLATFORM)
    except NoProductMatchingSynthesis as e:
        logging.error(str(e))
        sys.exit(NO_PRODUCT_MATCHING_SYNTHESIS)
    except NoSnowProductFound as e:
        logging.error(str(e))
        sys.exit(NO_SNOW_PRODUCT_FOUND)
    except NoZipFound as e:
        logging.error(str(e))
        sys.exit(NO_ZIP_FOUND)
    except Exception as e:
        logging.error(str(e))
        sys.exit(-1)

    sys.exit(0)


if __name__ == "__main__":
    args_parser = create_synthesis_argument_parser()
    args = args_parser.parse_args(sys.argv[1:])
    main(args)
