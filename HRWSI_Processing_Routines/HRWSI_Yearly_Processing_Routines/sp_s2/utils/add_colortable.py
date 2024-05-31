#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
try:
    from osgeo import gdal
except:
    import gdal

def get_unit16_colors_all_nan_transparent():
    '''
    TODO
    '''
    colors = gdal.ColorTable()
    for ii in range(65535+1):
        colors.SetColorEntry(ii, tuple([0,0,0,0]))
    return colors

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

def add_sp_scd_colortable(product_path):
    '''
    TODO
    '''
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit16_colors_all_nan_transparent()
    colors.SetColorEntry(0, tuple([255,255,255,255]))
    colors = add_linspace_colors(colors, list(range(1,366+1)), [255,255,255], [255,75,170])
    colors.SetColorEntry(420, tuple([100,100,215,255]))
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds

def add_sp_sco_colortable(product_path):
    '''
    TODO
    '''
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit16_colors_all_nan_transparent()
    colors.SetColorEntry(0, tuple([255,255,255,255]))
    colors = add_linspace_colors(colors, list(range(1,366+1)), [255,255,255], [21,128,13])
    colors.SetColorEntry(420, tuple([100,100,215,255]))
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds

def add_sp_scm_colortable(product_path):
    '''
    TODO
    '''
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit16_colors_all_nan_transparent()
    colors.SetColorEntry(0, tuple([255,255,255,255]))
    colors = add_linspace_colors(colors, list(range(1,366+1)), [255,255,255], [126,49,129])
    colors.SetColorEntry(420, tuple([100,100,215,255]))
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds

def add_sp_nobs_colortable(product_path):
    '''
    TODO
    '''
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit16_colors_all_nan_transparent()
    colors.SetColorEntry(0, tuple([255,255,255,255]))
    colors = add_linspace_colors(colors, list(range(1,183+1)), [255,255,255], [211,77,15])
    colors.SetColorEntry(420, tuple([100,100,215,255]))
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds

def add_qc_colortable(product_path):
    '''
    TODO
    '''
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit16_colors_all_nan_transparent()
    colors.SetColorEntry(0, tuple([93,164,0,255]))
    colors.SetColorEntry(1, tuple([189,189,91,255]))
    colors.SetColorEntry(2, tuple([255,194,87,255]))
    colors.SetColorEntry(3, tuple([255,70,37,255]))
    colors.SetColorEntry(420, tuple([100,100,215,255]))
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
    
    if product_tag.split('_')[0] == 'SP':
        if os.path.isdir(product_path):
            for el in ['SCD', 'SCO', 'SCM', 'NOBS', 'QC']:
                add_colortable_to_files(os.path.join(product_path, f'{product_tag}_{el}.tif'))
        elif product_tag.split('_')[-1] in ['SCD.tif']:
            add_sp_scd_colortable(product_path)
        elif product_tag.split('_')[-1] in ['SCO.tif']:
            add_sp_sco_colortable(product_path)
        elif product_tag.split('_')[-1] in ['SCM.tif']:
            add_sp_scm_colortable(product_path)
        elif product_tag.split('_')[-1] in ['NOBS.tif']:
            add_sp_nobs_colortable(product_path)
        elif product_tag.split('_')[-1] in ['QC.tif']:
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
    

    
