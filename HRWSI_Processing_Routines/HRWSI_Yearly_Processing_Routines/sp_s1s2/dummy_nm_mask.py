#!/bin/python
import os, argparse, sys
import numpy as np
from osgeo import gdal


# Creates dummy NM mask for flat tiles (from same tile aux file template) so that SP S1+S2 can be produced.
# NM are only available in mountain tiles.
# Example python dummy_nm_mask.py -i T34UDV_60m_MASK_FOREST_URBAN_WATER_v20240404.tif -i T34UDV_60m_MASK_NON_MOUNTAIN_AREA_V20211119.tif

baseDir = os.path.split(os.path.realpath(os.sys.argv[0]))[0]
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-i','--template-file',help='Preprocessing input directory (GFSC)')
parser.add_argument('-o','--output-file',help='LIS input directory (FSC)')

sysargv = vars(parser.parse_args())
inputfile = sysargv['template_file']
outputfile = sysargv['output_file']

def readRasters(fname):
    try:
        gtif = gdal.Open(fname)
        data = [np.array(gtif.GetRasterBand(i+1).ReadAsArray()) for i in range(gtif.RasterCount)]
        data_shape = data[0].shape
        data = data[0] if len(data) == 1 else data
        geoTransform = gtif.GetGeoTransform()
        projectionRef = gtif.GetProjectionRef()
        return (data,geoTransform,projectionRef)
    except:
        return None

def writeRaster(fname,rasterData, geoTransform, projectionRef, colorMap = None):
    if rasterData.dtype == np.float32:
        dtype = gdal.GDT_Float32
        noData = np.nan
    if rasterData.dtype == np.uint8:
        dtype = gdal.GDT_Byte
        noData = 255
    if rasterData.dtype == np.int16:
        dtype = gdal.GDT_Int16
        noData = 32767
    if rasterData.dtype == np.uint32:
        dtype = gdal.GDT_UInt32
        noData = 4294967295
    if rasterData.dtype == np.int32:
        dtype = gdal.GDT_Int32
        noData = 2147483647
    dst_ds = gdal.GetDriverByName('MEM').Create('', rasterData.shape[0], rasterData.shape[1], 1, dtype)
    dst_ds.SetGeoTransform(geoTransform)
    dst_ds.SetProjection(projectionRef)
    dst_ds.GetRasterBand(1).WriteArray(rasterData)
    dst_ds.GetRasterBand(1).SetNoDataValue(noData)
    band = dst_ds.GetRasterBand(1)
    if colorMap is not None:
        colors = gdal.ColorTable()
        for value in colorMap:
            colors.SetColorEntry(value, colorMap[value])
        band.SetRasterColorTable(colors)
        band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)
    gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
    gdal.SetConfigOption('GDAL_TIFF_OVR_BLOCKSIZE', '1024')
    dst_ds.BuildOverviews("NEAREST", [2,4,8,16,32])
    band = None
    options = ['COMPRESS=DEFLATE', 'PREDICTOR=1', 'ZLEVEL=4', 'TILED=YES', 'BLOCKXSIZE=1024', 'BLOCKYSIZE=1024', "COPY_SRC_OVERVIEWS=YES"]
    dst_ds2 = gdal.GetDriverByName('GTiff').CreateCopy(fname, dst_ds, options=options)
    dst_ds = None
    dst_ds2 = None
    return True


data,geoTransform,projectionRef = readRasters(inputfile)
data[:] = 240
os.makedirs(os.path.split(outputfile)[0],exist_ok=True)
writeRaster(outputfile,data, geoTransform, projectionRef)

