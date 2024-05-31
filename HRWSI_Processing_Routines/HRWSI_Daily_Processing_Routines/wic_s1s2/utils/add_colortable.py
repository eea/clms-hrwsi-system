#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from osgeo import gdal

def get_unit8_colors_all_nan_transparent():
    '''
    TODO
    '''
    colors = gdal.ColorTable()
    for ii in range(255+1):
        colors.SetColorEntry(ii, tuple([0,0,0,0]))
    return colors

def add_wic_colortable(product_path):
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit8_colors_all_nan_transparent()
    colors.SetColorEntry(1, tuple([0,0,255,255])) #open water
    colors.SetColorEntry(100, tuple([0,255,255,255])) #ice
    colors.SetColorEntry(200, tuple([40,40,40,255])) #radar shadow
    colors.SetColorEntry(205, tuple([123,123,123,255])) #clouds
    colors.SetColorEntry(254, tuple([255,0,0,255])) # other features
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds

def add_qc_colortable(product_path, with_cloud=True):
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
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds
