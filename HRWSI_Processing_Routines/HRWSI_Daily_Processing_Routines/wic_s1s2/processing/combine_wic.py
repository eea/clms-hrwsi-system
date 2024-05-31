#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from osgeo import gdal, ogr, osr
import os
import sys
import glob
import datetime
import numpy as np

ROOT_FOLDER = '/'.join(os.getcwd().split('wic_s1s2')[:-1])
sys.path.append(ROOT_FOLDER+'wic_s1s2')
from geometry.combine_bits_geotiff import bit_bandmath, bit_bandmath_uint16
from utils.add_colortable import add_wic_colortable, add_qc_colortable
from utils.rewrite_cog import rewrite_cog

class WICCombination:
    """
    Combination of input WIC S1 & S2 products in order to process WIC S1S2 product
    """

    def __init__(self,
                 wic_s1_folder:str,
                 wic_s2_folder:str,
                 water_mask_path:str,
                 output_folder:str,
                 date:str):
        self.wic_s1_folder = wic_s1_folder
        self.wic_s2_folder = wic_s2_folder
        self.water_mask_path = water_mask_path
        self.output_folder = output_folder
        self.date = date

        #other parameters
        self.resolution = 20

        if not os.path.isdir(self.output_folder):
            os.mkdir(self.output_folder)

    def resample_image(self, 
                       res_out,
                       input_image_path,
                       output_image_path):
        """
        Resample the input image to a new resolution and save the result to the output image.

        Args:
            res_out (float): Output resolution in the same unit as the input image.
            input_image_path (str): Path to the input image.
            output_image_path (str): Path to save the resampled output image.
        """
        try:
            # Open the input image
            # src_ds = gdal.Open(input_image_path, gdalconst.GA_ReadOnly)
            src_ds = gdal.Open(input_image_path, gdal.GA_ReadOnly)
            if src_ds is None:
                raise ValueError("Failed to open the input image.")

            # Get the geotransform parameters
            ulx, xres, xskew, uly, yskew, yres = src_ds.GetGeoTransform()
            lrx = ulx + (src_ds.RasterXSize * xres) + (xskew * src_ds.RasterYSize)
            lry = uly + (src_ds.RasterYSize * yres) + (yskew * src_ds.RasterXSize)

            # Close the input image dataset
            src_ds = None

            # Perform resampling using gdal.Warp
            gdal.Warp(output_image_path, input_image_path,
                      options=gdal.WarpOptions(resampleAlg='average', format='VRT',
                      outputBounds=(ulx, lry, lrx, uly),
                      xRes=res_out, yRes=-res_out))
        except Exception as e:
            print(f"An error occurred: {e}")


    def add_water_mask(self,
                       output_file:str,
                       input_file:str,
                       water_mask:str):
        """Add water mask to wic s2 file."""
        source_list = [{'sources': [{'filepath': water_mask,'bandnumber': 1,'unpack_bits': False},
                                    {'filepath': input_file,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': 'np.uint(255)*(A0==0) +\
                                      A1*(A0==1) +\
                                      A1*(A0==2) +\
                                      np.uint(255)*(A0==253) +\
                                      np.uint(255)*(A0==254) +\
                                      np.uint(255)*(A0==255)'}]
        
        source_list_qcflags = [{'sources': [{'filepath': water_mask,'bandnumber': 1,'unpack_bits': False},
                                    {'filepath': input_file,'bandnumber': 1,'unpack_bits': False}], \
                                'operation': 'np.uint(0)*(A0==0) +\
                                              A1*(A0==1) +\
                                              A1*(A0==2) +\
                                              np.uint(0)*(A0==253) +\
                                              np.uint(0)*(A0==254) +\
                                              np.uint(0)*(A0==255)'}]

        raster_gdal_info = gdal.Info(input_file, format='json')
        if "WICS1_QCFLAGS" in input_file:
            bit_bandmath_uint16(output_file, raster_gdal_info, [source_list_qcflags],
                    compress=False, add_overviews=False, use_default_cosims_config=False)
        elif "WICS2_QCFLAGS" in input_file:
            bit_bandmath(output_file, raster_gdal_info, [source_list_qcflags],
                    compress=False, add_overviews=False, use_default_cosims_config=False)
        else:
            bit_bandmath(output_file, raster_gdal_info, [source_list],
                    no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)

    def check_wic_products_of_the_same_aquisition(self):
        # Retrieve the dates of the products
        wic_s2_products_dates = dict()
        for wic_s2_product in wic_s2_products:
            # Check that one WIC layer exists
            wics2_layers = glob.glob(os.path.join(self.wic_s2_folder, wic_s2_product, "*_WIC.tif"))
            assert len(wics2_layers) == 1
            #retrieve date
            wic_s2_layer_date = wics2_layers[0].split('/')[-1].split('_')[1]
            wic_s2_products_dates[wics2_layers[0].split('/')[-1]] = wic_s2_layer_date
        # TODO then, merge the wic s2 products of the same acquisition
        # for key, value in wic_s2_products_dates:

        wic_s1_products_dates = dict()
        for wic_s1_product in wic_s1_products:
            wics1_layers = glob.glob(os.path.join(self.wic_s1_folder, wic_s1_product, "*_WIC.tif"))
            assert len(wics1_layers) == 1
            #retrieve date
            wic_s1_layer_date = wics1_layers[0].split('/')[-1].split('_')[1]
            wic_s1_products_dates[wics1_layers[0].split('/')[-1]] = wic_s1_layer_date
        # TODO then, merge the wic s1 products of the same acquisition
        # for key, value in wic_s1_products_dates:
    
    def preprocessing(self):
        # Mask WIC S2 layers with water mask
        tmp_files = {}
        for layer in ["WIC", "QCFLAGS", "QC"]:
            wics2_layer = glob.glob(os.path.join(self.wic_s2_folder, self.wics2_product, f"*_{layer}.tif"))[0]
            assert os.path.exists(wics2_layer), f"{wics2_layer} does not exist"
        
            tmp_wics2_layer_masked = os.path.join(self.tmp_folder, f"tmp_WICS2_{layer}_masked.tif")
            self.add_water_mask(tmp_wics2_layer_masked, wics2_layer, self.water_mask_path)

            tmp_files[f"WICS2_{layer}"] = tmp_wics2_layer_masked

            # Resample WIC S1 layer to 20m + water mask
            wics1_layer = glob.glob(os.path.join(self.wic_s1_folder, self.wics1_product, f"*_{layer}.tif"))[0]
            assert os.path.exists(wics1_layer), f"{wics1_layer } does not exist"
            
            tmp_wics1_layer_resampled = os.path.join(self.tmp_folder, f"tmp_WICS1_{layer}_resampled.tif")
            self.resample_image(self.resolution, wics1_layer, tmp_wics1_layer_resampled)
            #water masking
            tmp_wics1_layer_resampled_masked = os.path.join(self.tmp_folder, f"tmp_WICS1_{layer}_resampled_masked.tif")
            self.add_water_mask(tmp_wics1_layer_resampled_masked, tmp_wics1_layer_resampled, self.water_mask_path)
            
            tmp_files[f"WICS1_{layer}"] = tmp_wics1_layer_resampled_masked

        return tmp_files

    def merge_wic_layers(self, wic_s1_layer, wic_s2_layer):
        #check that wic files exist
        assert os.path.exists(wic_s1_layer), f"{wic_s1_layer} does not exist"
        assert os.path.exists(wic_s2_layer), f"{wic_s2_layer} does not exist"

        # Define output filename (following the naming convention from PUM ICE)
        wic_filename = self.product_name + "_WIC.tif"

        output_wics1s2_layer =  os.path.join(self.output_product_path, wic_filename)

        #Combine layers
        #if a pixel has an exploitable classification in WIC S2 (‘water’, ‘ice’ or ‘other features’), this information is kept. 
        #otherwise, if the pixel is classified as ‘water’ or ‘ice’ in the WIC S1 product, this information is taken as a replacement
        #if not (‘radar shadow’ or ‘no data’), the WIC S2 classification is kept (‘cloud’ or ‘no data’).
        #if 'no data' in WIC S2, the WIC S1 info is taken
        source_list = [{'sources': [{'filepath': wic_s1_layer,'bandnumber': 1,'unpack_bits': False},
                                    {'filepath': wic_s2_layer,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': 'A1*(A1==1) +\
                                      A1*(A1==100) +\
                                      A1*(A1==254) +\
                                      A0*(A0==1)*(A1==205) +\
                                      A0*(A0==100)*(A1==205) +\
                                      A1*(A0!=1)*(A0!=100)*(A1==205) +\
                                      A0*(A1==255)'}]
        raster_gdal_info = gdal.Info(wic_s2_layer, format='json')
        bit_bandmath(output_wics1s2_layer, raster_gdal_info, [source_list],
                    no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)

        # Add final colortable
        add_wic_colortable(output_wics1s2_layer)

        #Rewrite COG
        rewrite_cog(output_wics1s2_layer)

        
    def merge_qc_layers(self, wics1_wic_layer, wics2_wic_layer, wics1_qc_layer, wics2_qc_layer): 
        # check that wic layers and qc layers exist
        assert os.path.exists(wics1_wic_layer), f"{wics1_wic_layer} does not exist"
        assert os.path.exists(wics2_wic_layer), f"{wics2_wic_layer} does not exist"
        assert os.path.exists(wics1_qc_layer), f"{wics1_qc_layer} does not exist"
        assert os.path.exists(wics2_qc_layer), f"{wics2_qc_layer} does not exist"

        # Define output QC filename (following the naming convention from PUM ICE)
        qc_filename = self.product_name + "_QC.tif"
        output_qc_layer =  os.path.join(self.output_product_path, qc_filename)

        #Combine layers
        source_list = [{'sources': [{'filepath': wics1_wic_layer,'bandnumber': 1,'unpack_bits': False},
                                    {'filepath': wics2_wic_layer,'bandnumber': 1,'unpack_bits': False},
                                    {'filepath': wics1_qc_layer,'bandnumber': 1,'unpack_bits': False},
                                    {'filepath': wics2_qc_layer,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': 'A3*(A1==1) +\
                                      A3*(A1==100) +\
                                      A3*(A1==254) +\
                                      A2*(A1==205)*(A0==1) +\
                                      A2*(A1==205)*(A0==100) +\
                                      A2*(A1==205)*(A0!=100)*(A0!=1) +\
                                      A2*(A1==255)'}]
                                    #   A3*(A1==205)*(A0==200) +\
                                    #   A3*(A1==205)*(A0==255) +\
        raster_gdal_info = gdal.Info(wics2_qc_layer, format='json')
        bit_bandmath(output_qc_layer, raster_gdal_info, [source_list],
                    no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)   
        
        # Add final colortable
        add_qc_colortable(output_qc_layer)

        #Rewrite COG
        rewrite_cog(output_qc_layer)
        
    def merge_qcflags_layers(self, wics1_wic_layer, wics2_wic_layer, wics1_qcflags_layer, wics2_qcflags_layer): 
        # check that wic layers and qc layers exist
        assert os.path.exists(wics1_wic_layer), f"{wics1_wic_layer} does not exist"
        assert os.path.exists(wics2_wic_layer), f"{wics2_wic_layer} does not exist"
        assert os.path.exists(wics1_qcflags_layer), f"{wics1_qcflags_layer} does not exist"
        assert os.path.exists(wics2_qcflags_layer), f"{wics2_qcflags_layer} does not exist"

        # Define output QC filename (following the naming convention from PUM ICE)
        qcflags_filename = self.product_name + "_QCFLAGS.tif"
        output_qcflags_layer =  os.path.join(self.output_product_path, qcflags_filename)

        #Combine layers
        source_list = [{'sources': [{'filepath': wics1_wic_layer,'bandnumber': 1,'unpack_bits': False},
                                    {'filepath': wics2_wic_layer,'bandnumber': 1,'unpack_bits': False},
                                    {'filepath': wics1_qcflags_layer,'bandnumber': 1,'unpack_bits': False},
                                    {'filepath': wics2_qcflags_layer,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': 'A3*(A1==1) +\
                                      A3*(A1==100) +\
                                      A3*(A1==254) +\
                                      (np.uint16(256)+A2)*(A1==205)*(A0==1) +\
                                      (np.uint16(256)+A2)*(A1==205)*(A0==100) +\
                                      (np.uint16(256)+A2)*(A1==205)*(A0!=100)*(A0!=1) +\
                                      (np.uint16(256)+A2)*(A1==255)*(A2!=0) +\
                                      np.uint16(0)*(A1==255)*(A2==0)'}]
        raster_gdal_info = gdal.Info(wics1_qcflags_layer, format='json')
        bit_bandmath_uint16(output_qcflags_layer, raster_gdal_info, [source_list],
                    compress=False, add_overviews=False, use_default_cosims_config=False)   
        
        #Rewrite COG
        rewrite_cog(output_qcflags_layer)

    def define_output_folder(self):
        #Retrieve input products timestamps
        self.wic_s2_date = self.wics2_product.split('/')[-1].split('_')[1]
        self.wic_s1_date = self.wics1_product.split('/')[-1].split('_')[1]

        wic_S1_datetime = datetime.datetime.strptime(self.wic_s1_date, '%Y%m%dT%H%M%S')
        wic_S2_datetime = datetime.datetime.strptime(self.wic_s2_date, '%Y%m%dT%H%M%S')
        timestamp = max(wic_S1_datetime, wic_S2_datetime).strftime('%Y%m%dT%H%M%S')
        mission = "S1-S2"
        #TODO: write version in config file
        version = "V100"
        #TODO : retrieve mode from MAJA L2A
        mode = "0"
        self.product_name = "_".join(["WIC",timestamp,mission,self.tile_id ,version,mode])
        self.output_product_path = os.path.join(self.output_folder, self.product_name)
        if not os.path.isdir(self.output_product_path):
            os.mkdir(self.output_product_path)

        self.tmp_folder = os.path.join(self.output_product_path, "tmp")
        if not os.path.isdir(self.tmp_folder):
            os.mkdir(self.tmp_folder)

    
    def full_processing(self):
        #TODO: identify input products
        self.wic_s1_products = [prod for prod in os.listdir(self.wic_s1_folder) if self.date in prod]
        self.wic_s2_products = [prod for prod in os.listdir(self.wic_s2_folder) if self.date in prod]

        if not(self.wic_s1_products) or not (self.wic_s2_products):
            print(f"No WICS1S2 computation because no WIC S1 or no WIC S2 on date {self.date}")
        else:
            # Check of several WIC S2 of the same acquisition
            #TODO
            # self.check_wic_products_of_the_same_aquisition()

            # for a given day, there can be 1 S2 acquisition and 2 S1 acquisitions
            for self.wics1_product in self.wic_s1_products:
                self.wics2_product = self.wic_s2_products[0]
            
                #Check that they are on the same tile
                tileid_wics1 = self.wics1_product.split('_')[-3]
                tileid_wics2 = self.wics2_product.split('_')[-3]
                assert tileid_wics1 == tileid_wics2
                self.tile_id = tileid_wics2
                
                self.define_output_folder()

                #Reproject WIC S1 to 20m, and apply water mask to WIC S2
                tmp_files = self.preprocessing()

                #Combine both layers
                self.merge_wic_layers(tmp_files['WICS1_WIC'], 
                                      tmp_files['WICS2_WIC'])

                #Create QC layer
                self.merge_qc_layers(tmp_files['WICS1_WIC'], 
                                     tmp_files['WICS2_WIC'],
                                     tmp_files['WICS1_QC'],
                                     tmp_files['WICS2_QC'])

                #Create QCFLAGS layer
                self.merge_qcflags_layers(tmp_files['WICS1_WIC'], 
                                          tmp_files['WICS2_WIC'],
                                          tmp_files['WICS1_QCFLAGS'],
                                          tmp_files['WICS2_QCFLAGS'])
                


if __name__ == "__main__":
    
    # TODO: give folder as arguments, or directly WIC products paths ?

    #Folder containing all the S1 products of the day
    wic_s1_folder = "/home/madeni/Documents/HR-WSI/products_wics1"
    #Folder containing all the S2 products of the day
    wic_s2_folder = "/home/madeni/Documents/HR-WSI/products_wic_s2_T32TNS_GV/WIC_output"
    #Path to water mask
    water_mask_path = "/home/madeni/Documents/HR-WSI/products_wics1s2/water_mask/32TNS/WL_2018_20m_32TNS.tif"
    #Path to output folder where the WIC S1S2 will be written
    output_folder = "/home/madeni/Documents/HR-WSI/products_wics1s2"


    #Date of the day
    # date = "20200905"
    for day in range(5,6):
        date = datetime.datetime(2020,9,day)
        date_str = date.strftime('%Y%m%d')

        WICCombine = WICCombination(wic_s1_folder,
                                    wic_s2_folder,
                                    water_mask_path,
                                    output_folder,
                                    date_str)
        WICCombine.full_processing()
