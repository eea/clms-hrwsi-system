#!/usr/bin/python3

import os
import sys
import logging
import numpy as np
from osgeo import osr, gdal
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET
from subprocess import Popen as subprocess_Popen
from yaml import safe_load as yaml_load

gdal.UseExceptions()
osr.UseExceptions()


logger = logging.getLogger(__name__)


def processing_routine(args):
    RC_TRESHLIST = [-4.0, -3.5, -3.0, -2.5]

    CODE_SSC_WET = 110
    CODE_SSC_DRY = 115
    CODE_SSC_SNOWFREE = 120
    CODE_CLOUD = 205
    CODE_WATER = 210
    CODE_NONMONTAIN = 240
    CODE_MASKS = 250
    CODE_NODATA = 255

    CODE_WSM_WET = 110
    CODE_WSM_NOTWET = 125

    theta1 = 20
    theta2 = 45
    k = 0.5

    FSC_THRESHOLD = 60

    # treshold in db for noise
    VHDBNOISE = 42
    VVDBNOISE = 40

    # return status
    ret = 0

    # suppress to create .aux.xml files
    # os.environ['GDAL_PAM_ENABLED'] = 'NO'
    gdal.SetConfigOption('GDAL_NUM_THREADS', 'ALL_CPUS')
    # output driver
    drv = gdal.GetDriverByName('MEM')
    # copy is needed for Cloud Optimized Geotiff (COG), https://geoexamples.com/other/2019/02/08/cog-tutorial.html/
    drv2 = gdal.GetDriverByName('GTiff')
    optionCOG = ["COMPRESS=DEFLATE", "ZLEVEL=4", "PREDICTOR=1", "TILED=YES", "BLOCKXSIZE=1024", "BLOCKYSIZE=1024",
                 "COPY_SRC_OVERVIEWS=YES"]

    # Read reference for this tile
    f = os.path.join(args.auxiliaries_dir, args.ref)
    ds = gdal.Open(f, gdal.GA_ReadOnly)
    if ds is None:
        logger.error("gdal.Open() failed for file: " + f)
        raise SystemExit(21)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjectionRef())
    gt = ds.GetGeoTransform()
    refxmin, refxpix, _, refymax, _, refypix = gt
    refxsiz, refysiz = ds.RasterXSize, ds.RasterYSize
    refvhnd = ds.GetRasterBand(1).GetNoDataValue()
    refvvnd = ds.GetRasterBand(2).GetNoDataValue()

    VHref = ds.GetRasterBand(1).ReadAsArray()
    VVref = ds.GetRasterBand(2).ReadAsArray()

    # Convert to dB
    mask_ref = (VHref > 0) & (VVref > 0) & (VHref != refvhnd) & (VVref != refvvnd)
    VHrefdB = 10 * np.log10(VHref, where=mask_ref)
    VVrefdB = 10 * np.log10(VVref, where=mask_ref)

    # Read ifile
    f = os.path.join(args.input_dir, args.sig0)
    ds = gdal.Open(f, gdal.GA_ReadOnly)
    if ds is None:
        logger.error("gdal.Open() failed for file: " + f)
        raise SystemExit(21)
    s1xmin, s1xpix, _, s1ymax, _, s1ypix = ds.GetGeoTransform()
    s1xsiz, s1ysiz = ds.RasterXSize, ds.RasterYSize
    s1vhnd = ds.GetRasterBand(1).GetNoDataValue()
    s1vvnd = ds.GetRasterBand(2).GetNoDataValue()
    # we need nodata value with zero, bc we do multilooking (mean)
    assert s1vhnd == 0
    assert s1vvnd == 0
    # Convert to dB
    S1assVH = ds.GetRasterBand(1).ReadAsArray()
    S1assVV = ds.GetRasterBand(2).ReadAsArray()

    # multilook (reshape) 6x6
    shap = [S1assVH.shape[0]//6, 6, S1assVH.shape[1]//6, 6]
    min1 = S1assVH.reshape(shap).min(-1).min(1)
    min2 = S1assVV.reshape(shap).min(-1).min(1)
    mask = (min1 > 0) & (min2 > 0)
    VH = S1assVH.reshape(shap).mean(-1).mean(1) * mask
    VV = S1assVV.reshape(shap).mean(-1).mean(1) * mask
    del S1assVH
    del S1assVV

    assert VH.shape == VHref.shape
    assert VV.shape == VVref.shape

    vhnoise = 10 ** (-VHDBNOISE / 10)
    vvnoise = 10 ** (-VVDBNOISE / 10)

    mask_s1 = (VH > vhnoise) & (VV > vvnoise) & (VH != s1vhnd) & (VV != s1vvnd)
    VHdB = 10 * np.log10(VH, where=mask_s1)
    VVdB = 10 * np.log10(VV, where=mask_s1)

    # Compute RVV and RVH
    RVH = VHdB - VHrefdB
    RVV = VVdB - VVrefdB

    # Initialise weighting
    f = os.path.join(args.auxiliaries_dir, args.incangle)
    ds = gdal.Open(f, gdal.GA_ReadOnly)
    if ds is None:
        logger.error("gdal.Open() failed for file: " + f)
        raise SystemExit(21)
    iaxmin, iaxpix, _, iaymax, _, iaypix = ds.GetGeoTransform()
    iaxsiz, iaysiz = ds.RasterXSize, ds.RasterYSize
    iand = ds.GetRasterBand(1).GetNoDataValue()
    IA = ds.GetRasterBand(1).ReadAsArray()
    mask_ia = (IA > -180) & (IA < 180) & (IA != iand)
    mnodata = np.logical_not(mask_ref & mask_s1 & mask_ia)
    if mnodata.sum() == mnodata.shape[0] * mnodata.shape[1]:
        # no data, tiles will be empty
        ret |= 0xD0

    # Compute weighting
    W = np.ones(IA.shape, dtype=np.float32)
    m = (IA >= theta1) & (IA <= theta2) & (IA != iand)
    W[m] = k * (1 + (theta2 - IA[m]) / (theta2 - theta1))
    m = IA > theta2
    W[m] = k

    # Compute Rc
    Rc = W * RVH + (1 - W) * RVV

    wsm = np.empty(VH.shape, dtype=np.uint8)
    wsm[:] = CODE_NODATA
    qcwsm = np.empty(VH.shape, dtype=np.uint8)
    qcwsm[:] = CODE_NODATA

    m = Rc >= RC_TRESHLIST[3]
    wsm[m] = CODE_WSM_NOTWET
    qcwsm[m] = CODE_MASKS

    m = ((Rc >= RC_TRESHLIST[2]) & (Rc < RC_TRESHLIST[3]))
    wsm[m] = CODE_WSM_WET
    qcwsm[m] = 3
    m = ((Rc >= RC_TRESHLIST[1]) & (Rc < RC_TRESHLIST[2]))
    wsm[m] = CODE_WSM_WET
    qcwsm[m] = 2
    m = ((Rc >= RC_TRESHLIST[0]) & (Rc < RC_TRESHLIST[1]))
    wsm[m] = CODE_WSM_WET
    qcwsm[m] = 1
    m = (Rc < RC_TRESHLIST[0])
    wsm[m] = CODE_WSM_WET
    qcwsm[m] = 0

    masks = np.zeros((refysiz, refxsiz), dtype=np.uint8)
    f = os.path.join(args.auxiliaries_dir, args.mask)
    ds = gdal.Open(f, gdal.GA_ReadOnly)
    if ds is None:
        logger.error("gdal.Open() failed for file: " + f)
        raise SystemExit(21)
    bmask = ds.GetRasterBand(1).ReadAsArray()
    m = (bmask != 0)
    masks[m] = bmask[m]
    f = os.path.join(args.auxiliaries_dir, args.layshad)
    ds = gdal.Open(f, gdal.GA_ReadOnly)
    if ds is None:
        logger.error("gdal.Open() failed for file: " + f)
        raise SystemExit(21)
    bmask = ds.GetRasterBand(1).ReadAsArray()
    m = (bmask != 0)
    masks[m] = bmask[m]


    ### generate WDS Product ###

    ssc = np.array(wsm)
    qcssc = np.array(qcwsm)
    ssc_valid = np.zeros((refysiz, refxsiz), dtype=np.uint8)
    ssc[:] = CODE_NODATA
    qcssc[:] = CODE_NODATA

    for fsc_path in args.fsc_paths:
        f = os.path.join(args.input_dir, fsc_path)
        ds = gdal.Open(f, gdal.GA_ReadOnly)
        if ds is None:
            logger.error("gdal.Open() failed for file: " + f)
            raise SystemExit(21)
        fsc = ds.GetRasterBand(1).ReadAsArray()

        scale_y, scale_x = fsc.shape[0] // ssc.shape[0], fsc.shape[1] // ssc.shape[1]
        observed_th = (scale_y * scale_x) // 2
        for y in range(0, ssc.shape[0]):
            fsc_y = y * scale_y
            for x in range(0, ssc.shape[1]):
                fsc_x = x * scale_x
                d = fsc[fsc_y:fsc_y + scale_y, fsc_x:fsc_x + scale_x]
                observed = ((d >= 0) & (d <= 100))
                observed_count = np.count_nonzero(observed)
                cloud = (d == CODE_CLOUD)
                cloud_count = np.count_nonzero(cloud)
                cloud_th = scale_y * scale_x - observed_count - cloud_count
                water = (d == CODE_WATER)
                water_count = np.count_nonzero(water)
                water_th = scale_y * scale_x - observed_count - water_count
                if observed_count > observed_th:
                    ssc_valid[y, x] = 1
                    # observed
                    if d[observed].mean() >= FSC_THRESHOLD:
                        # snow
                        if wsm[y, x] == CODE_WSM_WET:
                            # wet snow
                            ssc[y, x] = CODE_SSC_WET
                            qcssc[y, x] = qcwsm[y, x]
                        elif wsm[y, x] == CODE_WSM_NOTWET:
                            ssc[y, x] = CODE_SSC_DRY
                            qcssc[y, x] = CODE_MASKS
                    else:
                        # no snow
                        ssc[y, x] = CODE_SSC_SNOWFREE
                        qcssc[y, x] = CODE_MASKS
                elif ssc_valid[y, x] != 1 and cloud_count > cloud_th:
                    ssc_valid[y, x] = 2
                    # cloud
                    ssc[y, x] = CODE_CLOUD
                    qcssc[y, x] = CODE_MASKS
                elif ssc_valid[y, x] != 1 and water_count > water_th:
                    ssc_valid[y, x] = 2
                    # water
                    ssc[y, x] = CODE_WATER
                    qcssc[y, x] = CODE_MASKS

    m = (ssc_valid == 1) & (masks != 0)
    ssc[m] = masks[m]
    qcssc[m] = CODE_MASKS
    ssc[mnodata] = CODE_NODATA
    qcssc[mnodata] = CODE_NODATA

    if (ssc != CODE_NODATA).sum() == 0:
        # wds is empty
        ret |= 0xD0
    else:
        ssc_file = os.path.join(args.output_dir, args.ssc)
        ds = drv.Create(ssc_file, refxsiz, refysiz, 1, gdal.GDT_Byte)
        if ds is None:
            logger.error("drv.Create() failed in MEM: " + ssc_file)
            raise SystemExit(22)
        ds.SetGeoTransform(gt)
        ds.SetProjection(srs.ExportToWkt())
        band = ds.GetRasterBand(1)
        band.WriteArray(ssc)
        band.SetNoDataValue(CODE_NODATA)
        if args.ssc_colortable:
            f = os.path.join(args.auxiliaries_dir, args.ssc_colortable)
            ct = readColorTable(f)
            band.SetRasterColorTable(ct)
            band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)
        gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
        gdal.SetConfigOption('GDAL_TIFF_OVR_BLOCKSIZE', '1024')
        ds.BuildOverviews("NEAREST", [2, 4, 8, 16, 32])
        ds2 = drv2.CreateCopy(ssc_file, ds, options=optionCOG)
        if ds2 is None:
            logger.error("drv2.CreateCopy() failed for file: " + ssc_file)
            raise SystemExit(23)
        thumbnail = os.path.join(args.output_dir, "thumbnail.png")
        ds3 = gdal.Translate(thumbnail, ds, format="PNG", width=1000, height=1000, resampleAlg="nearest")
        if ds3 is None:
            logger.error("gdal.Translate() failed for file: " + thumbnail)
            raise SystemExit(24)
        band = None

        qcssc_file = os.path.join(args.output_dir, args.qcssc)
        ds = drv.Create(qcssc_file, refxsiz, refysiz, 1, gdal.GDT_Byte)
        if ds is None:
            logger.error("drv.Create() failed in MEM: " + qcssc_file)
            raise SystemExit(22)
        ds.SetGeoTransform(gt)
        ds.SetProjection(srs.ExportToWkt())
        band = ds.GetRasterBand(1)
        band.WriteArray(qcssc)
        band.SetNoDataValue(CODE_NODATA)
        if args.qcssc_colortable:
            f = os.path.join(args.auxiliaries_dir, args.qcssc_colortable)
            ct = readColorTable(f)
            band.SetRasterColorTable(ct)
            band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)
        gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
        gdal.SetConfigOption('GDAL_TIFF_OVR_BLOCKSIZE', '1024')
        ds.BuildOverviews("NEAREST", [2, 4, 8, 16, 32])
        ds2 = drv2.CreateCopy(qcssc_file, ds, options=optionCOG)
        if ds2 is None:
            logger.error("drv2.CreateCopy() failed for file: " + qcssc_file)
            raise SystemExit(23)
        band = None

    return ret


def readColorTable(color_file):
    color_table = gdal.ColorTable()
    with open(color_file, "r") as fp:
        for line in fp:
            line = line.strip()
            entry = line.split(",")
            if not line.startswith('#') and len(entry) >= 4:
                if len(entry) > 4:
                    alpha = int(entry[4])
                else:
                    alpha = 0
                color_table.SetColorEntry(int(entry[0]), (int(entry[1]), int(entry[2]), int(entry[3]), alpha))
    return color_table


def read_parameterfile(args):
    with open(args.parameterfile, "r") as fd:
        params = yaml_load(fd)
    for k, v in params.items():
        if getattr(args, k, None) is None:
            logger.debug(f'read_parameterfile setattr: "{k}"="{v}"')
            setattr(args, k, v)
    return args


if __name__ == '__main__':
    import argparse

    argparser = argparse.ArgumentParser(description="HR-WSI WDS processing")
    argparser.add_argument('parameterfile', help="options read from parameterfile")
    input_arg = argparser.add_argument_group('Inputs')
    input_arg.add_argument('--sig0', help="Sentinel-1 radarbrightness map with 10m")
    input_arg.add_argument('--fsc_paths', nargs='+', help="FSC files")
    input_arg.add_argument('--tileId', help="tile Id")
    auxis_arg = argparser.add_argument_group('Auxiliaries')
    auxis_arg.add_argument('--ref', help="reference S1 file")
    auxis_arg.add_argument('--incangle', help="incident angle file")
    auxis_arg.add_argument('--layshad', help="layover/shadow mask file")
    auxis_arg.add_argument('--mask', help="Forst/Water/Imperviousness mask file")
    auxis_arg.add_argument('--ssc_colortable', help="colortable wet/dry snow file")
    auxis_arg.add_argument('--qcssc_colortable', help="colortable wet/dry snow quality file")
    outpt_arg = argparser.add_argument_group('Outputs')
    outpt_arg.add_argument('--ssc', help="wet/dry snow file")
    outpt_arg.add_argument('--qcssc', help="wet/dry snow quality file")
    group_dir = argparser.add_argument_group('Directories')
    group_dir.add_argument("--input_dir")
    group_dir.add_argument("--output_dir")
    group_dir.add_argument("--auxiliaries_dir")
    group_dir.add_argument("--intermediate_dir")
    group_dir.add_argument("--logs_dir")

    args = argparser.parse_args()

    # setup parameter
    try:
        # change to proccessing directory
        os.chdir(os.path.dirname(sys.argv[0]) or ".")

        if args.parameterfile:
            args = read_parameterfile(args)
        else:
            logger.error("Parameter file not given")
            exit(101)
        # set default directories after reading parameterfile
        if args.input_dir is None:
            args.input_dir = "."
        if args.output_dir is None:
            args.output_dir = "."
        if args.auxiliaries_dir is None:
            args.auxiliaries_dir = "."
        if args.intermediate_dir is None:
            args.intermediate_dir = "."
        if args.logs_dir is None:
            args.logs_dir = "."
    except Exception as e:
        logger.error("Parameter setup failed")
        logger.error(e)
        exit(101)


    # configure logging
    logger.setLevel(logging.DEBUG)
    lfmt = logging.Formatter(fmt='[%(levelname)s][%(filename)s][%(asctime)s] > %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
    hndl = logging.FileHandler(os.path.join(args.logs_dir, "wds_processing_routine_stdout.log"), mode='a')
    hndl.setLevel(logging.DEBUG)
    hndl.setFormatter(lfmt)
    logger.addHandler(hndl)
    hndl = logging.FileHandler(os.path.join(args.logs_dir, "wds_processing_routine_stderr.log"), mode='a')
    hndl.setLevel(logging.WARNING)
    hndl.setFormatter(lfmt)
    logger.addHandler(hndl)

    ret = 0
    try:

        # check parameters
        for i in ["sig0", "fsc_paths", "ref", "incangle", "layshad", "mask", "ssc", "qcssc"]:
            if getattr(args, i, None) is None:
                logger.error(f"Parameter {i} not given")
                exit(102)

        # call product generation
        ret = processing_routine(args)

    except Exception as e:
        logger.error(e)
        ret=113

    # exit with success
    exit(ret)
