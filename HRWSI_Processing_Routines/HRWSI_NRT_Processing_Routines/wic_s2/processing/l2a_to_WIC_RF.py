#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
import logging
import joblib
import numpy as np
import pandas as pd
from osgeo import gdal

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('wic_s2')[:-1])
sys.path.append(ROOT_FOLDER+'wic_s2')
from processing.indices_computation import IndicesComputation
from utils.log_util import LogUtil
from utils.add_colortable import add_wic_colortable, add_proba_colortable
from geometry.combine_bits_geotiff import bit_bandmath
from utils.rewrite_cog import rewrite_cog


LIST_TRAINING_INDICES = ["NDVI", "NDSI", "NDWI", "std_g_blue", "slope", "bounded_b11"]
LIST_TRAINING_INDICES_TYPES = { "NDVI":"int16", "NDSI":"int16", "NDWI":"int16",
                                "std_g_blue":"float32", "slope":"float32", "bounded_b11":"int16"}

def load_configuration(config_json_file):
    """Load configuration from a JSON file."""
    with open(config_json_file, 'r') as f:
        return json.load(f)

def create_dataframe(matrix_of_indices, list_training_indices, list_training_indices_types):
    """Create a DataFrame from matrix of indices."""
    dataframe_indices = pd.DataFrame()
    for i, matrix_generator in enumerate(matrix_of_indices):
        index_matrix = np.array(list(matrix_generator))
        column_name = list_training_indices[i]
        column_dtype = list_training_indices_types.get(column_name)
        dataframe_indices[column_name] = index_matrix.astype(column_dtype)
    return dataframe_indices

def classify_data(classifier, dataframe_indices, batch_size=10000):
    """Classify data using the classifier."""
    predictions = []
    probabilities = []
    num_batches = len(dataframe_indices) // batch_size + 1
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, len(dataframe_indices))
        batch_predictions = classifier.predict(dataframe_indices[start_idx:end_idx].values)
        batch_probabilities = classifier.predict_proba(dataframe_indices[start_idx:end_idx].values)
        predictions.extend(batch_predictions)
        probabilities.extend(batch_probabilities)
    return np.array(predictions), np.array(probabilities)

def get_classifier(classifier_path):
    classifier = joblib.load(classifier_path)
    return classifier

def write_raster(raster, input_image_path, image_name, output_WIC_file):
    IndicesComputer.from_array_to_tif(raster,
                                    os.path.join(input_image_path, image_name + "_FRE_B11.tif"),
                                    output_WIC_file)
    
def change_wic_values(new_WIC_file, WIC_file):
    """Compute macro classes from WIC raster."""
    source_list = [{'sources': [{'filepath': WIC_file,'bandnumber': 1,'unpack_bits': False}], \
                    'operation': 'np.uint8(255)*(A0==255) + np.uint8(254)*(A0==0)+\
                                np.uint8(100)*(A0==1) + np.uint8(1)*(A0==2)'}]
    raster_gdal_info = gdal.Info(WIC_file, format='json')
    bit_bandmath(new_WIC_file, raster_gdal_info, [source_list],
                 no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)

def compute_macro_classes(input_file, output_file):
    """Compute macro classes from WIC raster."""
    source_list = [{'sources': [{'filepath': input_file,'bandnumber': 1,'unpack_bits': False}], \
                    'operation': 'np.uint8(255)*(A0==255) + np.uint8(255)*(A0==0)+\
                                np.uint8(254)*(A0==1) + np.uint8(254)*(A0==2) + np.uint8(254)*(A0==3) +\
                                np.uint8(254)*(A0==4) + np.uint8(254)*(A0==5) + np.uint8(254)*(A0==12) +\
                                np.uint8(254)*(A0==13) + np.uint8(254)*(A0==14) +\
                                np.uint8(100)*(A0==7)+ np.uint8(100)*(A0==10) + np.uint8(100)*(A0==11) +\
                                np.uint8(1)*(A0==6) + np.uint8(1)*(A0==8) + np.uint8(1)*(A0==9)'}]
    raster_gdal_info = gdal.Info(input_file, format='json')
    bit_bandmath(output_file, raster_gdal_info, [source_list],
                 no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)

