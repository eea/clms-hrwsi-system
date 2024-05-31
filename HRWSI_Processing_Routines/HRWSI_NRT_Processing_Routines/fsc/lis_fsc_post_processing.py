#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import shutil
import numpy as np
from osgeo import gdal
from common.exitcodes import MainInputFileError
from common.file_util import FileUtil
from utils import rewrite_cog, add_quicklook, add_colortable
from geometry.combine_bits_geotiff import bit_bandmath

class LisFscPostProcessing:
    '''
    This class handles the post processng of LIS outputs.
    It generates the GeoTIFFs required for the HR-WSI projects, including the QC layers  and QC flags.
    '''
    product_prefix_name = 'FSC'
    product_version_id = 'V200_1'
    product_folder_name_final = ''
    product_folder_name = ''
    workdir_path = ''

    ALGO_VERSION = '1.11.0'
    ALGO_OUTPUT_FOLDER_NAME = 'output'
    ALGO_STATIC_OUTPUT_PREFIX_NAME = 'LIS_S2-SNOW-FSC_T'
    ALGO_OUTPUT_TMP_FOLDER_NAME = f'{ALGO_OUTPUT_FOLDER_NAME}/tmp'

    BASE_WATER_MASK_FOLDER = 'water_mask'
    BASE_TCD_MASK_FOLDER = 'tcd'
    BASE_WATER_MASK_FILE_NAME = 'WL_2018_20m'
    BASE_TCD_MASK_FILE_NAME = 'TCD_2018_010m_eu_03035_V2_0_20m'
    BASE_L2A_FOLDER = 'L2A'

    postprocessing_auxilliary_files = {
        'WATER': {
            'src_name': '',
            'src_path': ''
        },
        'TCD': {
            'src_name': '',
            'src_path': ''
        },
        'NO_DATA': {
            'src_name': 'no_data_mask.tif',
            'src_path': f'{ALGO_OUTPUT_TMP_FOLDER_NAME}'
        },
        'U_SHADED_SNOW': {
            'src_name': 'uncalibrated_shaded_snow.tif',
            'src_path': f'{ALGO_OUTPUT_TMP_FOLDER_NAME}'
        },
        'HILLSHADE': {
            'src_name': 'hillshade_mask.tif',
            'src_path': f'{ALGO_OUTPUT_TMP_FOLDER_NAME}'
        },
        'GEOPHYSICAL': {
            'src_name': '',
            'src_path': ''
        },
        'L2A': {
            'src_name': '',
            'src_path': ''
        }
    }

    postprocessing_to_retrieve_files = {
        'NDSI': {
            'src_name': 'LIS_NDSI.TIF',
            'src_path': f'{ALGO_OUTPUT_TMP_FOLDER_NAME}',
            'dst_suffix_name': 'NDSI.tif'
        },
        'CLD': {
            'src_name': 'LIS_CLD.tif',
            'src_path': f'{ALGO_OUTPUT_TMP_FOLDER_NAME}',
            'dst_suffix_name': 'CLD.tif'
        }
    }

    postprocessing_to_edit_files = {
        'TOC': {
            'src_name': 'LIS_FSCTOCHS.TIF',
            'src_path': f'{ALGO_OUTPUT_TMP_FOLDER_NAME}',
            'dst_suffix_name': 'FSCTOC.tif'
        },
        'OG': {
            'src_name': '',
            'src_path': f'{ALGO_OUTPUT_FOLDER_NAME}',
            'dst_suffix_name': 'FSCOG.tif'
        }
    }

    postprocessing_to_make_files = {
        'QCFLAGS': {
            'dst_suffix_name': 'QCFLAGS.tif'
        },
        'QCTOC': {
            'dst_suffix_name': 'QCTOC.tif'
        },
        'QCOG': {
            'dst_suffix_name': 'QCOG.tif'
        },
        'GV': {
            'dst_suffix_name': 'GV_mask.tif'
        }
    }

    postprocessing_dictionnaries_input_files = [postprocessing_auxilliary_files, postprocessing_to_retrieve_files, postprocessing_to_edit_files]

    @staticmethod
    def parse_l2a_name(l2a_name:str)->tuple:
        '''
        Exctracts the tile id, the measurement date, and the sat id from a L2A name.
        
        Parameters:
        -----------
            l2a_name (str): the name of the L2A file to be parsed.
        
        Returns:
        --------
            tile_id, measurement_date, sat_id (tuple(str)): the parsed L2A file name.
        '''
        split_l2a_name = l2a_name.split('_')

        sat_name = split_l2a_name[0]
        sat_id = sat_name[-2:]

        raw_measurement_date = split_l2a_name[1]
        split_raw_measurement_day = raw_measurement_date.split('-')
        yyyymmdd = split_raw_measurement_day[0]
        hhmmss = split_raw_measurement_day[1]
        measurement_date = f'{yyyymmdd}T{hhmmss}'

        raw_tile_id = split_l2a_name[3]
        tile_id = raw_tile_id[1:]

        return tile_id, measurement_date, sat_id

    def __init__(self,
                 workdir_path:str,
                 l2a_name:str,
                 tile_id:str='',
                 measurement_date:str='',
                 sat_id:str='') -> None:

        if ('' == tile_id or
            '' == measurement_date or
            '' == sat_id):
            tile_id, measurement_date, sat_id = LisFscPostProcessing.parse_l2a_name(l2a_name)

        self.postprocessing_auxilliary_files['WATER']['src_name'] = f'{self.BASE_WATER_MASK_FILE_NAME}_{tile_id}.tif'
        self.postprocessing_auxilliary_files['WATER']['src_path'] = f'{self.BASE_WATER_MASK_FOLDER}'

        self.postprocessing_auxilliary_files['TCD']['src_name'] = f'{self.BASE_TCD_MASK_FILE_NAME}_{tile_id}.tif'
        self.postprocessing_auxilliary_files['TCD']['src_path'] = f'{self.BASE_TCD_MASK_FOLDER}'

        self.postprocessing_auxilliary_files['L2A']['src_name'] = f'{l2a_name}_FRE_B12.tif'
        self.postprocessing_auxilliary_files['L2A']['src_path'] = f'{self.BASE_L2A_FOLDER}/{l2a_name}'

        self.postprocessing_auxilliary_files['GEOPHYSICAL']['src_name'] = f'{l2a_name}_MG2_R2.tif'
        self.postprocessing_auxilliary_files['GEOPHYSICAL']['src_path'] = f'{self.BASE_L2A_FOLDER}/{l2a_name}/MASKS'

        self.product_folder_name_final = f'{self.product_prefix_name}_{measurement_date}_S{sat_id}_T{tile_id}_{self.product_version_id}'
        self.product_folder_name = f'{self.product_folder_name_final}_tmp'

        self.postprocessing_to_edit_files['OG']['src_name'] = f'{self.ALGO_STATIC_OUTPUT_PREFIX_NAME}{tile_id}_{measurement_date}_{self.ALGO_VERSION}_1.tif'

        self.workdir_path = workdir_path


    def check_post_processing_input_files(self)->None:
        '''
        Method checking whether all the required files for the post-processing stage are available
        at the location they are to be stored.
        
        Returns:
        --------
            Nothing
        
        Raises:
        -------
            MainInputFileError: if post processing required input files are unavailable.
        '''
        missing_input_files = []

        for postprocessing_dict in self.postprocessing_dictionnaries_input_files:

            for value in postprocessing_dict.values():
                file_path = os.path.join(self.workdir_path, value['src_path'], value['src_name'])
                if not os.path.isfile(os.path.join(self.workdir_path, value['src_path'], value['src_name'])):
                    missing_input_files.append(file_path)
        if len(missing_input_files) > 0:
            name_list = ''
            for missing_file in missing_input_files:
                name_list = name_list + ' ' + missing_file
            raise MainInputFileError(
                f'Missing files for LIS FSC post processing. Missing files list: {name_list}'
            )

    def retrieve_cloud_mask(self):
        '''
        Method computing and writting the LIS cloud mask.
        
        Returns:
        --------
            Nothing
        '''
        cloud_mask_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_to_retrieve_files['CLD']['src_path'],
            self.postprocessing_to_retrieve_files['CLD']['src_name']
        )
        cloud_mask_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_retrieve_files["CLD"]["dst_suffix_name"]}'
        )
        l2a_layer_for_no_data_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['L2A']['src_path'],
            self.postprocessing_auxilliary_files['L2A']['src_name']
        )

        source_list = []
        source_list += [{'sources': [{'filepath': cloud_mask_complete_src_path, 'bandnumber': 1, 'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': '(A1!=-10000)*A0'}]


        raster_gdal_info = gdal.Info(cloud_mask_complete_src_path, format='json')

        bit_bandmath(cloud_mask_complete_dst_path,
                     raster_gdal_info,
                     [source_list],
                     compress=False,
                     add_overviews=False,
                     use_default_cosims_config=False)

    def retrieve_geoville_mask(self):
       '''
        Method computing and writting the a boolean mask with 1 for every pixels where either:
            - MAJA found a cloud
            - LIS found snow
            - L2A has no data (-10000)
        
        Returns:
        --------
            Nothing
        '''
       cloud_mask_complete_src_path = os.path.join(
           self.workdir_path,
           self.postprocessing_to_retrieve_files['CLD']['src_path'],
           self.postprocessing_to_retrieve_files['CLD']['src_name']
       )
       l2a_layer_for_no_data_src_path = os.path.join(
           self.workdir_path,
           self.postprocessing_auxilliary_files['L2A']['src_path'],
           self.postprocessing_auxilliary_files['L2A']['src_name']
       )
       lis_fsc_toc_complete_dst_path = os.path.join(
           self.workdir_path,
           self.postprocessing_to_edit_files['TOC']['src_path'],
           self.postprocessing_to_edit_files['TOC']['src_name']
       )
       water_layer_complete_src_path = os.path.join(
           self.workdir_path,
           self.postprocessing_auxilliary_files['WATER']['src_path'],
           self.postprocessing_auxilliary_files['WATER']['src_name']
       )
       geoville_mask_complete_dst_path = os.path.join(
           self.workdir_path,
           self.product_folder_name,
           f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["GV"]["dst_suffix_name"]}'
       )
       source_list = []
       source_list += [{'sources': [{'filepath': cloud_mask_complete_src_path,  'bandnumber': 1, 'unpack_bits': False},
                                    {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1, 'unpack_bits': False},
                                    {'filepath': lis_fsc_toc_complete_dst_path, 'bandnumber': 1, 'unpack_bits': False},
                                    {'filepath': water_layer_complete_src_path, 'bandnumber': 1, 'unpack_bits': False}], \
           'operation': '(A3!=255)*(A3!=253)*(A1!=-10000)*np.logical_or((A0>0),(A2>0)*(A2<=100)) + (A1==-10000)'}]


       raster_gdal_info = gdal.Info(cloud_mask_complete_src_path, format='json')

       bit_bandmath(geoville_mask_complete_dst_path,
                    raster_gdal_info,
                    [source_list],
                    compress=False,
                    add_overviews=False,
                    use_default_cosims_config=False)

    def retrieve_lis_fsc_ndsi_layer(self):
        '''
        Method computing and writting the LIS NDSI layer.
        
        Returns:
        --------
            Nothing
        '''
        ndsi_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_to_retrieve_files['NDSI']['src_path'],
            self.postprocessing_to_retrieve_files['NDSI']['src_name']
        )
        ndsi_layer_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_retrieve_files["NDSI"]["dst_suffix_name"]}'
        )
        water_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['WATER']['src_path'],
            self.postprocessing_auxilliary_files['WATER']['src_name']
        )
        l2a_layer_for_no_data_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['L2A']['src_path'],
            self.postprocessing_auxilliary_files['L2A']['src_name']
        )

        source_list = [{'sources': [{'filepath': ndsi_layer_complete_src_path,  'bandnumber': 1, 'unpack_bits': False},
                                    {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1, 'unpack_bits': False},
                                    {'filepath': water_layer_complete_src_path, 'bandnumber': 1, 'unpack_bits': False}], \
            'operation': 'A0*(A1!=-10000)*(A2!=253)*(A2!=255)*(A0!=205)*(A2!=1)*(A2!=2) + '+\
                         'np.uint8(205)*(A1!=-10000)*(A2!=253)*(A2!=255)*(A0==205) + '+\
                         'np.uint8(255)*((A1==-10000)+(A2==255)+(A2==253)) + '+\
                         'np.uint8(210)*((A2==1)+(A2==2))*(A0<205)'}]
        raster_gdal_info = gdal.Info(ndsi_layer_complete_src_path, format='json')

        bit_bandmath(ndsi_layer_complete_dst_path,
                     raster_gdal_info,
                     [source_list],
                     compress=False,
                     add_overviews=False,
                     use_default_cosims_config=False)

    def make_lis_fsc_toc_layer(self):
        '''
        Method computing and writting the LIS FSC TOC layer.
        
        Returns:
        --------
            Nothing
        '''
        lis_fsc_toc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.postprocessing_to_edit_files['TOC']['src_path'],
            self.postprocessing_to_edit_files['TOC']['src_name']
        )
        water_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['WATER']['src_path'],
            self.postprocessing_auxilliary_files['WATER']['src_name']
        )
        l2a_layer_for_no_data_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['L2A']['src_path'],
            self.postprocessing_auxilliary_files['L2A']['src_name']
        )

        source_list = [{'sources': [{'filepath': lis_fsc_toc_complete_dst_path,  'bandnumber': 1, 'unpack_bits': False},
                                    {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1, 'unpack_bits': False},
                                    {'filepath': water_layer_complete_src_path, 'bandnumber': 1, 'unpack_bits': False}], \
            'operation': 'A0*(A1!=-10000)*(A2!=253)*(A2!=255)*(A0!=205)*(A2!=1)*(A2!=2) + '+\
                         'np.uint8(205)*(A1!=-10000)*(A2!=253)*(A2!=255)*(A0==205) + '+\
                         'np.uint8(255)*((A1==-10000)+(A2==255)+(A2==253)) + '+\
                         'np.uint8(210)*((A2==1)+(A2==2))*(A0<205)'}]

        fsc_toc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["TOC"]["dst_suffix_name"]}'
        )

        raster_gdal_info = gdal.Info(lis_fsc_toc_complete_dst_path, format='json')
        bit_bandmath(fsc_toc_complete_dst_path,
                     raster_gdal_info,
                     [source_list],
                     no_data_values_per_band=[np.uint8(255)],
                     compress=False,
                     add_overviews=False,
                     use_default_cosims_config=False)

    def make_lis_fsc_og_layer(self):
        '''
        Method computing and writting the LIS FSC OG layer.
        
        Returns:
        --------
            Nothing
        '''
        lis_fsc_og_complete_dst_path = os.path.join(
            self.workdir_path,
            self.postprocessing_to_edit_files['OG']['src_path'],
            self.postprocessing_to_edit_files['OG']['src_name']
        )
        water_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['WATER']['src_path'],
            self.postprocessing_auxilliary_files['WATER']['src_name']
        )
        l2a_layer_for_no_data_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['L2A']['src_path'],
            self.postprocessing_auxilliary_files['L2A']['src_name']
        )

        source_list = [{'sources': [{'filepath': lis_fsc_og_complete_dst_path,  'bandnumber': 1, 'unpack_bits': False},
                                    {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1, 'unpack_bits': False},
                                    {'filepath': water_layer_complete_src_path, 'bandnumber': 1, 'unpack_bits': False}], \
            'operation': 'A0*(A1!=-10000)*(A2!=253)*(A2!=255)*(A0!=205)*(A2!=1)*(A2!=2) + '+\
                         'np.uint8(205)*(A1!=-10000)*(A2!=253)*(A2!=255)*(A0==205) + '+\
                         'np.uint8(255)*((A1==-10000)+(A2==255)+(A2==253)) + '+\
                         'np.uint8(210)*((A2==1)+(A2==2))*(A0<205)'}]

        fsc_og_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["OG"]["dst_suffix_name"]}'
        )

        raster_gdal_info = gdal.Info(lis_fsc_og_complete_dst_path, format='json')

        bit_bandmath(fsc_og_complete_dst_path,
                     raster_gdal_info,
                     [source_list],
                     no_data_values_per_band=[np.uint8(255)],
                     compress=False,
                     add_overviews=False,
                     use_default_cosims_config=False)

    def make_lis_fsc_qcflag_layer(self):
        '''
        Method computing and writting the FSC QCFLAGS layer.
        
        Returns:
        --------
            Nothing
        '''
        geophysical_mask_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['GEOPHYSICAL']['src_path'],
            self.postprocessing_auxilliary_files['GEOPHYSICAL']['src_name']
        )
        tcd_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['TCD']['src_path'],
            self.postprocessing_auxilliary_files['TCD']['src_name']
        )
        cloud_mask_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_to_retrieve_files['CLD']['src_path'],
            self.postprocessing_to_retrieve_files['CLD']['src_name']
        )
        hillshade_mask_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['HILLSHADE']['src_path'],
            self.postprocessing_auxilliary_files['HILLSHADE']['src_name']
        )
        uncalibrated_shaded_snow_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['U_SHADED_SNOW']['src_path'],
            self.postprocessing_auxilliary_files['U_SHADED_SNOW']['src_name']
        )
        fsc_toc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["TOC"]["dst_suffix_name"]}'
        )
        water_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['WATER']['src_path'],
            self.postprocessing_auxilliary_files['WATER']['src_name']
        )
        l2a_layer_for_no_data_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['L2A']['src_path'],
            self.postprocessing_auxilliary_files['L2A']['src_name']
        )

        #expert flags
        source_list = []
        #bit 0: MAJA sun too low for an accurate slope correction
        source_list += [{'sources': [{'filepath': geophysical_mask_complete_src_path,'bandnumber': 1,'unpack_bits': True},
                                     {'filepath': water_layer_complete_src_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': {0: '(A1<253)*np.logical_and(A0[:,:,6],A2!=-10000)'}}]
        #bit 1: MAJA sun tangent
        source_list += [{'sources': [{'filepath': geophysical_mask_complete_src_path,'bandnumber': 1,'unpack_bits': True},
                                     {'filepath': water_layer_complete_src_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': {1: '(A1<253)*np.logical_and(A0[:,:,7],A2!=-10000)'}}]
        #bit 2: tree cover density > 90%
        source_list += [{'sources': [{'filepath': tcd_layer_complete_src_path,'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': water_layer_complete_src_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': {2: '(A1<253)*np.logical_and((A0<101)*(A0>90),A2!=-10000)'}}]
        #bit 3: snow detected under thin clouds
        source_list += [{'sources': [{'filepath': cloud_mask_complete_src_path, 'bandnumber': 1, 'unpack_bits': False},
                                     {'filepath': fsc_toc_complete_dst_path, 'bandnumber': 1, 'unpack_bits': False},
                                     {'filepath': water_layer_complete_src_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': {3: '(A2<253)*np.logical_and((A0>0)*(A1>0)*(A1<101),A3!=-10000)'}}]
        #bit 4: tree cover density undefined or unavailable
        source_list += [{'sources': [{'filepath': tcd_layer_complete_src_path, 'bandnumber': 1, 'unpack_bits': False},
                                     {'filepath': water_layer_complete_src_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': {4: '(A1<253)*np.logical_and((A0==1)*(A0>100),A2!=-10000)'}}]
        #bit 5: hillshade coverage
        source_list += [{'sources': [{'filepath': hillshade_mask_src_path, 'bandnumber': 1, 'unpack_bits': False},
                                     {'filepath': water_layer_complete_src_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': {5: '(A1<253)*np.logical_and(A0==1,A2!=-10000)'}}]
        #bit 6: shaded snow found with specific hillshade thresholds
        source_list += [{'sources': [{'filepath': uncalibrated_shaded_snow_src_path, 'bandnumber': 1, 'unpack_bits': False},
                                     {'filepath': water_layer_complete_src_path, 'bandnumber': 1,'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': {6: '(A1<253)*np.logical_and(A0==1,A2!=-10000)'}}]

        fsc_qcflags_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QCFLAGS"]["dst_suffix_name"]}'
        )

        raster_gdal_info = gdal.Info(fsc_toc_complete_dst_path, format='json')

        bit_bandmath(fsc_qcflags_complete_dst_path,
                     raster_gdal_info,
                     [source_list],
                     compress=False,
                     add_overviews=False,
                     use_default_cosims_config=False)

    def make_lis_fsc_qctoc_layer(self):
        '''
        Method computing and writting the FSC TOC QC layer.
        
        Returns:
        --------
            Nothing
        '''
        fsc_qcflags_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QCFLAGS"]["dst_suffix_name"]}'
        )
        fsc_toc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["TOC"]["dst_suffix_name"]}'
        )
        l2a_layer_for_no_data_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['L2A']['src_path'],
            self.postprocessing_auxilliary_files['L2A']['src_name']
        )

        #QC layer top of canopy
        #[0: highest quality, 1: lower quality, 2: decreasing quality, 3: lowest quality, 205: cloud mask, 255: no data]
        source_list = []
        source_list += [{'sources': [{'filepath': fsc_qcflags_complete_dst_path, 'bandnumber': 1, 'unpack_bits': True},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': '(A1==-10000)*np.uint8(255)+(A1!=-10000)*np.minimum(B*0+3,(4-np.maximum(B*0, (100.-30.*A0[:,:,1]-50.*A0[:,:,0]-25.*A0[:,:,3]-25.*A0[:,:,2])/25.))).astype(np.uint8)'}]
        #values 205, 210 and 255 from FSCTOC snow product
        source_list += [{'sources': [{'filepath': fsc_toc_complete_dst_path, 'bandnumber': 1, 'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': '(A1==-10000)*np.uint8(255)+(A1!=-10000)*(B*(A0!=205)*(A0!=255)*(A0!=210) + np.uint8(205)*(A0==205) + np.uint8(210)*(A0==210) + np.uint8(255)*(A0==255))'}]

        fsc_qctoc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QCTOC"]["dst_suffix_name"]}'
        )

        raster_gdal_info = gdal.Info(fsc_toc_complete_dst_path, format='json')

        bit_bandmath(fsc_qctoc_complete_dst_path,
                     raster_gdal_info,
                     [source_list],
                     no_data_values_per_band=[np.uint8(255)],
                     compress=False,
                     add_overviews=False,
                     use_default_cosims_config=False)

    def make_lis_fsc_qcog_layer(self):
        '''
        Method computing and writting the FSC OG QC layer.
        
        Returns:
        --------
            Nothing
        '''
        fsc_qcflags_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QCFLAGS"]["dst_suffix_name"]}'
        )
        fsc_og_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["OG"]["dst_suffix_name"]}'
        )
        tcd_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['TCD']['src_path'],
            self.postprocessing_auxilliary_files['TCD']['src_name']
        )
        l2a_layer_for_no_data_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['L2A']['src_path'],
            self.postprocessing_auxilliary_files['L2A']['src_name']
        )

        #QC layer on ground
        #[0: highest quality, 1: lower quality, 2: decreasing quality, 3: lowest quality, 205: cloud mask, 255: no data]
        source_list = []
        source_list += [{'sources': [{'filepath': fsc_qcflags_complete_dst_path, 'bandnumber': 1, 'unpack_bits': True},
                                     {'filepath': tcd_layer_complete_src_path, 'bandnumber': 1, 'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': '(A2==-10000)*np.uint8(255)+(A2!=-10000)*np.minimum(B*0+3,(4-np.maximum(B*0, (100.-30.*A0[:,:,1]-50.*A0[:,:,0]-25.*A0[:,:,3]-25.*A0[:,:,2]-80.*A1)/25.))).astype(np.uint8)'}]
        #values 205, 210 and 255 from FSCOG snow product
        source_list += [{'sources': [{'filepath': fsc_og_complete_dst_path, 'bandnumber': 1, 'unpack_bits': False},
                                     {'filepath': l2a_layer_for_no_data_src_path,'bandnumber': 1,'unpack_bits': False}], \
            'operation': '(A1==-10000)*np.uint8(255)+(A1!=-10000)*(B*(A0!=205)*(A0!=255)*(A0!=210) + np.uint8(205)*(A0==205) + np.uint8(210)*(A0==210) + np.uint8(255)*(A0==255))'}]

        fsc_qcog_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QCOG"]["dst_suffix_name"]}'
        )

        raster_gdal_info = gdal.Info(fsc_og_complete_dst_path, format='json')

        bit_bandmath(fsc_qcog_complete_dst_path,
                     raster_gdal_info,
                     [source_list],
                     no_data_values_per_band=[np.uint8(255)],
                     compress=False,
                     add_overviews=False,
                     use_default_cosims_config=False)

    def retrieve_product_files(self):
        '''
        Method launching the extraction of LIS results and their adaptation as FSC product layers.
        The computed layers are:
            - LIS Cloud Mask layer
            - LIS NDSI layer
            - Geoville binary MAJA cloud & snow & nodata mask

        Returns:
        --------
            Nothing
        '''
        self.retrieve_cloud_mask()
        self.retrieve_lis_fsc_ndsi_layer()
        self.retrieve_geoville_mask()

    def edit_product_files(self):
        '''
        Method launching the edition of LIS results as FSC product layers.
        The computed layers are:
            - FSC TOC layer
            - FSC OG layer
        
        Returns:
        --------
            Nothing
        '''
        self.make_lis_fsc_toc_layer()
        self.make_lis_fsc_og_layer()

    def make_quality_files(self):
        '''
        Method launching the computation of FSC quality layers.
        The computed layers are:
            - QCFLAGS
            - FSC TOC QC layer
            - FSC OG QC layer
        
        Returns:
        --------
            Nothing
        '''
        self.make_lis_fsc_qcflag_layer()
        self.make_lis_fsc_qctoc_layer()
        self.make_lis_fsc_qcog_layer()

    def make_metadata_and_xml_files(self):
        '''
        TODO
        '''
        pass

    def fsc_product_main_layers_creation(self):
        '''
        Method orchestrating the computation of the eventual FSC product layers.
        It also compresses the output layers in COG format.
        Eventually, it launches the computation of JSON and XML files for indexation purposes.
        
        Returns:
        --------
            Nothing
        '''
        
        FileUtil.make_dir(
            os.path.join(
                self.workdir_path, self.product_folder_name
            )
        )
        self.check_post_processing_input_files()
        self.retrieve_product_files()
        self.edit_product_files()
        self.make_quality_files()
        add_colortable.add_colortable_to_files(
            os.path.join(
                self.workdir_path, self.product_folder_name
            ),
            product_tag=self.product_folder_name_final
        )
        rewrite_cog.rewrite_cog(
            os.path.join(
                self.workdir_path, self.product_folder_name
            ),
            os.path.join(
                self.workdir_path, self.product_folder_name_final
            )
        )
        add_quicklook.add_quicklook(
            os.path.join(self.workdir_path, self.product_folder_name_final),'_FSCTOC.tif'
        )
        self.make_metadata_and_xml_files()

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='This script is used to process FSC from an L2A tile')
    parser.add_argument("--workdir", type=str, required=True, help='output directory')
    parser.add_argument("--tile_id", type=str, default='', help='output directory')
    parser.add_argument("--measurement_date", type=str, default='', help='output directory')
    parser.add_argument("--sat_id", type=str, default='', help='output directory')
    parser.add_argument("--l2a_name", type=str, required=True, help='output directory')
    args = parser.parse_args()

    lis_fsc_pos_processing = LisFscPostProcessing(args.workdir,
                                                  args.l2a_name,
                                                  args.tile_id,
                                                  args.measurement_date,
                                                  args.sat_id
    )
    lis_fsc_pos_processing.fsc_product_main_layers_creation()
