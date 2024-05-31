import logging
import os
import os.path as op
import shutil

import numpy as np
from osgeo import gdal
import copy

from s2snow.lis_constant import FSCCLD, QCFLAGS, QCOG, QCTOC


def edit_lis_fsc_qc_layers(fsc_toc_file, maja_cloud_mask_file, geophysical_mask_file, output_folder, fsc_og_file=None,
                           water_mask_path=None, tcd_path=None, shaded_snow_path=None):
    output_expert_file = None
    raster_gdal_info = gdal.Info(fsc_toc_file, format='json')

    # cloud : there used to be a specific cloud processing but instead we are just copying the MAJA cloud mask
    output_cloud_file = op.join(output_folder, FSCCLD)
    copy_original(maja_cloud_mask_file, output_cloud_file)
    compress_geotiff_file(output_cloud_file, add_overviews=True, use_default_cosims_config=True)

    output_expert_file = op.join(output_folder, QCFLAGS)

    # expert flags
    if tcd_path is not None:
        if water_mask_path is not None:
            source_list = []
            # bit 0: MAJA sun too low for an accurate slope correction
            # bit 1: MAJA sun tangent
            source_list += [{'sources': [{'filepath': geophysical_mask_file, 'bandnumber': 1, 'unpack_bits': True}], \
                             'operation': {0: 'A0[:,:,6]', 1: 'A0[:,:,7]'}}]
            # bit 2: water mask
            source_list += [{'sources': [{'filepath': water_mask_path, 'bandnumber': 1, 'unpack_bits': False}], \
                             'operation': {2: 'A0==1'}}]
            # bit 3: tree cover density > 90%
            source_list += [{'sources': [{'filepath': tcd_path, 'bandnumber': 1, 'unpack_bits': False}], \
                             'operation': {3: 'np.logical_and(A0<101,A0>90)'}}]
            # bit 4: snow detected under thin clouds
            source_list += [{'sources': [{'filepath': maja_cloud_mask_file, 'bandnumber': 1, 'unpack_bits': False},
                                         {'filepath': fsc_toc_file, 'bandnumber': 1, 'unpack_bits': False}], \
                             'operation': {4: '(A0>0)*(A1>0)*(A1<101)'}}]
            # bit 5: tree cover density undefined or unavailable
            source_list += [{'sources': [{'filepath': tcd_path, 'bandnumber': 1, 'unpack_bits': False}], \
                             'operation': {5: 'A0>100'}}]
            if shaded_snow_path is not None:
                # bit 6: artificial 100 fsc due to shaded snow detection
                source_list += [{'sources': [{'filepath': shaded_snow_path, 'bandnumber': 1, 'unpack_bits': False}, ], \
                                 'operation': {6: 'A0==1'}}]
            bit_bandmath(output_expert_file, raster_gdal_info, [source_list], compress=True,
                         use_default_cosims_config=True)

            if fsc_og_file is not None:
                # QC layer on ground
                # [0: highest quality, 1: lower quality, 2: decreasing quality, 3: lowest quality, 205: cloud mask, 255: no data]
                source_list = []
                source_list += [{'sources': [{'filepath': output_expert_file, 'bandnumber': 1, 'unpack_bits': True},
                                             {'filepath': tcd_path, 'bandnumber': 1, 'unpack_bits': False}], \
                                 'operation': 'np.minimum(B*0+3,(4-np.maximum(B*0, (100.-30.*A0[:,:,1]-50.*A0[:,:,0]-25.*A0[:,:,4]-25.*A0[:,:,2]-80.*A1)/25.))).astype(np.uint8)'}]
                # values 205 and 255 from FSCOG snow product
                source_list += [{'sources': [{'filepath': fsc_og_file, 'bandnumber': 1, 'unpack_bits': False}], \
                                 'operation': 'B*(A0!=205)*(A0!=255) + 205*(A0==205) + 255*(A0==255)'}]
                output_qc_og_file = op.join(output_folder, QCOG)
                bit_bandmath(output_qc_og_file, raster_gdal_info, [source_list], no_data_values_per_band=[np.uint8(255)],
                             compress=True, use_default_cosims_config=True)
            else:
                logging.warning("FSCOG is not defined. QC Layer on ground file cannot be computed.")

            # QC layer top of canopy
            # [0: highest quality, 1: lower quality, 2: decreasing quality, 3: lowest quality, 205: cloud mask, 255: no data]
            source_list = []
            source_list += [{'sources': [{'filepath': output_expert_file, 'bandnumber': 1, 'unpack_bits': True}], \
                             'operation': 'np.minimum(B*0+3,(4-np.maximum(B*0, (100.-100.*A0[:,:,6]-30.*A0[:,:,1]-50.*A0[:,:,0]-25.*A0[:,:,4]-25.*A0[:,:,2])/25.))).astype(np.uint8)'}]
            # values 205 and 255 from FSCTOC snow product
            source_list += [{'sources': [{'filepath': fsc_toc_file, 'bandnumber': 1, 'unpack_bits': False}], \
                             'operation': 'B*(A0!=205)*(A0!=255) + 205*(A0==205) + 255*(A0==255)'}]
            output_qc_toc_file = op.join(output_folder, QCTOC)
            bit_bandmath(output_qc_toc_file, raster_gdal_info, [source_list], no_data_values_per_band=[np.uint8(255)],
                         compress=True, use_default_cosims_config=True)
        else:
            logging.warning("Water mask is not defined. QCFlags files cannot be computed.")
    else:
        logging.warning(
            "Tree cover density is not defined. QCFlags files cannot be computed.")

    return output_expert_file


