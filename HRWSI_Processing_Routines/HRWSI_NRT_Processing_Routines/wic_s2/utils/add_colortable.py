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

def add_proba_colortable(product_path):
    '''
    TODO
    '''
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit8_colors_all_nan_transparent()
    colors.SetColorEntry(0, tuple([0,0,0,0]))
    colors = add_linspace_colors(colors, list(range(1,100+1)), [8,51,112], [255,255,255])
    colors.SetColorEntry(205, tuple([123,123,123,255])) #clouds
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds


def add_wic_colortable(product_path):
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit8_colors_all_nan_transparent()
    colors.SetColorEntry(1, tuple([0,0,255,255])) #open water
    colors.SetColorEntry(100, tuple([0,255,255,255])) #ice
    colors.SetColorEntry(205, tuple([123,123,123,255])) #clouds
    colors.SetColorEntry(254, tuple([255,0,0,255])) # other features
    band.SetRasterColorTable(colors)
    band.FlushCache()
    ds = None
    del ds

def add_labels_colortable(product_path):
    assert os.path.exists(product_path), f'product_path {product_path} does not exist'
    ds = gdal.Open(product_path, 1)
    band = ds.GetRasterBand(1)
    colors = get_unit8_colors_all_nan_transparent()
    colors.SetColorEntry(0, tuple([155,4,255,255])) #no data
    colors.SetColorEntry(1, tuple([155,4,255,255])) #background
    colors.SetColorEntry(2, tuple([123,123,123,255])) #low clouds
    colors.SetColorEntry(3, tuple([188,188,188,255])) #high clouds
    colors.SetColorEntry(4, tuple([0,0,0,255])) #clouds shadows
    colors.SetColorEntry(5, tuple([154,92,0,255])) #land
    colors.SetColorEntry(6, tuple([0,0,255,255])) #water
    colors.SetColorEntry(7, tuple([213,232,255,255])) #snow
    colors.SetColorEntry(8, tuple([247,255,0,255])) #mineral turbidity
    colors.SetColorEntry(9, tuple([203,210,0,255])) #organic turbidity
    colors.SetColorEntry(10, tuple([0,239,255,255])) #thin ice
    colors.SetColorEntry(11, tuple([0,179,255,255])) #thick ice
    colors.SetColorEntry(12, tuple([0,153,0,255])) #vegetation
    colors.SetColorEntry(13, tuple([245,155,0,255])) #salt sea
    colors.SetColorEntry(14, tuple([255,0,0,255])) #other
    colors.SetColorEntry(205, tuple([123,123,123,255])) #clouds
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

