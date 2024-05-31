#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from osgeo import gdal
import numpy as np

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('wic_s2')[:-1])
sys.path.append(ROOT_FOLDER+'wic_s2')
from processing.l2a_to_WIC_RF import load_configuration
from geometry.combine_bits_geotiff import bit_bandmath
from utils.add_colortable import add_qc_colortable
from utils.rewrite_cog import rewrite_cog

class WicPostProcessing:
    def __init__(self,
                 input_image_path,
                 output_WIC_dir,
                 water_mask_path):
        self.input_image_path = input_image_path.rstrip(os.sep)
        self.input_image_name = self.input_image_path.split('/')[-1]
        self.output_WIC_dir = output_WIC_dir

        # Retrieve auxiliary files : WAW WATER MASK, MAJA MG2 R2 MASK, MAJA EDG R2 MASK
        #TODO: differentiate water mask file (WAW now but WCD later) from WAW file
        self.water_mask_path = water_mask_path
        assert os.path.exists(self.water_mask_path), f'product_path {self.water_mask_path} does not exist'
        self.mg2_mask_path = os.path.join(self.input_image_path,
                                         'MASKS' ,
                                         self.input_image_name + "_MG2_R2.tif")
        assert os.path.exists(self.mg2_mask_path), f'product_path {self.mg2_mask_path} does not exist'
        self.edg_mask_path = os.path.join(self.input_image_path,
                                         'MASKS' ,
                                         self.input_image_name + "_EDG_R2.tif")
        assert os.path.exists(self.edg_mask_path), f'product_path {self.edg_mask_path} does not exist'

        #get product name
        self.identify_WIC_product_name()

        # Get existing WIC layers
        self.wic_raster_path = os.path.join(self.output_WIC_dir,
                                         self.output_folder_name ,
                                         self.output_folder_name + "_WIC.tif")
        assert os.path.exists(self.wic_raster_path), f'product_path {self.wic_raster_path} does not exist'
        self.proba_raster_path = os.path.join(self.output_WIC_dir,
                                         self.output_folder_name ,
                                         self.output_folder_name + "_PRB.tif")
        assert os.path.exists(self.proba_raster_path), f'product_path {self.proba_raster_path} does not exist'
    
    def identify_WIC_product_name(self):
        timestamp = self.input_image_path.split('/')[-1].split('_')[1].split('-')[0] + 'T' +\
                self.input_image_path.split('/')[-1].split('_')[1].split('-')[1]
        mission = "S2" + self.input_image_path.split('/')[-1].split('_')[0][-1]
        tile_id = self.input_image_path.split('/')[-1].split('_')[3]
        #TODO: write version in config file
        version = "V100"
        #TODO: retrieve mode from MAJA L2A
        mode = "0"
        self.output_folder_name = "_".join(["WIC",timestamp,mission,tile_id,version,mode])

    def limit_qc_to_three(self,qc_file):
        assert os.path.exists(qc_file), f'product_path {qc_file} does not exist'
        tmp_file = os.path.join(self.output_WIC_dir,
                                         self.output_folder_name ,
                                         self.output_folder_name + "_tmp_qc.tif")
        
        source_list = [{'sources': [{'filepath': qc_file,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': 'np.uint8(0)*(A0==0)+\
                                        np.uint8(1)*(A0==1)+\
                                        np.uint8(2)*(A0==2)+\
                                        np.uint8(3)*(A0==3)+\
                                        np.uint8(3)*(A0>3)*(A0<=10)+\
                                        np.uint8(205)*(A0==205)+\
                                        np.uint8(255)*(A0==255)'}]
        raster_gdal_info = gdal.Info(qc_file, format='json')
        bit_bandmath(tmp_file, raster_gdal_info, [source_list],
                    no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)
        os.remove(qc_file)
        os.rename(tmp_file,qc_file)

    
    def compute_QC_proba(self):

        self.output_qc_proba_path =   os.path.join(self.output_WIC_dir,
                                         self.output_folder_name ,
                                         self.output_folder_name + "_QC_proba.tif")
        #[0: highest quality, 1: lower quality, 2: decreasing quality, 3: lowest quality, 205: cloud mask, 255: no data]
        source_list = [{'sources': [{'filepath': self.proba_raster_path,'bandnumber': 1,'unpack_bits': False},\
                                    {'filepath': self.edg_mask_path,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': 'np.uint8(255)*(A1==1) +\
                                      np.uint8(255)*(A1!=1)*(A0==255) +\
                                      np.uint8(205)*(A1!=1)*(A0==205) +\
                                      np.uint8(0)*(A1!=1)*(A0>80) +\
                                      np.uint8(1)*(A1!=1)*(A0<=80)*(A0>67) +\
                                      np.uint8(2)*(A1!=1)*(A0<=67)*(A0>50) +\
                                      np.uint8(3)*(A1!=1)*(A0<=50)'}]
        raster_gdal_info = gdal.Info(self.proba_raster_path, format='json')
        bit_bandmath(self.output_qc_proba_path, raster_gdal_info, [source_list],
                    no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)
        
        # Add colortable
        add_qc_colortable(self.output_qc_proba_path)
        rewrite_cog(self.output_qc_proba_path)

    def compute_QC_proba_waw(self):
        #add a comparison of WIC layer with WAW, and decrease QC_proba is case of disagreement
        assert os.path.exists(self.output_qc_proba_path), f'product_path {self.output_qc_proba_path} does not exist'

        self.output_qc_proba_waw_path =   os.path.join(self.output_WIC_dir,
                                         self.output_folder_name ,
                                         self.output_folder_name + "_QC_proba_waw.tif")
        
        source_list = [{'sources': [{'filepath': self.output_qc_proba_path,'bandnumber': 1,'unpack_bits': False},\
                                    {'filepath': self.water_mask_path,'bandnumber': 1,'unpack_bits': False},\
                                    {'filepath': self.wic_raster_path,'bandnumber': 1,'unpack_bits': False},\
                                    {'filepath': self.edg_mask_path,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': 'A0 +\
                                      np.uint8(1)*(A2==1)*(A1!=1)*(A1!=2)*(A0<=2) +\
                                      np.uint8(1)*(A2==100)*(A1!=1)*(A1!=2)*(A0<=2) +\
                                      np.uint8(1)*(A2==254)*(A1!=0)*(A1!=254)*(A0<=2)'}]
                                    #   A0*(A0==255) +\
                                    #   A0*(A0==205)+\
                                    #   (A0<=3)*(A3!=1)*np.minimum(B*0+3,A0+np.uint8(1)*(A2==1)*(A1!=1)*(A1!=2)*(A3!=1)).astype(np.uint8) +\
                                    #   (A0<=3)*(A3!=1)*np.minimum(B*0+3,A0+np.uint8(1)*(A2==100)*(A1!=1)*(A1!=2)*(A3!=1)).astype(np.uint8) +\
                                    #   (A0<=3)*(A3!=1)*np.minimum(B*0+3,A0+np.uint8(1)*(A2==254)*(A1!=0)*(A1!=254)*(A3!=1)).astype(np.uint8)'}]
        raster_gdal_info = gdal.Info(self.proba_raster_path, format='json')
        bit_bandmath(self.output_qc_proba_waw_path, raster_gdal_info, [source_list],
                    no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)
        
        # Add colortable
        add_qc_colortable(self.output_qc_proba_waw_path)
        rewrite_cog(self.output_qc_proba_waw_path)

    def compute_QC_proba_waw_mg2(self):
        #add a comparison of WIC layer with WAW, and decrease QC_proba is case of disagreement
        assert os.path.exists(self.output_qc_proba_waw_path), f'product_path {self.output_qc_proba_waw_path} does not exist'

        self.output_qc_proba_waw_mg2_path = os.path.join(self.output_WIC_dir,
                                            self.output_folder_name ,
                                            self.output_folder_name + "_QC.tif")
        
        source_list = [{'sources': [{'filepath': self.output_qc_proba_waw_path,'bandnumber': 1,'unpack_bits': False},\
                                    {'filepath': self.mg2_mask_path,'bandnumber': 1,'unpack_bits': True}], \
                        'operation': 'A0 +\
                                      np.uint8(1)*(A0<=2)*(A1[:,:,4] ==1) +\
                                      np.uint8(1)*(A0<=2)*(A1[:,:,5] ==1) +\
                                      np.uint8(1)*(A0<=2)*(A1[:,:,6] ==1) +\
                                      np.uint8(1)*(A0<=2)*(A1[:,:,7] ==1)'}]
        raster_gdal_info = gdal.Info(self.proba_raster_path, format='json')
        bit_bandmath(self.output_qc_proba_waw_mg2_path, raster_gdal_info, [source_list],
                    no_data_values_per_band=[np.uint8(255)], compress=False, add_overviews=False, use_default_cosims_config=False)
        
        self.limit_qc_to_three(self.output_qc_proba_waw_mg2_path)
        # Add colortable
        add_qc_colortable(self.output_qc_proba_waw_mg2_path)
        rewrite_cog(self.output_qc_proba_waw_mg2_path)

    def compute_QCFLAGS(self):
        self.qcflags_path=   os.path.join(self.output_WIC_dir,
                                         self.output_folder_name ,
                                         self.output_folder_name + "_QCFLAGS.tif")
        
        source_list = []
        #bit 0: topographic shadows
        source_list += [{'sources': [{'filepath': self.mg2_mask_path,'bandnumber': 1,'unpack_bits': True},
                                     {'filepath': self.water_mask_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': self.edg_mask_path,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': {0: '(A1<253)*np.logical_and(A0[:,:,4],A2!=1)'}}]
        #bit 1: unseen pixels due to topography
        source_list += [{'sources': [{'filepath': self.mg2_mask_path,'bandnumber': 1,'unpack_bits': True},
                                     {'filepath': self.water_mask_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': self.edg_mask_path,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': {1: '(A1<253)*np.logical_and(A0[:,:,5],A2!=1)'}}]
        #bit 2: sun too low for an accurate slope correction
        source_list += [{'sources': [{'filepath': self.mg2_mask_path,'bandnumber': 1,'unpack_bits': True},
                                     {'filepath': self.water_mask_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': self.edg_mask_path,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': {2: '(A1<253)*np.logical_and(A0[:,:,6],A2!=1)'}}]
        #bit 3: sun direction tangent to slope (inaccurate terrain correction)
        source_list += [{'sources': [{'filepath': self.mg2_mask_path,'bandnumber': 1,'unpack_bits': True},
                                     {'filepath': self.water_mask_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': self.edg_mask_path,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': {3: '(A1<253)*np.logical_and(A0[:,:,7],A2!=1)'}}]
        #bit 4: presence of water from WAW
        source_list += [{'sources': [{'filepath': self.water_mask_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': self.edg_mask_path,'bandnumber': 1,'unpack_bits': False}], \
                        'operation': {4: 'np.logical_or(A0==1,A0==2)*(A1!=1)'}}]

        raster_gdal_info = gdal.Info(self.wic_raster_path, format='json')
        bit_bandmath(self.qcflags_path, raster_gdal_info, [source_list],
                    compress=False, add_overviews=False, use_default_cosims_config=False)
        rewrite_cog(self.qcflags_path)


if __name__ == '__main__':
    config_json_file = sys.argv[1]
    config = load_configuration(config_json_file)

    output_WIC_dir = config['output_WIC_dir']
    input_image_path = config['input_image_path']
    water_mask_path = config['water_mask_path']

    wic_post_processing = WicPostProcessing(input_image_path,
                                            output_WIC_dir,
                                            water_mask_path)
    wic_post_processing.compute_QC_proba()
    wic_post_processing.compute_QC_proba_waw()
    wic_post_processing.compute_QC_proba_waw_mg2()

    wic_post_processing.compute_QCFLAGS()


 

