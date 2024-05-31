#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
try:
    from osgeo import gdal
except:
    import gdal

def get_unit8_colors_all_nan_transparent():
    '''
    Set transparent color to all the values not used in the layer.
    '''
    colors = gdal.ColorTable()
    for ii in range(255+1):
        colors.SetColorEntry(ii, tuple([0,0,0,0]))
    return colors

def add_cc_colortable(product_path:str) -> None:
    '''
    Add colortable to the Cloud Classification file.

    :param product_path: the absolute path to the CC file.

    :returns: Nothing.
    '''
    # Check the file exists.
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'

    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)

    # Preset the NAN values color.
    colors = get_unit8_colors_all_nan_transparent()
    # Set the four color for the four CC values.
    colors.SetColorEntry(0, tuple([0,0,0,0]))
    colors.SetColorEntry(1, tuple([254,230,206,255]))
    colors.SetColorEntry(2, tuple([253,174,107,255]))
    colors.SetColorEntry(3, tuple([230,85,13,255]))

    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds

def add_qc_colortable(product_path:str) -> None:
    '''
    Add colortable to the QC file.

    :param product_path: the absolute path to the QC file.

    :returns: Nothing.
    '''
    # Check the file exists.
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'

    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)

    # Preset the NAN values color.
    colors = get_unit8_colors_all_nan_transparent()
    # Set the four color for the four QC values.
    colors.SetColorEntry(0, tuple([93,164,0,255]))
    colors.SetColorEntry(1, tuple([189,189,91,255]))
    colors.SetColorEntry(2, tuple([255,194,87,255]))
    colors.SetColorEntry(3, tuple([255,70,37,255]))

    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds

def add_colortable_to_files(product_path:str, product_tag:str=None) -> None:
    '''
    Add colortable to files in CC product.

    :param product_path: the absolute path to the product folder.
    :param product_tag: the name of the product folder.

    :returns: Nothing.
    '''

    success = True

    # Check that the product to manage exists.
    assert os.path.exists(product_path), f'product path {product_path} does not exist'

    # If the product_tag has not been given as a parameter, retrieve it from the compelte path.
    if product_tag is None:
        product_tag = os.path.basename(product_path)

    # Check that the product is indeed a Cloud Classification one.
    if product_tag.split('_')[0] == 'CC':
        # If the path is that of the whole product folder, call reccursively 
        # add_colortable_to_files on each file to manage within the folder.
        if os.path.isdir(product_path):
            # Only the CC and QC layer need colortables.
            for el in ['CC', 'QC']:
                print(f'colortable {product_tag}_{el}.tif')
                add_colortable_to_files(os.path.join(product_path, f'{product_tag}_{el}.tif'))
        # Manage the files.
        elif product_tag.split('_')[-1] in ['CC.tif']:
            print('add colortable to CC')
            add_cc_colortable(product_path)
        elif product_tag.split('_')[-1] in ['QC.tif']:
            print('add colortable to QC')
            add_qc_colortable(product_path)
        # Manage the case of an unindentified layer.
        else:
            success = False

    if not success:
        print(f'{product_path}: unidentified product')
    return success


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "product_path",
        type=str,
        help="CM product path. The program identifies which product is concerned py ' + \
        'parsing its name."
    )
    args = parser.parse_args()

    add_colortable_to_files(args.product_path)
