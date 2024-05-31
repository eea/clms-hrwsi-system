#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
try:
    from osgeo import gdal
except:
    import gdal

def get_unit8_colors_all_nan_transparent():
    '''
    TODO
    '''
    colors = gdal.ColorTable()
    for ii in range(255+1):
        colors.SetColorEntry(ii, tuple([0,0,0,0]))
    return colors
    
def add_linspace_colors(colors, values, color_start, color_end):
    '''
    TODO
    '''
    nadd = len(values)
    if len(color_start) == 3:
        color_start = color_start + [255]
    if len(color_end) == 3:
        color_end = color_end + [255]
    assert all([0<=ii<=255 for ii in color_start])
    assert all([0<=ii<=255 for ii in color_end])
    for i0, value in enumerate(values):
        coeff = i0*1./(nadd-1.)
        colors.SetColorEntry(value, tuple([int(round(color_start[ii]+coeff*(color_end[ii]-color_start[ii]))) for ii in range(4)]))
    return colors

def add_fsc_colortable(product_path):
    '''
    TODO
    '''
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit8_colors_all_nan_transparent()
    colors.SetColorEntry(0, tuple([0,0,0,0]))
    colors = add_linspace_colors(colors, list(range(1,100+1)), [8,51,112], [255,255,255])
    colors.SetColorEntry(205, tuple([123,123,123,255]))
    colors.SetColorEntry(210, tuple([119,161,203,255]))
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds

def add_qc_colortable(product_path, with_cloud=True):
    '''
    TODO
    '''
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit8_colors_all_nan_transparent()
    colors.SetColorEntry(0, tuple([93,164,0,255]))
    colors.SetColorEntry(1, tuple([189,189,91,255]))
    colors.SetColorEntry(2, tuple([255,194,87,255]))
    colors.SetColorEntry(3, tuple([255,70,37,255]))
    if with_cloud:
        colors.SetColorEntry(205, tuple([123,123,123,255]))
    colors.SetColorEntry(210, tuple([0,0,255,255]))
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds
    

    

def add_colortable_to_files(product_path, product_tag=None):
    '''
    TODO
    '''
    
    success = True
    
    assert os.path.exists(product_path), f'product path {product_path} does not exist'
    if product_tag is None:
        product_tag = os.path.basename(product_path)
    
    if product_tag.split('_')[0] == 'FSC':
        if os.path.isdir(product_path):
            for el in ['FSCTOC', 'FSCOG', 'QCTOC', 'QCOG', 'NDSI']:
                add_colortable_to_files(os.path.join(product_path, f'{product_tag}_{el}.tif'))
        elif product_tag.split('_')[-1] in ['FSCTOC.tif', 'FSCOG.tif', 'NDSI.tif']:
            add_fsc_colortable(product_path)
        elif product_tag.split('_')[-1] in ['QCTOC.tif', 'QCOG.tif']:
            add_qc_colortable(product_path, with_cloud=True)
        else:
            success = False
        
    if not success:
        print(f'{product_path}: unidentified product')
    return success
    

if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("product_path", type=str, help="FSC, RLIE or PSA product path. The program identifies which product is concerned py parsing its name.")
    args = parser.parse_args()
    
    add_colortable_to_files(args.product_path)
    

    
