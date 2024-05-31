#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from osgeo import gdal
import numpy as np


# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('wic_s2')[:-1])
sys.path.append(ROOT_FOLDER+'wic_s2')
from utils.log_util import LogUtil


class IndicesComputation:
    """
    Indices computation class in order to classify the S2 image
    """

    LOGGER_LEVEL=logging.DEBUG

    def __init__(self,
                 s2_image_path:str,
                 output_wic_path:str,
                 slope_file_path:str,
                 list_training_indices:list['str'])->None:

        self.s2_image_path = s2_image_path
        self.output_wic_path = output_wic_path
        self.slope_file_path = slope_file_path
        self.list_training_indices = list_training_indices
        self.logger = LogUtil.get_logger('IndicesComputation', self.LOGGER_LEVEL, "log_harvester/logs.log")
        self.image_name = os.path.split(self.s2_image_path.rstrip(os.sep))[1]

        gdal.DontUseExceptions()

    def resample_image(self, res_out, input_image_path, output_image_path):
        """
        Resample the input image to a new resolution and save the result to the output image.

        Args:
            res_out (float): Output resolution in the same unit as the input image.
            input_image_path (str): Path to the input image.
            output_image_path (str): Path to save the resampled output image.
        """
        self.logger.debug(f"Resampling image {input_image_path}")
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
    
    def compute_index(self, gen1, gen2, threshold):
        """
        Compute an index based on two generators.

        Args:
            gen1 (iterable): First generator.
            gen2 (iterable): Second generator.
            threshold (float): Threshold value.

        Returns:
            generator: Generator yielding computed indices.
        """
        # Utiliser zip pour combiner les valeurs des deux générateurs
        combined_values = zip(gen1, gen2)
        
        # Itérer sur les valeurs combinées et calculer les indices
        for x, y in combined_values:
            try:
                # change data type to avoid RuntimeWarning
                x = np.float64(x)
                y = np.float64(y)

                if x + y != 0:
                    result = self.binarise_index((x - y) / (x + y), threshold)
                else:
                    result = -9999
            except RuntimeWarning as e:
                print("A RuntimeWarning occurred:", e)
                result = None
            yield result

    def binarise_index(self, value, threshold):
        """
        Binarise the index based on a threshold value.

        Args:
            value (float): Index value.
            threshold (float): Threshold value.

        Returns:
            float: Binarised index value.
        """
        return 1 if value >= threshold else 0
    
    def bounds(self, gen, mini, maxi):
        """
        Limit the value of 'elem' to be within the range [mini, maxi].

        Args:
            gen (generator): A generator yielding values to be constrained.
            mini (int or float): The minimum value.
            maxi (int or float): The maximum value.
        
        Returns:
            int or float: The constrained value within the specified range.
        """
        for elem in gen:
            yield max(mini, min(elem, maxi))

    def read_band_generator(self, band_path):
        """
        Generator function to read the raster band data from the specified file.

        Args:
            band_path (str): Path to the raster file.
        
        Yields:
            float: Each individual pixel value from the raster band.
        """
        try:
            with gdal.Open(band_path) as src:
                if src is None:
                    raise ValueError("Unable to open raster file.")
                    
                band_data = src.GetRasterBand(1).ReadAsArray()
                for value in band_data.flatten():
                    yield value
        except Exception as e:
            raise RuntimeError(f"An error occurred while reading band data: {e}")
    
    def compute_image_shape(self, band_path):
        """
        Computes the dimensions of the image from the specified raster file.

        Args:
            band_path (str): Path to the raster file.
        
        Returns:
            list: A list containing the dimensions of the image [width, height].
        """
        try:
            with gdal.Open(band_path) as src:
                if src is None:
                    raise ValueError("Impossible d'ouvrir le fichier raster.")
                    
                width = src.RasterXSize
                height = src.RasterYSize
                return [width, height]
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    
    def compute_mask(self, gen1, gen2):
        """
        Compute a mask based on two generators.

        Args:
            gen1 (iterable): First generator.
            gen2 (iterable): Second generator.
            
        Returns:
            numpy.ndarray: Array containing the mask values.
        """
        # Use zip to combine values from both generators
        combined_values = zip(gen1, gen2)
        # Generateur mask value one by one
        for x, y in combined_values:
            yield np.float64(x) + np.float64(y) == 0
    
    def combine_mask(self, gen1, gen2, gen3):
        """
        Combine masks from three generators using bitwise OR operation.

        Args:
            gen1 (iterable): First generator.
            gen2 (iterable): Second generator.
            gen3 (iterable): Third generator.
            
        Returns:
            generator: Generator yielding combined mask values.
        """
        combined_values = zip(gen1, gen2, gen3)
        combined_mask = (x | y | z for x, y, z in combined_values)
        return combined_mask

    def create_matrix_of_indices(self):
        index = {self.list_training_indices[i] : i for i in range(0,len(self.list_training_indices))}
        matrix_of_indices = [None]*len(self.list_training_indices)

        # Read slope tif file within a generator
        assert "slope" in self.list_training_indices
        assert os.path.isfile(self.slope_file_path)
        self.logger.info(f"Reading slope file: {self.slope_file_path}")
        ## TODO make sure the slope has the same dimension as the s2 image
        matrix_of_indices[index["slope"]] = self.read_band_generator(self.slope_file_path)

        # Read std_g_blue file within a generator
        assert "std_g_blue" in self.list_training_indices
        std_g_blue_path = os.path.join(self.output_wic_path, "tmp", "std_g_blue.tif")
        assert os.path.isfile(std_g_blue_path)
        self.logger.info(f"Reading std of blue gradient file: {std_g_blue_path}")
        matrix_of_indices[index["std_g_blue"]] = self.read_band_generator(std_g_blue_path)

        # Resample bands if not already done, verify the new tif file exists
        bands_to_resample = ["B3","B8","B4"]
        band_paths = {}
        for band_name in bands_to_resample:
            band_path = os.path.join(self.s2_image_path, f"20m_{self.image_name}_FRE_{band_name}.tif")
            if not os.path.exists(band_path):
                self.logger.info(f"Resampling band {band_name}")
                self.resample_image(20, os.path.join(self.s2_image_path, f"{self.image_name}_FRE_{band_name}.tif"), band_path)
            assert os.path.exists(band_path)
            band_paths[band_name] = band_path
        
        # verify the B11 tif file exists
        b11_path = os.path.join(self.s2_image_path, self.image_name + "_FRE_B11.tif")
        assert os.path.exists(b11_path)
        band_paths["B11"] = b11_path

        indices_bands = [   ("NDSI", "B3", "B11",0.4),
                            ("NDVI", "B8", "B4",0.1),
                            ("NDWI", "B3", "B8",0.3)]
        masks = []
        for normalised_index, b1, b2,threshold in indices_bands:
            self.logger.info(f"Compute {normalised_index}")
            normalised_index_generator = self.compute_index(self.read_band_generator(band_paths[b1]), self.read_band_generator(band_paths[b2]),threshold)
            matrix_of_indices[index[normalised_index]] = normalised_index_generator
            
            self.logger.info(f"Compute mask where reflectances of {b1} and {b2} are null")
            mask = self.compute_mask(self.read_band_generator(band_paths[b1]), self.read_band_generator(band_paths[b2]))
            masks.append(mask)

        # Compute bounded B11
        self.logger.info("Compute bounded B11")
        # bounded_b11 = (self.bounds(x, 200, 600) for x in self.read_band_generator(b11_path))
        bounded_b11_generator = self.bounds(self.read_band_generator(b11_path), 200, 600)
        
        matrix_of_indices[index['bounded_b11']] = bounded_b11_generator

        # Compute input image shape, because it is flatten and must be reshaped at the end of the classification
        input_image_shape = self.compute_image_shape(b11_path)

        combined_mask = self.combine_mask(masks[0],masks[1],masks[2])

        return matrix_of_indices, input_image_shape, combined_mask

    def from_array_to_tif(self, array, image_to_copy, output_tif_path):
        self.logger.info(f"Write array to tif file: {output_tif_path}")
        #get info from image_to_copy
        tiff_file = gdal.Open(image_to_copy)
        geotransform = tiff_file.GetGeoTransform()
        projection = tiff_file.GetProjection()
        band = tiff_file.GetRasterBand(1)
        xsize = band.XSize
        ysize = band.YSize
        tiff_file = None #close it
        band = None #close it
        
        #create new raster with wanted array
        driver = gdal.GetDriverByName('GTiff')

        # out_ds = driver.Create(output_tif_path,xsize,ysize,1,gdal.GDT_Int8)
        out_ds = driver.Create(output_tif_path,xsize,ysize,1,gdal.GDT_Byte)
        out_ds.SetGeoTransform(geotransform)
        out_ds.SetProjection(projection)

        out_band = out_ds.GetRasterBand(1)
        # out_band.WriteArray(array)
        #test: ecriture en bloc pour éviter de corrompre l'ecriture
        block_size = 1830
        rows, cols = array.shape
        for i in range(0, rows, block_size):
            for j in range(0, cols, block_size):
                data_block = array[i:i+block_size, j:j+block_size]
                out_band.WriteArray(data_block, j, i)

        out_band.SetNoDataValue(255)
        out_band.FlushCache()
        out_band = None 