def add_cloud_mask(output_file, wic_file, cloud_mask):
    """Add cloud mask to wic file."""
    source_list = [{'sources': [{'filepath': cloud_mask,'bandnumber': 1,'unpack_bits': False},
                                {'filepath': wic_file,'bandnumber': 1,'unpack_bits': False}], \
                    'operation': 'np.uint8(205)*(A0!=0) + A1*(A0==0)'}]
    raster_gdal_info = gdal.Info(wic_file, format='json')
    bit_bandmath(output_file, raster_gdal_info, [source_list],
                 no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)

def add_water_mask(output_file, wic_file, water_mask):
    """Add cloud mask to wic file."""
    source_list = [{'sources': [{'filepath': water_mask,'bandnumber': 1,'unpack_bits': False},
                                {'filepath': wic_file,'bandnumber': 1,'unpack_bits': False}], \
                    'operation': 'A1*(A1!=100)*(A0!=253)*(A0!=255) + np.uint8(254)*(A1==100)*(A0==0)+\
                                np.uint8(100)*(A1==100)*(A0==1) + np.uint8(100)*(A1==100)*(A0==2)+\
                                np.uint8(255)*(A0==253) + np.uint8(255)*(A0==255)+\
                                np.uint8(254)*(A1==100)*(A0==254)'}]
    raster_gdal_info = gdal.Info(wic_file, format='json')
    bit_bandmath(output_file, raster_gdal_info, [source_list],
                 no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)

def add_nodata_mask(output_file, wic_file, nodata_mask):
    """Add no data mask to wic file."""
    source_list = [{'sources': [{'filepath': nodata_mask,'bandnumber': 1,'unpack_bits': False},
                                {'filepath': wic_file,'bandnumber': 1,'unpack_bits': False}], \
                    'operation': 'np.uint8(255)*(A0!=0) + A1*(A0==0)'}]
    raster_gdal_info = gdal.Info(wic_file, format='json')
    bit_bandmath(output_file, raster_gdal_info, [source_list],
                 no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)
    
def define_output_folder(input_product):
    
    timestamp = input_product.split('/')[-1].split('_')[1].split('-')[0] + 'T' +\
                input_product.split('/')[-1].split('_')[1].split('-')[1]
    mission = "S2" + input_product.split('/')[-1].split('_')[0][-1]
    tile_id = input_product.split('/')[-1].split('_')[3]
    #TODO: write version in config file
    version = "V100"
    #TODO: retrieve mode from MAJA L2A
    mode = "0"
    output_folder_name = "_".join(["WIC",timestamp,mission,tile_id,version,mode])
    return output_folder_name

