#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import xarray as xr
from osgeo import gdal
import rioxarray as rxr
import numpy as np
import cv2 as cv

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('wic_s2')[:-1])
sys.path.append(ROOT_FOLDER+'wic_s2')
from utils.log_util import LogUtil


# import line_profiler
class ImageTexturesComputation:
    '''
    Texture computation tools for S2 rasters
    '''
    LOGGER_LEVEL=logging.DEBUG
    NODATA_L2A = -10000

    def __init__(self,
                 path_s2_input_dir:str,
                 textures_to_compute:list['str'],
                 target_resolution:int,
                 path_wic_output_dir:str)->None:

        self.path_s2_input_dir = path_s2_input_dir
        self.textures_to_compute = textures_to_compute
        self.target_resolution = target_resolution
        self.path_wic_output_dir = path_wic_output_dir
        self.logger = LogUtil.get_logger('ImageTexturesComputation', self.LOGGER_LEVEL, "log_harvester/logs.log")
        self.gradient=None
        self.resampled_b2_path = None
        self.resampled_b2 = None
        self.std_gblue = None

        gdal.DontUseExceptions()

    def get_local_std(self, array, nb_of_neighbors=2):
        mu = cv.blur(array, (nb_of_neighbors+1,nb_of_neighbors+1))
        mu2 = cv.blur(array*array, (nb_of_neighbors+1,nb_of_neighbors+1))

        sigma = cv.sqrt(mu2 - mu*mu);
        return sigma

    #@profile
    def sobel_grad(self, array, nb_of_neighbour=2):
        array = ((array>=self.NODATA_L2A) * array - (array<=self.NODATA_L2A) * np.ones_like(array)).astype(np.float32)
        self.logger.info(f'>>> Sobel filtering on array with type {array.dtype}')
        array[array == -1] = np.nan
        
        dx = 1
        dy = 0
        ksize = nb_of_neighbour+1
        gradient_x = abs(cv.Sobel(array,
                                  ddepth=cv.CV_32FC1,
                                  dx=dx,
                                  dy=dy,
                                  scale=2**(2+dx+dy-ksize*2),
                                  ksize=ksize))
        
        gradient_y = abs(cv.Sobel(array,
                                  ddepth=cv.CV_32FC1,
                                  dx=dy,
                                  dy=dx,
                                  scale=2**(2+dx+dy-ksize*2),
                                  ksize=ksize))
        edges = cv.addWeighted(gradient_x,0.5, gradient_y,0.5,1)

        return edges

    #@profile
    def get_gradient(self, input_array, nb_of_neighbors=2):

        gradient = self.sobel_grad(input_array,
                                   nb_of_neighbors)

        # gradient = cv.bilateralFilter(gradient,
        #                               d=nb_of_neighbors+1,
        #                               sigmaColor=75,
        #                               sigmaSpace=75)
        return gradient

    def resample_raster(self,
                       res_out:int,
                       raster_path:str):
        """
        Resamples a raster
        """
        gdal.Warp(self.path_wic_output_dir+'/tmp/resampled_B2.tif',
                  raster_path,
                  options=gdal.WarpOptions(resampleAlg='average',
                                           xRes=res_out,
                                           yRes=res_out))

        ds = gdal.Open(self.path_wic_output_dir+'/tmp/resampled_B2.tif')
        resampled_array = ds.GetRasterBand(1).ReadAsArray()
        del ds

        return resampled_array

    @staticmethod
    def write_geotiff(filename:str, arr:np.array, in_ds:gdal.Dataset)->None:
        '''
        _summary_

        _extended_summary_

        Parameters
        ----------
        filename : str
            _description_
        arr : np.array
            _description_
        in_ds : gdal.Dataset
            _description_
        '''

        if arr.dtype == np.float64:
            arr_type = gdal.GDT_Float64
        elif arr.dtype == np.float32:
            arr_type = gdal.GDT_Float32
        elif arr.dtype == np.int16:
            arr_type = gdal.GDT_Int16
        else:
            arr_type = gdal.GDT_Int32

        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(filename, arr.shape[1], arr.shape[0], 1, arr_type)
        out_ds.SetProjection(in_ds.GetProjection())
        out_ds.SetGeoTransform(in_ds.GetGeoTransform())
        band = out_ds.GetRasterBand(1)
        band.WriteArray(arr)
        band.FlushCache()
        band.ComputeStatistics(False)

    def get_image_textures(self):
        """
        Summary
        -------
        Computes Sentinel_2 raster textures listed in argument.

        Args:
        -----
        - image_path (str): path to S2 image
        - textures_to_compute (list): list str with indices to compute in : ['g_blue', 'WICI', 'std_ndsi', 'std_classified_ndsi', 'std_gblue', 'std_b2']
        - target_resolution (int): target resolution in meters
        - savedir (str): path of the directory where the output image will be created

        Return:
        -------
        None

        Raises:
        -------
        None
        """
        self.logger.info('Starting textures computation')
        self.path_s2_input_dir = self.path_s2_input_dir.rstrip(os.sep)
        image_name = os.path.basename(self.path_s2_input_dir)
        self.logger.info(f'Loading B12 band from {image_name} located at {self.path_s2_input_dir}...')
        # Load B12
        im_b12 = rxr.open_rasterio(f"{self.path_s2_input_dir}/{image_name}_FRE_B12.tif")

        # Set-up output file-tree
        self.logger.info('Setting up output file-tree...')
        if not os.path.exists(self.path_wic_output_dir):
            os.mkdir(self.path_wic_output_dir)
        if not os.path.exists(os.path.join(self.path_wic_output_dir,"tmp")):
            os.mkdir(os.path.join(self.path_wic_output_dir,"tmp"))

        if 'g_blue' in self.textures_to_compute:

            self.logger.info('Computing Blue Gradient')
            self.logger.debug('Resampling B2')
            self.resampled_b2_path = f"{self.path_s2_input_dir}/{image_name}_FRE_B2.tif"
            self.resampled_b2 = self.resample_raster(self.target_resolution, self.resampled_b2_path)

            self.logger.debug('Initializing Gradient output ndarray')
            self.logger.debug('Computing gradient...')
            self.gradient = self.get_gradient(self.resampled_b2,
                                              nb_of_neighbors= 2)
            self.logger.debug(f'{self.gradient.dtype}')
            self.logger.debug('Done')

            self.g_blue_file_path = os.path.join(self.path_wic_output_dir, "tmp", "g_blue.tif")
            self.logger.info(f'Writing the output location {self.g_blue_file_path}')
            ds = gdal.Open(self.path_wic_output_dir+'/tmp/resampled_B2.tif')
            self.write_geotiff(self.g_blue_file_path, self.gradient, ds)
            del ds

        else:

            self.gradient = None
            self.resampled_b2 = None

        if 'std_gblue' in self.textures_to_compute :
            if self.gradient is None:
                g_blueds=xr.open_dataset(f"{self.path_wic_output_dir}/{image_name}_g_blue.nc")
                self.gradient = g_blueds['__xarray_dataarray_variable__'].values

            self.logger.info('Computing STD of Blue gradient...')
            self.std_gblue = self.get_local_std(self.gradient,
                                                nb_of_neighbors=10)
            self.logger.info('Done')

            self.std_g_blue_file_path = os.path.join(self.path_wic_output_dir, "tmp", "std_g_blue.tif")
            self.logger.info(f'Writing the output location {self.std_g_blue_file_path}')
            ds = gdal.Open(self.path_wic_output_dir+'/tmp/resampled_B2.tif')
            self.write_geotiff(self.std_g_blue_file_path, self.std_gblue, ds)

        self.gradient = None
        self.std_gblue = None
        im_b12.close()

#######################################################################################################
#                                                 MAIN                                                #
#######################################################################################################
if __name__ == "__main__":
    # INPUT PARSING
    # First input is the path of the input Sentinel-2 L2A product
    # Second input is the path of the output WIC product
    path_s2_input_dir, path_wic_output_dir = sys.argv[1], sys.argv[2]

    # PROCESSING CONFIGURATION
    # TODO move those 2 parameters to a configuration file (json for example)
    TEXTURES_TO_COMPUTE = ['g_blue', 'std_gblue']
    TARGET_RESOLUTION = 20

    # TEXTURE PROCESSING
    ImageTexturesComputer = ImageTexturesComputation(path_s2_input_dir,
                                                     TEXTURES_TO_COMPUTE,
                                                     TARGET_RESOLUTION,
                                                     path_wic_output_dir)

    ImageTexturesComputer.get_image_textures()