def bit_bandmath(output_file, raster_info_dict, source_list_per_band, no_data_values_per_band=None, compress=True,
                 add_overviews=True, use_default_cosims_config=True):
    """Creates a copy of a monoband uint8 source model file and fills each bits independantly from different uint8 files.

    :param output_file: path to output TIF file
    :param raster_info_dict: dict containing some gdal.Info information on raster to create (['size'], ['geoTransform'] and ['coordinateSystem']['wkt'])
    :param source_list_per_band: list of source lists (1 per output file band)
    :param reinitialize_values: reinitialize values to 0, otherwise values from source_model_file are kept
    :param keep_no_data_from_source_file: reapply nodata values from source_model_file at the end of operations
    :return: returns nothing

    source list example (monoband): [{'filepath': cloud_mask_file, 'bandnumber': 1, 'bit_operations': {0: 'A[:,:,1]', 1: '1-(1-A[:,:,2])*(1-A[:,:,3])',  2: '(1-A[:,:,1])*(1-A[:,:,6])'}}]
    WARNING: bits unpacked in little endian (from smaller to greater)
    """

    nbands = len(source_list_per_band)

    # open source model file, copy it and load data
    ds_out = gdal.GetDriverByName('GTiff').Create(output_file, raster_info_dict['size'][0], raster_info_dict['size'][1],
                                                  nbands, gdal.GDT_Byte)
    is_gcps = 'gcps' in raster_info_dict
    if 'gcps' in raster_info_dict:
        assert 'geoTransform' not in raster_info_dict
        ds_out.SetGCPs([gdal.GCP(el['x'], el['y'], el['z'], el['pixel'], el['line']) for el in
                        raster_info_dict['gcps']['gcpList']], raster_info_dict['gcps']['coordinateSystem']['wkt'])
    else:
        ds_out.SetGeoTransform(tuple(raster_info_dict['geoTransform']))
    for band_no in range(nbands):
        outband = ds_out.GetRasterBand(band_no + 1)
        outband.DeleteNoDataValue()
        if no_data_values_per_band is not None:
            if no_data_values_per_band[band_no] is not None:
                outband.SetNoDataValue(float(no_data_values_per_band[band_no]))
        output_array = outband.ReadAsArray()
        output_array[:, :] = 0
        output_bits_unpacked = False
        for dico in source_list_per_band[band_no]:
            local_eval_dict = {'np': np, 'logical_array_list_operation': logical_array_list_operation}
            for i_src, src in enumerate(dico['sources']):
                local_name = 'A%d' % i_src
                # get all input arrays
                assert os.path.exists(src['filepath']), 'file %s missing' % src['filepath']
                ds_loc = gdal.Open(src['filepath'])
                if ds_loc is None:
                    raise IOError('gdal could not open file %s' % src['filepath'])
                local_eval_dict[local_name] = ds_loc.GetRasterBand(src['bandnumber']).ReadAsArray()
                if src['unpack_bits']:
                    local_eval_dict[local_name] = unpackbits2d(local_eval_dict[local_name])
                ds_loc = None

            # fill output_array
            is_bit_operation_on_output_array = isinstance(dico['operation'], dict)
            if is_bit_operation_on_output_array:
                if not output_bits_unpacked:
                    output_array = unpackbits2d(output_array)
                    output_bits_unpacked = True
                local_eval_dict['B'] = output_array
                for id_bit, operation in dico['operation'].items():
                    output_array[:, :, id_bit] = eval(operation, {}, local_eval_dict)
            else:
                if output_bits_unpacked:
                    output_array = packbits2d(output_array)
                    output_bits_unpacked = False
                local_eval_dict['B'] = output_array
                output_array = eval(dico['operation'], {}, local_eval_dict)

        if output_bits_unpacked:
            output_array = packbits2d(output_array)
        # write array
        outband.WriteArray(output_array)
        outband.FlushCache()

    if not is_gcps:
        ds_out.SetProjection(raster_info_dict['coordinateSystem']['wkt'])
    ds_out = None
    del ds_out
    if compress or add_overviews:
        compress_geotiff_file(output_file, add_overviews=add_overviews,
                              use_default_cosims_config=use_default_cosims_config)


def compress_geotiff_file(src_file, dest_file=None, tiled=True, compress='deflate', zlevel=4, predictor=1,
                          add_overviews=False, use_default_cosims_config=False):
    if dest_file is None:
        dest_file = src_file

    if add_overviews:
        # build external overviews base on src image
        tmp_img = gdal.Open(src_file, 0)  # 0 = read-only (external overview), 1 = read-write.
        gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
        if use_default_cosims_config:
            gdal.SetConfigOption('GDAL_TIFF_OVR_BLOCKSIZE', '1024')
        tmp_img.BuildOverviews("NEAREST", [2, 4, 8, 16, 32])
        del tmp_img

    compression_options = []
    if tiled:
        compression_options.append('tiled=yes')
        if use_default_cosims_config:
            compression_options.append('blockxsize=1024')
            compression_options.append('blockysize=1024')
    compression_options.append('compress=%s' % compress)
    if compress == 'deflate':
        compression_options.append('zlevel=%d' % zlevel)
    if compress in ['deflate', 'lzw', 'lzma']:
        compression_options.append('predictor=%d' % predictor)
    # any src_file overviews will be internal in dest_file
    compression_options.append('COPY_SRC_OVERVIEWS=YES')
    if os.path.abspath(src_file) == os.path.abspath(dest_file):
        prefix, sufix = '.'.join(dest_file.split('.')[0:-1]), dest_file.split('.')[-1]
        temp_name = prefix + '_temp.' + sufix
        
        gdal.Translate(temp_name, src_file, creationOptions=compression_options)
        shutil.move(temp_name, dest_file)
    else:
        
        gdal.Translate(dest_file, src_file, creationOptions=compression_options)
    if os.path.exists(src_file + '.ovr'):
        # remove temporary external overview
        os.unlink(src_file + '.ovr')


def logical_array_list_operation(list_in, operation):
    assert isinstance(list_in, list)
    assert len(list_in) > 0
    assert operation in ['or', 'and']
    ar_loc = copy.deepcopy(list_in[0])
    for ii in range(1, len(list_in)):
        if operation == 'or':
            ar_loc = np.logical_or(ar_loc, list_in[ii])
        elif operation == 'and':
            ar_loc = np.logical_and(ar_loc, list_in[ii])
    return ar_loc


def check_path(path, is_dir=False):
    assert os.path.exists(path), 'path %s does not exist' % path
    if is_dir:
        assert os.path.isdir(path), 'path %s is not a directory' % path
    return path


def copy_original(src, dst):
    src_realpath = original_path(src)
    if os.path.isdir(src_realpath):
        shutil.copytree(src_realpath, dst)
    else:
        shutil.copy(src_realpath, dst)


def original_path(file_in):
    if not os.path.islink(file_in):
        return file_in
    return original_path(os.readlink(file_in))


def unpackbits2d(ar):
    return np.unpackbits(np.expand_dims(ar, axis=2), axis=2, bitorder='little')


def packbits2d(ar):
    return np.squeeze(np.packbits(ar, axis=2, bitorder='little'), axis=2)
