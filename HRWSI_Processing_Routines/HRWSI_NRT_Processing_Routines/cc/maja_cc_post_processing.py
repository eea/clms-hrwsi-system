#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
from typing import Tuple
import numpy as np
from osgeo import gdal
gdal.DontUseExceptions()
from common.exitcodes import MainInputFileError
from common.file_util import FileUtil
from utils import rewrite_cog, add_quicklook, add_colortable
from geometry.combine_bits_geotiff import bit_bandmath

class MajaCcPostProcessing:
    '''
    Class managing the output of MAJA and making it into an HR-WSI product 
    Cloud Classification (CC).
    '''

    # Attributes, amongst which some that are initialized when the class is instantiated,
    # corresponding to path depending on the L2a name.
    product_prefix_name = 'CC'
    product_version_id = 'V100_0'
    product_folder_name_final = ''
    product_folder_name = ''
    workdir_path = ''

    ALGO_VERSION = '4.5.3'
    ALGO_OUTPUT_FOLDER_NAME = "output"

    """
    Dictionnary of the auxilliary files used to make the various files of the product.
    """
    postprocessing_auxilliary_files = {
        'CLOUD': {
            'src_name': '',
            'src_path': ''
        },
        'NO_DATA': {
            'src_name': '', 
            'src_path': ''
        },
        'GEOPHYSICAL': {
            'src_name': '',
            'src_path': ''
        }
    }

    """
    Dictionnary of the files from the outputs of the MAJA algorithm, already corresponding 
    to one of the files of the product.
    """
    postprocessing_to_retrieve_files = {

    }

    """
    Dictionnary of the files from the outputs of the MAJA algorithm that only need minor modifications 
    to fit the product.
    """
    postprocessing_to_edit_files = {

    }

    """
    Dictionnary of the files that are to be made from scratch.
    """
    postprocessing_to_make_files = {
        'CC': {
            'dst_suffix_name': 'CC.tif'
        },
        'QCFLAGS': {
            'dst_suffix_name': 'QCFLAGS.tif'
        },
        'QC': {
            'dst_suffix_name': 'QC.tif'
        }
    }

    '''List of all the files dictionnaries containing input files for the post processing.'''
    postprocessing_dictionnaries_input_files = [
        postprocessing_auxilliary_files,
        postprocessing_to_retrieve_files,
        postprocessing_to_edit_files
    ]

    @staticmethod
    def parse_l2a_name(l2a_name:str) -> Tuple[str, str, str]:
        '''
        From the name of the L2A, retrieve basic information such as sat name, tile id, 
        measurement date.

        :param str l2a_name: name of the L2A to post process

        :returns: a tuple of three strings, the tile id, the measurement date and the satellite id.

        '''
        print('parse l2a')
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

    def __init__(
        self, workdir_path:str, l2a_name:str, tile_id:str='',
        measurement_date:str='', sat_id:str=''
    ) -> None:
        '''
        Initialize the instance with specific data from the L2A name.

        :param workdir_path: the absolute path where the output repository, the auxilliaries are found, 
            and where the product will be stored.
        :param l2a_name: name of the L2A to post process.
        :param tile_id: the id of the tile that was processed by the MAJA algorithm.
        :param measurement_date: the date of measurement of the L1C, format is yyyymmddThhmmss.
        :param sat_id: the id of the staellite responsible for the adquisition of the image.

        :returns: nothing.
        '''

        print(tile_id)
        if ('' == tile_id or '' == measurement_date or '' == sat_id):
            tile_id, measurement_date, sat_id = MajaCcPostProcessing.parse_l2a_name(l2a_name)

        print(tile_id)

        self.postprocessing_auxilliary_files['GEOPHYSICAL']['src_name'] = f'{l2a_name}_MG2_R2.tif'
        self.postprocessing_auxilliary_files['GEOPHYSICAL']['src_path'] = f'{self.ALGO_OUTPUT_FOLDER_NAME}/{l2a_name}/MASKS'

        self.postprocessing_auxilliary_files['NO_DATA']['src_name'] = f'{l2a_name}_EDG_R2.tif'
        self.postprocessing_auxilliary_files['NO_DATA']['src_path'] = f'{self.ALGO_OUTPUT_FOLDER_NAME}/{l2a_name}/MASKS'

        self.postprocessing_auxilliary_files['CLOUD']['src_name'] = f'{l2a_name}_CLM_R2.tif'
        self.postprocessing_auxilliary_files['CLOUD']['src_path'] = f'{self.ALGO_OUTPUT_FOLDER_NAME}/{l2a_name}/MASKS'

        self.product_folder_name_final = f'{self.product_prefix_name}_{measurement_date}_S{sat_id}_T{tile_id}_{self.product_version_id}'
        self.product_folder_name = f'{self.product_folder_name_final}_tmp'
        self.workdir_path = workdir_path

    def check_post_processing_input_files(self) -> None:
        '''
        Check all the input files and raise a custom Exception if one or many are missing. Log the name of the 
        missing files for debug purposes.

        :raises MainInputFileError: specific Exception corresponding to an essential input file missing.
        '''
        missing_input_files = []

        for postprocessing_dict in self.postprocessing_dictionnaries_input_files:

            for value in postprocessing_dict.values():
                file_path = os.path.join(self.workdir_path, value['src_path'], value['src_name'])
                if not os.path.isfile(
                    os.path.join(
                        self.workdir_path,
                        value['src_path'],
                        value['src_name']
                    )
                ):
                    missing_input_files.append(file_path)
        if len(missing_input_files) > 0:
            name_list = ''
            for missing_file in missing_input_files:
                name_list = name_list + ' ' + missing_file
            raise MainInputFileError(
                f'Missing files for MAJA CM post processing. Missing files list: {name_list}'
            )

    def make_maja_cc_cc_layer(self):
        '''
        Generates the main layer of the Cloud Classification, the Cloud Classification layer.
        '''

        # The complete path of the auxilliary files used to generated the CC layer.
        cloud_mask_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['CLOUD']['src_path'],
            self.postprocessing_auxilliary_files['CLOUD']['src_name']
        )
        no_data_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['NO_DATA']['src_path'],
            self.postprocessing_auxilliary_files['NO_DATA']['src_name']
        )

        source_list = []

        # Main operation to generate the CC layer.
        # Sets NO_DATA value (uint8(255)) where the NO_DATA mask is active.
        # Sets value 3 where there is cloud shadow or projected shadow, and no cloud
        # Sets value 2 where there is cloud except high clouds
        # Sets value 1 where there is high clouds
        # Sets value 0 where there is no cloud nor shadow
        source_list += [{
            'sources': [
                {
                    'filepath': cloud_mask_complete_src_path,
                    'bandnumber': 1,
                    'unpack_bits': True
                },
                {
                    'filepath': no_data_layer_complete_src_path,
                    'bandnumber': 1,
                    'unpack_bits': False
                }
            ], \
            'operation': 'A1*np.uint8(255) + (1-A1)*(B*0 + 3*np.logical_or(A0[:,:,5],A0[:,:,6])*(1-A0[:,:,7])*(1-A0[:,:,1]) + 1*A0[:,:,7] + 2*A0[:,:,1]*(1-A0[:,:,7]))'
        }]

        # Final CC layer file path and name
        maja_cc_cc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["CC"]["dst_suffix_name"]}'
        )
        raster_gdal_info = gdal.Info(cloud_mask_complete_src_path, format='json')

        bit_bandmath(
            maja_cc_cc_complete_dst_path,
            raster_gdal_info,
            [source_list],
            compress=False,
            no_data_values_per_band=[np.uint8(255)],
            add_overviews=False,
            use_default_cosims_config=False
        )

    def make_maja_cc_qcflag_layer(self):
        '''
        Generate the QCFLAGS mask of the CC product.
        '''

        # The complete path of the auxilliary files used to generated the CC layer.
        geophysical_mask_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['GEOPHYSICAL']['src_path'],
            self.postprocessing_auxilliary_files['GEOPHYSICAL']['src_name']
        )
        cloud_mask_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['CLOUD']['src_path'],
            self.postprocessing_auxilliary_files['CLOUD']['src_name']
        )
        maja_cc_cc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["CC"]["dst_suffix_name"]}'
        )

        #expert flags
        source_list = []
        #bit 0: Clouds detected via mono-temporal thresholds
        #bit 1: Clouds detected via multi-temporal thresholds
        #bit 2: thinnest clouds
        #bit 3: Cloud shadows cast by a detected cloud
        #bit 4: Cloud shadows cast by a cloud outside image
        source_list += [{
            'sources': [{
                'filepath': cloud_mask_complete_src_path, 
                'bandnumber': 1, 
                'unpack_bits': True
            }], \
            'operation': {
                0: 'A0[:,:,2]',
                1: 'A0[:,:,3]',
                2: 'A0[:,:,4]',
                3: 'A0[:,:,5]',
                4: 'A0[:,:,6]'
            }
        }]
        #bit 5: Water
        source_list += [{
            'sources': [{
                'filepath': geophysical_mask_complete_src_path, 
                'bandnumber': 1, 
                'unpack_bits': True
            }], \
            'operation': {
                5: 'A0[:,:,0]'
            }
        }]

        # Final QCFLAGS mask file path and name
        cc_qcflags_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QCFLAGS"]["dst_suffix_name"]}'
        )
        raster_gdal_info = gdal.Info(maja_cc_cc_complete_dst_path, format='json')

        bit_bandmath(
            cc_qcflags_complete_dst_path, raster_gdal_info, 
            [source_list], compress=False, add_overviews=False,
            use_default_cosims_config=False
        )

    def make_maja_cc_qc_layer(self):
        '''
        Generate the QC layer of the CC product.
        '''

        # The complete path of the auxilliary files used to generated the CC layer.
        cc_qcflags_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QCFLAGS"]["dst_suffix_name"]}'
        )
        maja_cc_cc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["CC"]["dst_suffix_name"]}'
        )
        no_data_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['NO_DATA']['src_path'],
            self.postprocessing_auxilliary_files['NO_DATA']['src_name']
        )

        #QC layer for Cloud Layer
        #0: highest quality,
        #1: lower quality,
        #2: decreasing quality,
        #3: lowest quality
        #255: from EDGE mask
        source_list = []
        source_list += [{
            'sources': [
                {
                    'filepath': cc_qcflags_complete_dst_path, 
                    'bandnumber': 1, 
                    'unpack_bits': True
                },
                {
                    'filepath': no_data_layer_complete_src_path, 
                    'bandnumber': 1, 
                    'unpack_bits': False
                }
            ], \
            'operation': 'A1*np.uint8(255) + (1-A1)*(B*0+1*A0[:,:,4]).astype(np.uint8)'
        }]

        # Final QC layer file path and name
        cc_qc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QC"]["dst_suffix_name"]}'
        )
        raster_gdal_info = gdal.Info(maja_cc_cc_complete_dst_path, format='json')

        bit_bandmath(
            cc_qc_complete_dst_path,
            raster_gdal_info, [source_list],
            no_data_values_per_band=[np.uint8(255)],
            compress=False,
            add_overviews=False,
            use_default_cosims_config=False
        )

    def retrieve_product_files(self):
        '''
        Retrieve files from the MAJA algorithm outputs to integrate them directly as a
        product file.
        For MAJA CC products, there is no product from MAJA algorithm outputs to retrieve as is.
        '''

    def edit_product_files(self):
        '''
        Do minor updates to a file from the MAJA algorithm outputs and then integrate it as a 
        product file.
        For MAJA CC products, there is no product from MAJA algorithm outputs to edit.
        '''

    def make_main_layer_files(self):
        '''
        Generate new files corresponding to main layers of the product, on the basis of 
        auxilliary files and output files from the MAJA algorithm.

        For MAJA CC products, the main layers to create are:
            - Cloud Classification
        '''

    def make_quality_files(self):
        '''
        Generate new files to assess product quality, on the basis of auxilliary files 
        and output files from the MAJA algorithm.

        For MAJA CC products, the quality files are:
            - QCFLAGS mask
            - QC layer
        '''
        self.make_maja_cc_cc_layer()
        self.make_maja_cc_qcflag_layer()
        self.make_maja_cc_qc_layer()

    def make_metadata_and_xml_files(self):
        '''
        Generate XML and metadata files 
        '''
        #TODO

    def product_main_layers_creation(self):
        '''
        Manage the creation of the product layers, from the ouputs of the MAJA algorithm.
        '''

        # If needed create the repository corresponding to the product.
        FileUtil.make_dir(
            os.path.join(
                self.workdir_path, self.product_folder_name
            )
        )
        self.check_post_processing_input_files()
        # Fill the product folder with all the main layers files.
        self.retrieve_product_files()
        self.edit_product_files()
        self.make_main_layer_files()
        self.make_quality_files()
        # Implement colortable.
        add_colortable.add_colortable_to_files(
            os.path.join(
                self.workdir_path, self.product_folder_name
            ),
            product_tag=self.product_folder_name_final
        )
        # Make the product folder a Cloud Optimized Geotiff (COG).
        rewrite_cog.rewrite_cog(
            os.path.join(
                self.workdir_path, self.product_folder_name
            ),
            os.path.join(
                self.workdir_path, self.product_folder_name_final
            )
        )
        # Generate a quicklook for easy visualization.
        add_quicklook.add_quicklook(
            os.path.join(
                self.workdir_path, self.product_folder_name_final
            ),
            f'_{self.postprocessing_to_make_files["CC"]["dst_suffix_name"]}'
        )
        # Generate metadata and xml files.
        self.make_metadata_and_xml_files()



if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(
        description='This script is used to post-process CC from an L2A tile'
    )
    parser.add_argument(
        "--workdir", type=str, required=True, help='output directory'
    )
    parser.add_argument(
        "--tile_id", type=str, default='', required=False, help='output directory'
    )
    parser.add_argument(
        "--measurement_date", type=str, default='', required=False, help='output directory'
    )
    parser.add_argument(
        "--sat_id", type=str, default='', required=False, help='output directory'
    )
    parser.add_argument(
        "--l2a_name", type=str, required=True, help='output directory'
    )

    args = parser.parse_args()

    maja_cc_post_processing = MajaCcPostProcessing(
        args.workdir, args.l2a_name, args.tile_id, args.measurement_date, args.sat_id
    )
    maja_cc_post_processing.product_main_layers_creation()
