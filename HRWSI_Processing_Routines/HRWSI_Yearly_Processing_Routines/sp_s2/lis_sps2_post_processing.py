#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
from datetime import datetime
import numpy as np
import rasterio
from osgeo import gdal
from common.exitcodes import MainInputFileError
from common.file_util import FileUtil
from utils import rewrite_cog, add_quicklook, add_colortable
from geometry.combine_bits_geotiff import bit_bandmath

class LisSpS2PostProcessing:
    '''
    TODO
    '''
    product_prefix_name = 'SP'
    product_version_id = 'V100_1'
    product_folder_name_final = ''
    product_folder_name = ''
    workdir_path = ''

    ALGO_VERSION = '1.11.0'
    ALGO_INPUT_FOLDER_NAME = 'input'
    ALGO_OUTPUT_FOLDER_NAME = 'output'
    ALGO_STATIC_OUTPUT_PREFIX_NAME = 'LIS_S2-SNOW'
    ALGO_OUTPUT_TMP_FOLDER_NAME = f'{ALGO_OUTPUT_FOLDER_NAME}/tmp'

    BASE_WATER_MASK_FOLDER = 'water_mask'
    BASE_TCD_MASK_FOLDER = 'tcd'
    BASE_WATER_MASK_FILE_NAME = 'WL_2018_20m'
    BASE_TCD_MASK_FILE_NAME = 'TCD_2018_010m_eu_03035_V2_0_20m'
    BASE_L2A_FOLDER = 'L2A'

    input_dates = []
    output_dates = []
    input_margin_dates = []
    output_margin_dates =[]
    date_start:datetime.date
    date_end:datetime.date

    postprocessing_auxilliary_files = {
        'WATER': {
            'src_name': '',
            'src_path': ''
        },
        'TCD': {
            'src_name': '',
            'src_path': ''
        },
        'INPUT_DATES': {
            'src_name': 'input_dates.txt',
            'src_path': f'{ALGO_OUTPUT_TMP_FOLDER_NAME}'
        },
        'OUTPUT_DATES': {
            'src_name': 'output_dates.txt',
            'src_path': f'{ALGO_OUTPUT_TMP_FOLDER_NAME}'
        },
        'MULTITEMP_INPUT_SNOW_MASKS': {
            'src_name': 'multitemp_snow100.tif',
            'src_path': f'{ALGO_OUTPUT_TMP_FOLDER_NAME}'
        }
    }

    postprocessing_to_retrieve_files = {

    }

    postprocessing_to_edit_files = {
        'SMOD': {
            'src_name': '',
            'src_path': f'{ALGO_OUTPUT_FOLDER_NAME}',
            'dst_suffix_name': 'SCM.tif'
        },
        'SCD': {
            'src_name': '',
            'src_path': f'{ALGO_OUTPUT_FOLDER_NAME}',
            'dst_suffix_name': 'SCD.tif'
        },
        'SOD': {
            'src_name': '',
            'src_path': f'{ALGO_OUTPUT_FOLDER_NAME}',
            'dst_suffix_name': 'SCO.tif'
        },
        'NOBS': {
            'src_name': '',
            'src_path': f'{ALGO_OUTPUT_FOLDER_NAME}',
            'dst_suffix_name': 'NOBS.tif'
        }
    }

    postprocessing_to_make_files = {
        'QCFLAGS': {
            'dst_suffix_name': 'QCFLAGS.tif'
        },
        'QC': {
            'dst_suffix_name': 'QC.tif'
        },
        'QCOD': {
            'dst_suffix_name': 'QCOD.tif'
        },
        'QCMD': {
            'dst_suffix_name': 'QCMD.tif'
        },
        'QCMEAN': {
            'dst_suffix_name': 'mean_QC.tif'
        },
        'QCMEDIAN': {
            'dst_suffix_name': 'median_QC.tif'
        }
    }

    postprocessing_dictionnaries_input_files = [
        postprocessing_auxilliary_files,
        postprocessing_to_retrieve_files,
        postprocessing_to_edit_files
    ]

    def __init__(
        self, workdir_path, tile_id,
        start_date, end_date
    ) -> None:

        self.postprocessing_auxilliary_files['WATER']['src_name'] = f'{self.BASE_WATER_MASK_FILE_NAME}_{tile_id}.tif'
        self.postprocessing_auxilliary_files['WATER']['src_path'] = f'{self.BASE_WATER_MASK_FOLDER}/{tile_id}'

        self.postprocessing_auxilliary_files['TCD']['src_name'] = f'{self.BASE_TCD_MASK_FILE_NAME}_{tile_id}.tif'
        self.postprocessing_auxilliary_files['TCD']['src_path'] = f'{self.BASE_TCD_MASK_FOLDER}/{tile_id}'

        self.product_folder_name_final = f'{self.product_prefix_name}_S2_{start_date}-{end_date}_T{tile_id}_{self.product_version_id}'
        self.product_folder_name = f'{self.product_folder_name_final}_tmp'

        for key, value, in self.postprocessing_to_edit_files.items():
            value['src_name'] = f'{self.ALGO_STATIC_OUTPUT_PREFIX_NAME}-{key}_T{tile_id}_{start_date}_{end_date}_{self.ALGO_VERSION}.tif'
        self.workdir_path = workdir_path
        self.date_start = datetime.strptime(start_date, '%Y%m%d')
        self.date_end = datetime.strptime(end_date, '%Y%m%d')
        print(self.date_start)
        print(self.date_end)
        self.read_input_output_dates()

    @staticmethod
    def read_dates_file(dates_file_path):
        '''
        TODO
        '''
        with open(dates_file_path, "r", encoding="utf-8") as idf:
            dates_raw = idf.readlines()

        dates = [
            datetime.strptime(input_date.strip(), '%Y%m%d') for input_date in dates_raw
        ]
        return dates

    def build_dates(self, margin_dates):
        '''
        TODO
        '''
        dates = []

        for margin_date in margin_dates:
            if margin_date<self.date_start:
                continue
            if margin_date>self.date_end:
                continue
            dates.append(margin_date)
        return dates

    def read_input_output_dates(self):
        '''
        TODO
        '''
        if len(self.input_margin_dates) == 0:
            sp_input_dates_src_complete_path = os.path.join(
                self.workdir_path,
                self.postprocessing_auxilliary_files['INPUT_DATES']['src_path'],
                self.postprocessing_auxilliary_files['INPUT_DATES']['src_name']
            )
            self.input_margin_dates = LisSpS2PostProcessing.read_dates_file(
                sp_input_dates_src_complete_path
            )
            self.input_dates = self.build_dates(self.input_margin_dates)
        if len(self.output_margin_dates) == 0:
            sp_output_dates_src_complete_path = os.path.join(
                self.workdir_path,
                self.postprocessing_auxilliary_files['OUTPUT_DATES']['src_path'],
                self.postprocessing_auxilliary_files['OUTPUT_DATES']['src_name']
            )
            self.output_margin_dates = LisSpS2PostProcessing.read_dates_file(
                sp_output_dates_src_complete_path
            )
            self.output_dates = self.build_dates(self.output_margin_dates)

    def write_raster_from_ndarray(
            self,
            raster_name='raster.tif',
            data_array=None,
            nb_col=0,
            nb_row=0,
            nb_band=0,
            driver=None,
            geo_transform=None,
            projection=None,
            raster_data_type=gdal.GDT_Byte,
            no_data_value=np.uint16(65535)
        ):
        '''
        TODO
        '''
        print(driver)
        output_raster = driver.Create(
            os.path.join(
                self.workdir_path,
                self.product_folder_name,
                raster_name
            ),
            nb_col,
            nb_row,
            nb_band,
            raster_data_type
        )

        output_band = output_raster.GetRasterBand(1)
        output_band.WriteArray(data_array,0,0)
        output_band.FlushCache()
        output_band.SetNoDataValue(no_data_value)

        output_raster.SetGeoTransform(geo_transform)
        output_raster.SetProjection(projection)

    def check_post_processing_input_files(self):
        '''
        TODO
        '''
        missing_input_files = []

        for postprocessing_dict in self.postprocessing_dictionnaries_input_files:

            for value in postprocessing_dict.values():
                file_path = os.path.join(
                    self.workdir_path,
                    value['src_path'],
                    value['src_name']
                )
                if not file_path:
                    missing_input_files.append(file_path)

        if missing_input_files:
            name_list = ''
            for missing_file in missing_input_files:
                name_list = name_list + ' ' + missing_file
            raise MainInputFileError(
                f'Missing files for LIS SP post processing. Missing files list: {name_list}'
            )

    def calculate_qc_files_list_stats(self, qc_files_list):
        '''
        TODO
        '''
        qc_histo = np.array([])
        qc_mean = np.array([])
        valid_pixel_counter = np.array([])
        for qc_file in qc_files_list:
            ds = gdal.Open(qc_file)
            band = ds.GetRasterBand(1)
            if not qc_mean.any():
                masked_band = band.ReadAsArray().astype(np.uint8)
                valid_pixels = masked_band<=3
                # In here we are storing the iterrations of 0, 1, 2, and 3.
                qc_histo = np.zeros([masked_band.shape[0],
                                      masked_band.shape[1],
                                      4], dtype=np.uint8)
                for value in range(4):
                    qc_histo[:,:,value] += (masked_band==value).astype(np.uint8)
                masked_band = masked_band*valid_pixels

                valid_pixel_counter = valid_pixels.astype(np.uint8)
                qc_mean = masked_band.astype(np.uint16)

                del ds, band
                continue
            masked_band = band.ReadAsArray().astype(np.uint8)
            for value in range(4):

                qc_histo[:,:,value] = qc_histo[:,:,value] + (masked_band==value).astype(np.uint8)
            valid_pixels = masked_band<=3
            masked_band = masked_band*valid_pixels

            valid_pixel_counter = valid_pixel_counter + valid_pixels.astype(np.uint8)
            qc_mean = masked_band.astype(np.uint16) + qc_mean.astype(np.uint16)


            del ds, band
        qc_mean = qc_mean / valid_pixel_counter.astype(float)
        qc_mean[valid_pixel_counter==0] = 255

        input_raster = gdal.Open(qc_files_list[0])
        (
            input_col, input_row, _, input_driver,
            input_geo_transform, input_projection
        ) = LisSpS2PostProcessing.get_raster_info(input_raster)

        print('calculate_qc_files_list_stats > write mean raster')
        self.write_raster_from_ndarray(
            raster_name = self.postprocessing_to_make_files['QCMEAN']['dst_suffix_name'],
            data_array = qc_mean,
            nb_col = input_col,
            nb_row = input_row,
            nb_band = 1,
            driver = input_driver,
            geo_transform = input_geo_transform,
            projection = input_projection,
            raster_data_type=gdal.GDT_Float32,
            no_data_value=255
        )

        del input_raster, qc_mean

        qc_histo_sumed = np.zeros(qc_histo.shape)
        for i in range(4):
            qc_histo_sumed[:,:,i] = np.sum(qc_histo[:,:,:i+1], axis=2)

        qc_histo_sumed = np.array([value * (qc_histo_sumed[:,:,value]>= valid_pixel_counter/2) +\
                    255 * (qc_histo_sumed[:,:,value]<valid_pixel_counter/2) for value in range(4)])
        qc_median = np.min(qc_histo_sumed, axis=0)

        # print('calculate_qc_files_list_stats > get input raster')
        input_raster = gdal.Open(qc_files_list[0])
        (
            input_col, input_row, _, input_driver,
            input_geo_transform, input_projection
        ) = LisSpS2PostProcessing.get_raster_info(input_raster)

        qc_median[valid_pixel_counter==0] = 255

        print('calculate_qc_files_list_stats > write median raster')
        self.write_raster_from_ndarray(
            raster_name = self.postprocessing_to_make_files['QCMEDIAN']['dst_suffix_name'],
            data_array = qc_median,
            nb_col = input_col,
            nb_row = input_row,
            nb_band = 1,
            driver = input_driver,
            geo_transform = input_geo_transform,
            projection = input_projection,
            raster_data_type=gdal.GDT_Float32,
            no_data_value=255
        )

    def make_lis_sps2_qcmean_qcmedian_layer(self):
        '''
        TODO
        '''
        sps2_input_folder_complete_path = os.path.join(
            self.workdir_path,
            self.ALGO_INPUT_FOLDER_NAME
        )

        input_fsc_list = os.listdir(sps2_input_folder_complete_path)
        input_fsc_qc_list = [
            os.path.join(
                sps2_input_folder_complete_path,
                fsc_name,
                f'{fsc_name}_QCOG.tif'
            )
            for fsc_name in input_fsc_list
        ]
        self.calculate_qc_files_list_stats(input_fsc_qc_list)

    def make_lis_sps2_qcflags_layer(self):
        '''
        TODO
        '''
        tcd_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['TCD']['src_path'],
            self.postprocessing_auxilliary_files['TCD']['src_name']
        )
        sp_scd_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["SCD"]["dst_suffix_name"]}'
        )
        sp_qcmean_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.postprocessing_to_make_files["QCMEAN"]["dst_suffix_name"]}'
        )
        water_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['WATER']['src_path'],
            self.postprocessing_auxilliary_files['WATER']['src_name']
        )

        #expert flags
        source_list = []
        #bit 0: Snow Cover Duration (from SCD file) too low (under threshold = 60)
        source_list += [
            {
                'sources': [
                    {
                        'filepath': sp_scd_complete_dst_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    },
                    {
                        'filepath': water_layer_complete_src_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    }
                ], \
                'operation': {
                    4: '(A0<60)*((A1==0)+(A1==254))'
                }
            }
        ]
        #bit 1: tree cover density > 90%
        source_list += [
            {
                'sources': [
                    {
                        'filepath': tcd_layer_complete_src_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    },
                    {
                        'filepath': water_layer_complete_src_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    }
                ], \
                'operation': {
                    5: '(A0<101)*(A0>90) * ((A1==0)+(A1==254))'
                }
            }
        ]
        #bit 2: rounded mean QC of input FSC products is 0
        #bit 3: rounded mean QC of input FSC products is 1
        #bit 4: rounded mean QC of input FSC products is 2
        #bit 5: rounded mean QC of input FSC products is 3
        #bit 6: rounded mean QC of input FSC products is undefined
        source_list += [
            {
                'sources': [
                    {
                        'filepath': sp_qcmean_complete_dst_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    },
                    {
                        'filepath': water_layer_complete_src_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    }
                ], \
                'operation': {
                    0:'(np.floor(A0)==0)*((A1==0)+(A1==254))',
                    1:'(np.floor(A0)==1)*((A1==0)+(A1==254))',
                    2:'(np.floor(A0)==2)*((A1==0)+(A1==254))',
                    3:'(np.floor(A0)==3)*(A0<=3)*((A1==0)+(A1==254))'
                }
            }
        ]

        sp_qcflags_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QCFLAGS"]["dst_suffix_name"]}'
        )
        raster_gdal_info = gdal.Info(sp_scd_complete_dst_path, format='json')

        bit_bandmath(
            sp_qcflags_complete_dst_path,
            raster_gdal_info,
            [source_list],
            compress=False,
            add_overviews=False,
            use_default_cosims_config=False,
            raster_data_type=gdal.GDT_Byte
        )

    def make_lis_sps2_qc_layer(self):
        '''
        TODO
        '''
        sp_mean_qc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.postprocessing_to_make_files["QCMEAN"]["dst_suffix_name"]}'
        )
        sp_scd_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["SCD"]["dst_suffix_name"]}'
        )
        sp_nobs_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["NOBS"]["dst_suffix_name"]}'
        )

        #QC layer on ground
        #0: highest quality,
        #1: lower quality,
        #2: decreasing quality,
        #3: lowest quality,
        #420: inland water,
        #65535: no data
        source_list = []
        source_list += [
            {
                'sources': [
                    {
                        'filepath': sp_scd_complete_dst_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    },
                    {
                        'filepath': sp_mean_qc_complete_dst_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    },
                    {
                        'filepath': sp_nobs_complete_dst_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    }], \
                'operation': '(np.minimum(3, (A0<60)*3 + (A0>=60)*((A2<40)*(np.floor(A1)+2) + (A2<80)*(A2>=40)*(np.floor(A1)+1) + (A2>=80)*np.floor(A1)))).astype(np.uint16)'
            }
        ]
        #values 420 from FSCOG snow product
        source_list += [
            {
                'sources': [
                    {
                        'filepath': sp_scd_complete_dst_path,
                        'bandnumber': 1,
                        'unpack_bits': False
                    }
                ], \
            'operation': 'B.astype(np.uint16)*(A0!=420)*(A0!=65535) + np.uint16(420)*(A0==420)*(A0!=65535) + np.uint16(65535)*(A0==65535)'
            }
        ]

        sp_qc_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_make_files["QC"]["dst_suffix_name"]}'
        )
        raster_gdal_info = gdal.Info(sp_scd_complete_dst_path, format='json')

        bit_bandmath(
            sp_qc_complete_dst_path,
            raster_gdal_info,
            [source_list],
            no_data_values_per_band=[np.uint16(65535)],
            compress=False,
            add_overviews=False,
            use_default_cosims_config=False,
            raster_data_type=gdal.GDT_UInt16
        )

    @staticmethod
    def get_raster_info(raster=None):
        '''
        TODO
        '''
        return (
            raster.RasterXSize,
            raster.RasterYSize,
            raster.GetRasterBand(1),
            raster.GetDriver(),
            raster.GetGeoTransform(),
            raster.GetProjection()
        )

    def make_lis_sps2_qcod_qcmd_layer(self):
        '''
        TODO
        '''
        print('START > make_lis_sps2_qcod_layer')

        sp_sco_dst_complete_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["SOD"]["dst_suffix_name"]}'
        )
        sp_scm_dst_complete_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["SMOD"]["dst_suffix_name"]}'
        )
        sp_multitemp_snow_mask_src_complete_path = os.path.join(
            self.workdir_path,
            f'{self.postprocessing_auxilliary_files["MULTITEMP_INPUT_SNOW_MASKS"]["src_path"]}',
            f'{self.postprocessing_auxilliary_files["MULTITEMP_INPUT_SNOW_MASKS"]["src_name"]}'
        )

        sco_raster = gdal.Open(sp_sco_dst_complete_path)
        sco_col, sco_row, sco_band, sco_driver, sco_geo_transform, sco_projection = \
        LisSpS2PostProcessing.get_raster_info(
            sco_raster
        )
        scm_raster = gdal.Open(sp_scm_dst_complete_path)
        scm_col, scm_row, scm_band, scm_driver, scm_geo_transform, scm_projection = \
        LisSpS2PostProcessing.get_raster_info(
            scm_raster
        )

        with rasterio.open(sp_multitemp_snow_mask_src_complete_path, 'r') as multitemp_raster:
            n = multitemp_raster.meta["count"]
            multitemp_input_snow_mask_array = multitemp_raster.read(range(1,n+1))

        sco_ndarray = np.array(sco_band.ReadAsArray())
        qcod_ndarray = np.ones(sco_ndarray.shape, dtype=np.uint16)*65535

        sco_date = np.array([sco_ndarray[i,j]
                             if sco_ndarray[i,j]<420
                             else 65535
                             for i,j in np.ndindex(sco_ndarray.shape)]).reshape(sco_ndarray.shape)

        scm_ndarray = np.array(scm_band.ReadAsArray())
        qcmd_ndarray = np.ones(scm_ndarray.shape, dtype=np.uint16)*65535

        scm_date = np.array([scm_ndarray[i,j]
                             if scm_ndarray[i,j]<420
                             else 65535
                             for i,j in np.ndindex(scm_ndarray.shape)]).reshape(scm_ndarray.shape)

        for i, date in enumerate(self.input_dates):
            date_index = self.output_dates.index(date)
            qcod_ndarray = np.min([qcod_ndarray,
                                (multitemp_input_snow_mask_array[i,:,:] != 0)*abs(sco_date-date_index) +\
                                65535*(multitemp_input_snow_mask_array[i,:,:] == 0)]
                                ,axis=0)
            qcmd_ndarray = np.min([qcmd_ndarray,
                                   (multitemp_input_snow_mask_array[i,:,:] != 0)*abs(scm_date-date_index) +\
                                   65535*(multitemp_input_snow_mask_array[i,:,:] == 0)]
                                   ,axis=0)

        qcod_ndarray[sco_date>=420] = 65535
        qcmd_ndarray[scm_date>=420] = 65535

        self.write_raster_from_ndarray(
            raster_name=f'{self.product_folder_name_final}_QCOD.tif',
            data_array=qcod_ndarray,
            nb_row=sco_row,
            nb_col=sco_col,
            nb_band=1,
            driver=sco_driver,
            geo_transform=sco_geo_transform,
            projection=sco_projection,
            raster_data_type=gdal.GDT_UInt16,
            no_data_value=65535
        )

        self.write_raster_from_ndarray(
            raster_name=f'{self.product_folder_name_final}_QCMD.tif',
            data_array=qcmd_ndarray,
            nb_row=scm_row,
            nb_col=scm_col,
            nb_band=1,
            driver=scm_driver,
            geo_transform=scm_geo_transform,
            projection=scm_projection,
            raster_data_type=gdal.GDT_UInt16,
            no_data_value=65535
        )

        print(np.histogram(qcmd_ndarray[qcmd_ndarray>65000], bins=20))

    def make_basic_post_processing(self, file_key: str):
        '''
        TODO
        '''
        lis_sps2_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_to_edit_files[file_key]['src_path'],
            self.postprocessing_to_edit_files[file_key]['src_name']
        )
        water_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_auxilliary_files['WATER']['src_path'],
            self.postprocessing_auxilliary_files['WATER']['src_name']
        )
        lis_sps2_scd_layer_complete_src_path = os.path.join(
            self.workdir_path,
            self.postprocessing_to_edit_files['SCD']['src_path'],
            self.postprocessing_to_edit_files['SCD']['src_name']
        )

        source_list = []

        source_list += [{
            'sources': [{
                'filepath': lis_sps2_layer_complete_src_path,
                'bandnumber': 1,
                'unpack_bits': False
            },
            {
                'filepath': water_layer_complete_src_path,
                'bandnumber': 1,
                'unpack_bits': False
            }], \
            'operation': '(A0.astype(np.uint16)*(A1!=1)*(A1!=2)*(A1!=253)*(A1!=255) + np.uint16(420)*((A1==1)+(A1==2)) + np.uint16(65535)*((A1==253)+(A1==255))).astype(np.uint16)'
        }]

        sps2_layer_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files[file_key]["dst_suffix_name"]}'
        )

        raster_gdal_info = gdal.Info(
            lis_sps2_scd_layer_complete_src_path,
            format='json'
        )
        print(f'basic post processing file {lis_sps2_layer_complete_src_path}')
        # print(f'raster_gdal_info = {raster_gdal_info}')

        bit_bandmath(
            sps2_layer_complete_dst_path,
            raster_gdal_info,
            [source_list],
            no_data_values_per_band=[np.uint16(65535)],
            compress=False,
            add_overviews=False,
            use_default_cosims_config=False,
            raster_data_type=gdal.GDT_UInt16
        )

    def mask_low_scd_areas(self, file_key: str, scd_threshold=60):
        '''
        TODO
        '''
        sps2_layer_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files[file_key]["dst_suffix_name"]}'
        )
        sps2_layer_temp_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'new_{self.product_folder_name_final}_{self.postprocessing_to_edit_files[file_key]["dst_suffix_name"]}'
        )
        sps2_layer_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files[file_key]["dst_suffix_name"]}'
        )
        sps2_scd_complete_dst_path = os.path.join(
            self.workdir_path,
            self.product_folder_name,
            f'{self.product_folder_name_final}_{self.postprocessing_to_edit_files["SCD"]["dst_suffix_name"]}'
        )

        source_list = []

        source_list += [{
            'sources': [{
                'filepath': sps2_layer_complete_dst_path,
                'bandnumber': 1,
                'unpack_bits': False
            },
            {
                'filepath': sps2_scd_complete_dst_path,
                'bandnumber': 1,
                'unpack_bits': False
            }], \
            'operation': f'(A1>={scd_threshold})*A0.astype(np.uint16) + (A1<{scd_threshold})*np.uint16(65535)'

        }]

        raster_gdal_info = gdal.Info(
            sps2_layer_complete_dst_path,
            format='json'
        )

        bit_bandmath(
            sps2_layer_temp_complete_dst_path,
            raster_gdal_info,
            [source_list],
            no_data_values_per_band=[np.uint16(65535)],
            compress=False,
            add_overviews=False,
            use_default_cosims_config=False,
            raster_data_type=gdal.GDT_UInt16
        )

        os.remove(sps2_layer_complete_dst_path)
        os.rename(sps2_layer_temp_complete_dst_path, sps2_layer_complete_dst_path)

    def retrieve_product_files(self):
        '''
        TODO
        '''
        pass

    def edit_product_files(self):
        '''
        Edit every LIS phenology output we must:
        - TODO list the products changed and the modifications.
        '''
        for file in self.postprocessing_to_edit_files:
            print(f'edit_product_files > {file}')
            self.make_basic_post_processing(file)

        for file in self.postprocessing_to_edit_files:
            if file not in ['SCD','NOBS']:
                print(f'edit_product_files > {file}')
                self.mask_low_scd_areas(file)

    def make_quality_files(self):
        '''
        TODO
        '''
        
        self.make_lis_sps2_qcmean_qcmedian_layer()
        self.make_lis_sps2_qcflags_layer()
        self.make_lis_sps2_qc_layer()
        self.make_lis_sps2_qcod_qcmd_layer()

    def make_metadata_and_xml_files(self):
        '''
        TODO
        '''
        pass

    def sps2_product_main_layers_creation(self):
        '''
        TODO
        '''
        FileUtil.make_dir(
            os.path.join(
                self.workdir_path,
                self.product_folder_name
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
            os.path.join(self.workdir_path, self.product_folder_name_final),'_SCD.tif'
        )
        # self.make_metadata_and_xml_files()

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(
        description='This script is used to process SP S2 from a set of FSCs on a tile on a hydrological year.'
    )
    parser.add_argument(
        "--workdir", type=str, required=True, help='output directory'
    )
    parser.add_argument(
        "--tile_id", type=str, default='', required=True, help='output directory'
    )
    parser.add_argument(
        "--start-date", dest="start_date", type=str, default='', required=True, help='output directory'
    )
    parser.add_argument(
        "--end_date", type=str, default='', required=True, help='output directory'
    )
    args = parser.parse_args()

    lis_fsc_pos_processing = LisSpS2PostProcessing(
        args.workdir, args.tile_id, args.start_date, args.end_date
    )
    lis_fsc_pos_processing.sps2_product_main_layers_creation()