if __name__ == "__main__":
    # INPUT PARSING
    # First & only input is the path of the input json configuration file
    config_json_file = sys.argv[1]
    config = load_configuration(config_json_file)
    
    input_image_path = config['input_image_path']
    classifier_path = config["classifier_path"]
    slope_file_path =config['slope_file_path']
    water_mask_path = config['water_mask_path']
    output_WIC_dir = config['output_WIC_dir']

    output_folder_name = define_output_folder(input_image_path.rstrip(os.sep))
    output_WIC_dir = os.path.join(output_WIC_dir, output_folder_name)
    if not os.path.isdir(output_WIC_dir):
        os.mkdir(output_WIC_dir)

    # Define logger
    LOGGER_LEVEL=logging.DEBUG
    logger = LogUtil.get_logger('WICComputation', LOGGER_LEVEL, "log_harvester/logs.log")

    #Compute image textures
    logger.info(f"Compute textures from input product: {input_image_path}")
    logger.info(f"Textures files are stored in: {output_WIC_dir}/tmp")
    os.system(f"{ROOT_FOLDER}/wic_s2/processing/compute_images_texture.py {input_image_path} {output_WIC_dir}")

    #Compute image indices
    image_name = os.path.split(input_image_path.rstrip(os.sep))[1]
    logger.info(f"Compute WIC from input product: {input_image_path}")

    IndicesComputer = IndicesComputation(   input_image_path,
                                            output_WIC_dir,
                                            slope_file_path,
                                            LIST_TRAINING_INDICES)
    matrix_of_indices, input_image_shape, unvalid_mask = IndicesComputer.create_matrix_of_indices()

    logger.info(f"Create dataframe")
    dataframe_indices = create_dataframe(matrix_of_indices, LIST_TRAINING_INDICES, LIST_TRAINING_INDICES_TYPES)

    logger.info(f"Load classifier: {classifier_path}")
    classifier = get_classifier(classifier_path)

    logger.info(f"Launch classification: {classifier_path}")

    ## CLASSIFY BY BATCH
    predictions, probabilities = classify_data(classifier, dataframe_indices)
    
    #Reshape to input image shape
    predictions = np.reshape(predictions, input_image_shape).astype(np.uint8)
    probabilities = np.reshape(100*probabilities, input_image_shape + [probabilities.shape[1]]).astype(np.uint8)
    # Change values to fill value within unvalid_mask
    # unvalid_mask = np.reshape([x for x in unvalid_mask], input_image_shape).astype(np.uint8)
    # predictions = np.where(unvalid_mask, 255, predictions)
    
    # Define filename (following the naming convention from PUM ICE)
    wic_filename = output_folder_name + "_WIC.tif"
    output_WIC_file = os.path.join(output_WIC_dir, wic_filename)
    logger.info(f"Write WIC raster to tif: {output_WIC_dir}")
    write_raster(predictions, input_image_path, image_name, output_WIC_file)
    
    tmp_WIC_nomask_file = os.path.join(output_WIC_dir, "tmp", "tmp_WIC_nomask.tif")
    change_wic_values(tmp_WIC_nomask_file, output_WIC_file)
    # os.rename(tmp_WIC_file, output_WIC_file)
    tmp_WIC_file = os.path.join(output_WIC_dir, "tmp", "tmp_WIC.tif")

    #Define masks paths
    cloud_mask_path = os.path.join(input_image_path, "MASKS", image_name + "_CLM_R2.tif")
    nodata_mask_path = os.path.join(input_image_path, "MASKS", image_name + "_EDG_R2.tif")
    # Add cloud mask
    add_cloud_mask(tmp_WIC_file, tmp_WIC_nomask_file, cloud_mask_path)
    os.rename(tmp_WIC_file, output_WIC_file)
    # Add no data mask
    add_nodata_mask(tmp_WIC_file, output_WIC_file, nodata_mask_path)
    os.rename(tmp_WIC_file, output_WIC_file)
    # Add water mask
    add_water_mask(tmp_WIC_file, output_WIC_file, water_mask_path)
    os.rename(tmp_WIC_file, output_WIC_file)

    # Add final colortable
    add_wic_colortable(output_WIC_file)
    #Rewrite in COG format
    rewrite_cog(output_WIC_file)

    #Write probabilities raster of each class to tif
    probabilities_classes = ['other_features','snow_ice','water']
    for i in range(probabilities.shape[2]):
        output_proba_file = os.path.join(output_WIC_dir, "tmp", f"proba_{probabilities_classes[i]}.tif")
        write_raster(probabilities[:,:,i], input_image_path, image_name, output_proba_file)
        add_proba_colortable(output_proba_file)
    
    #Write maximum probabilities to tif
    proba_maximum = np.max(probabilities,axis=2)
    proba_filename = output_folder_name + "_PRB.tif"
    output_proba_max_file = os.path.join(output_WIC_dir, proba_filename)
    write_raster(proba_maximum, input_image_path, image_name, output_proba_max_file)
    tmp_proba_file = os.path.join(output_WIC_dir, "tmp", "tmp_proba")
    #Add cloud mask
    add_cloud_mask(tmp_proba_file, output_proba_max_file, cloud_mask_path)
    os.rename(tmp_proba_file, output_proba_max_file)
    #Add no data mask
    add_nodata_mask(tmp_proba_file, output_proba_max_file, nodata_mask_path)
    os.rename(tmp_proba_file, output_proba_max_file)
    #Add colortable
    add_proba_colortable(output_proba_max_file)
    #Rewrite in COG format
    rewrite_cog(output_proba_max_file)
    
    logger.info("End of computation")
