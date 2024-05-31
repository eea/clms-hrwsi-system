#!/bin/python

# READ GFSCs
# FILTER OUT NON PRESENT DAY
# COUNT NCOS
# COUNT NWOS
# STORE GFSC1, NCOS, NWOS IN INPUT

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, argparse, sys
from datetime import datetime
import numpy as np
from osgeo import gdal

def log(*message):
        message = map(str,message)
        message = ''.join(message)
        print(message)
        f = open(logPath,'a')
        f.write(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
        f.write(': ')
        f.write(message)
        f.write('\n')
        f.close()

def readRaster(fname):
    log("Reading ",fname)
    try:
        gtif = gdal.Open(fname)
        data = gtif.GetRasterBand(1)
        data_shape = (data.YSize,data.XSize)
        data = np.array(data.ReadAsArray())
        geoTransform = gtif.GetGeoTransform()
        projectionRef = gtif.GetProjectionRef()
        return (data,geoTransform,projectionRef)
    except:
        log("Problem in reading ", fname)
        return None

def writeRaster(fname,rasterData, geoTransform, projectionRef, colorMap = None):
    log("Writing %s" % fname)
    if rasterData.dtype == np.uint8:
        dtype = gdal.GDT_Byte
        noData = 255
    if rasterData.dtype == np.int16:
        dtype = gdal.GDT_Int16
        noData = 32767
    if rasterData.dtype == np.uint16:
        dtype = gdal.GDT_UInt16
        noData = 65535
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

baseDir = os.path.split(os.path.realpath(os.sys.argv[0]))[0]
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-g','--gfsc-dir',required=True,help='Preprocessing input directory (GFSC)')
parser.add_argument('-i','--input-dir',required=True,help='LIS input directory (FSC)')
parser.add_argument('-o','--output-dir',required=True,help='LIS/final output directory (SPS1S2)')

parser.add_argument('-s','--start-date',required=True,help='First day of the period (%%Y%%m%%d)')
parser.add_argument('-e','--end-date',required=True,help='Last day of the period (%%Y%%m%%d)')

parser.add_argument('-t','--tmp-dir',help='Temporary storage directory')
sysargv = vars(parser.parse_args())

os.makedirs(sysargv['output_dir'],exist_ok=True)
logPath = os.path.join(sysargv['output_dir'], 'preprocessing.log')
gfscDir = sysargv['gfsc_dir']
fscDir = sysargv['input_dir']
spDir = sysargv['output_dir']

log("GFSC Dir: %s" % gfscDir)
log("LIS input Dir: %s" % fscDir)
log("LIS output Dir: %s" % spDir)

startDate = datetime.strptime(sysargv['start_date'] + "T000000","%Y%m%dT%H%M%S")
endDate = datetime.strptime(sysargv['end_date'] + "T235959","%Y%m%dT%H%M%S")

log("Date interval: %s - %s" % (startDate.strftime("%d.%m.%Y"),endDate.strftime("%d.%m.%Y")))

include_nobs_in_margin = False
log("Observations outside date interval (in margin) are %sincluded in NCSO and NWSO." % ("" if include_nobs_in_margin else "not "))

CLOUD = 205
WATER = 210
WATER16 = 420
NODATA = 255
NODATA16 = 65535
SENSORBIT = 7

# if any filename is incorrect, script will stop. 

gfscList = [productname for productname in os.listdir(gfscDir) if 
           len(productname.split('_')) == 6 and 
           productname.split('_')[0] == "GFSC"
           ]
gfscList.sort()

fscList = [productname
                .replace('GFSC','FSC')
                .replace('-' + productname.split('_')[1].split('-')[1],"T000000") # manipulate timestamp
                .replace(productname.split('_')[2],"S2") # manipulate mission
                .replace(productname.split('_')[5],"1") # manipulate mode/prod_ts
           for productname in gfscList]
        # GFSC_20200904-007_S1-S2_T32TQT_V200_0000000000 becomes FSC_20200904T000000_S2_T32TQT_V200_1

ncsoPath = os.path.join(spDir, "NCSO.tif")
nwsoPath = os.path.join(spDir, "NWSO.tif")

log("%s GFSC to be converted into input for LIS" % len(gfscList))

if len(gfscList) == 0:
    sys.exit(0)

log("Reading a product to initialize additional layers")
gf = readRaster(os.path.join(gfscDir,gfscList[0],gfscList[0] + '_GF.tif'))[0]
ncso = np.zeros(shape=gf.shape,dtype=np.uint16)
nwso = np.zeros(shape=gf.shape,dtype=np.uint16)
wm = gf == WATER   

for i, fscTitle in enumerate(fscList):
    productdate = datetime.strptime(fscTitle.split('_')[1],"%Y%m%dT%H%M%S")
    gfscTitle = gfscList[i]
    gfscPath = os.path.join(gfscDir,gfscTitle)
    fscPath = os.path.join(fscDir,fscTitle)

    fsc, geoTransform, projectionRef = readRaster(os.path.join(gfscPath,gfscTitle + '_GF.tif'))
    qc = readRaster(os.path.join(gfscPath,gfscTitle + '_QC.tif'))[0]
    qf = readRaster(os.path.join(gfscPath,gfscTitle + '_QCFLAGS.tif'))[0]
    at = readRaster(os.path.join(gfscPath,gfscTitle + '_AT.tif'))[0]

    productdateTimestampStart = productdate.timestamp()
    productdateTimestampEnd = productdateTimestampStart + 24*60*60 - 1
    productdateMask = (at >= productdateTimestampStart) * (at <= productdateTimestampEnd)

    if np.sum(productdateMask) == 0:
        log("No pixels for the product day in the product. Skipped. %s " % gfscTitle)
        continue

    # filter out old pixels # do not change water pixels
    np.place(fsc,~wm * ~productdateMask,NODATA)
    np.place(qc,~wm * ~productdateMask,NODATA)

    # find ncso and nwso
    s1pixels = np.bitwise_and(np.right_shift(qf,SENSORBIT),1).astype(np.bool_)
    validpixels = (fsc >= 0) * (fsc <= 100)
    cso = validpixels & ~s1pixels
    wso = validpixels & s1pixels
    # print("%s cso %s wso %s day" % (np.sum(cso),np.sum(wso),np.sum(productdateMask)))
    if include_nobs_in_margin or (productdate <= endDate and productdate >= startDate):
        ncso += cso.astype(ncso.dtype)
        nwso += wso.astype(nwso.dtype)

    # filter s1 pixels from qc, qc in lis should only use s2 based ones.
    np.place(qc,s1pixels,NODATA)

    os.makedirs(fscPath,exist_ok=True)
    writeRaster(os.path.join(fscPath,fscTitle + '_FSCOG.tif'), fsc, geoTransform, projectionRef)
    writeRaster(os.path.join(fscPath,fscTitle + '_QCOG.tif'), qc, geoTransform, projectionRef)

# fill water in nobs and write
print(np.sum(ncso),np.sum(nwso))
np.place(ncso,wm,WATER16)
np.place(nwso,wm,WATER16)
os.makedirs(spDir,exist_ok=True)
writeRaster(ncsoPath, ncso, geoTransform, projectionRef)
writeRaster(nwsoPath, nwso, geoTransform, projectionRef)

