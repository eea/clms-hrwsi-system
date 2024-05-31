#!/usr/bin/python3

import os
import sys
import logging

from osgeo import ogr, osr
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET
from subprocess import Popen as subprocess_Popen
from yaml import safe_load as yaml_load

from snap_template import *

ogr.UseExceptions()
osr.UseExceptions()


'''
https://forum.step.esa.int/t/sentinel-1-grd-preprocessing-graph/17810

FedericoF  Sep '19
Standard workflow for the preprocessing of Sentinel-1 GRDH data.

The GPF graph executes a Sentinel-1 GRDH preprocessing workflow that consists of seven processing steps, applying a series of standard corrections:

Apply Orbit File
Thermal Noise Removal
Border Noise Removal
Calibration
Speckle filtering (optional)
Range Doppler Terrain Correction
Conversion to dB
Sentinel-1 GRD products can be spatially coregistered to Sentinel-2 MSI data grids, in order to promote the use of satellite virtual constellations by means of data fusion techniques. Optionally a speckle filtering can be applied to the input image.


snap forum: lvevi: The noise removal should be done before calibration.

'''


logger = logging.getLogger(__name__)

UTC = timezone(timedelta(0))


def bb2poly(minX, minY, maxX, maxY, buf=0):
    # Lazy loading to not create dependencies chain in orchestrator services
    from osgeo import ogr

    # Create ring
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(minX-buf, minY-buf)
    ring.AddPoint(maxX+buf, minY-buf)
    ring.AddPoint(maxX+buf, maxY+buf)
    ring.AddPoint(minX-buf, maxY+buf)
    ring.AddPoint(minX-buf, minY-buf)
    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return poly

def generate_snap_graph(args):
    pixelsize = 10

    s1_product_list_sorted = sorted(args.s1_info, key=lambda p: p['startTime'])
    tileId = args.tileId

    epsg = int(tileId[:2]) + 32600
    missionTakeId = s1_product_list_sorted[0]['missionTakeId']
    s1_relativeOrbitNumber = s1_product_list_sorted[0]['relativeOrbitNumber']
    s1_startTime = s1_product_list_sorted[0]['startTime']
    s1_stopTime = s1_product_list_sorted[-1]['stopTime']
    platform = s1_product_list_sorted[0]['product_id'][:3]
    assembly_id = f"{platform}_{missionTakeId}_{tileId}"
    subst = {}
    subst['saveSelectedSourceBand'] = 'true'
    subst['saveLocalIncidenceAngle'] = 'false'
    subst['PIXELSIZE'] = pixelsize
    subst['epsg'] = epsg
    subst['assemblyId'] = assembly_id
    pread = []
    xml_graph = ET.fromstring(xml_graph_init)
    Inum = 0
    for s1 in s1_product_list_sorted:
        subst['readId'] = assembly_id + "_%d" % Inum
        subst['readFile'] = os.path.join(args.input_dir, s1["product_id"])
        subst['readFormat'] = 'SENTINEL-1'
        subst['rmBorderNoiseSourceProduct'] = 'Apply-Orbit-File'
        xml_graph.append(ET.fromstring(xml_graph_read % subst))
        if s1['startTime'].replace(tzinfo=UTC) < datetime.now(UTC) - timedelta(days=22):
            subst['orbitType'] = "Precise"
        else:
            subst['orbitType'] = "Restituted"
        xml_graph.append(ET.fromstring(xml_graph_orbit % subst))
        xml_graph.append(ET.fromstring(xml_graph_bordernoise % subst))
        xml_graph.append(ET.fromstring(xml_graph_thermalnoiseremoval % subst))
        xml_graph.append(ET.fromstring(xml_graph_calibration % subst))
        pread.append(subst['readId'])
        Inum += 1

    if len(pread) > 1:
        subst['xml_graph_assembly_source'] = "".join([xml_graph_assembly_source_line % {'Anum': Anum, 'readId': readId} for Anum, readId in enumerate(pread)])
        xml_graph.append(ET.fromstring(xml_graph_assembly % subst))
        subst['SubsetSource'] = "SliceAssembly(%s)" % assembly_id
        # subst['terraincorrection_source'] = "SliceAssembly(%s)" % assembly_id
    else:
        subst['SubsetSource'] = "Calibration(%s_0)" % assembly_id
        # subst['terraincorrection_source'] = "Calibration(%s_0)" % assembly_id


    srs_4326 = osr.SpatialReference()
    srs_4326.ImportFromEPSG(4326)
    srs_tile = osr.SpatialReference()
    srs_tile.ImportFromEPSG(subst['epsg'])
    if hasattr(srs_4326, "SetAxisMappingStrategy"):
        srs_4326.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    if hasattr(srs_tile, "SetAxisMappingStrategy"):
        srs_tile.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    transform1 = osr.CoordinateTransformation(srs_tile, srs_4326)
    regio = bb2poly(tiles_dict[tileId]['ulx'], tiles_dict[tileId]['lry'], tiles_dict[tileId]['lrx'], tiles_dict[tileId]['uly'], 120)
    regio.Transform(transform1)

    subst['subset_region'] = regio.ExportToWkt()
    subst['SubsetId'] = "Subset(%s)" % assembly_id
    xml_graph.append(ET.fromstring(xml_graph_subset % subst))

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(subst['epsg'])
    subst['terraincorrection_source'] = subst['SubsetId']
    subst['PROJCS'] = srs.ExportToWkt()
    subst['externalDEMFile'] = os.path.join(args.auxiliaries_dir, args.dem)
    subst['externalDEMNoDataValue'] = -32767
    subst['saveLocalIncidenceAngle'] = "true"
    # subst['terraincorrection_source'] = "Read(%s)" % assembly_id
    subst['IMGRESAMPLINGMETHOD'] = "BILINEAR_INTERPOLATION"
    subst['terraincorrectionId'] = assembly_id
    subst['STANDARDGRIDORIGIN'] = -1 * pixelsize / 2
    xml_graph.append(ET.fromstring(xml_graph_terraincorrection % subst))

    bn = f"{s1_startTime.strftime('%Y%m%dT%H%M%S')}_{s1_stopTime.strftime('%Y%m%dT%H%M%S')}_{missionTakeId}_{s1_relativeOrbitNumber:03d}_T{tileId}_{pixelsize}m_{platform}IWGRDH_ENVEO"
    subst['writeId'] = assembly_id
    subst['writeSource'] = "Terrain-Correction(%s)" % subst['terraincorrectionId']
    subst['writeFormat'] = 'GeoTIFF-BigTIFF' # 'GeoTIFF'
    subst['writeFile'] = os.path.join(args.intermediate_dir, "SIG0_" + bn + "_snap.tif")
    xml_graph.append(ET.fromstring(xml_graph_write % subst))

    snap_graph_file = os.path.join(args.intermediate_dir, "SIG0_" + bn + '_snap.graph.xml')
    open(snap_graph_file, "w").write(ET.tostring(xml_graph).decode('ascii'))

    return snap_graph_file, subst['writeFile'], tileId

def create_SIG0_tif(args, geotiff_in, geotiff_out, tileId):
    if geotiff_out is None:
        geotiff_out = os.path.join(args.output_dir, os.path.basename(geotiff_in.replace("_snap", "")))
    projwin = f"{tiles_dict[tileId]['ulx']} {tiles_dict[tileId]['uly']} {tiles_dict[tileId]['lrx']} {tiles_dict[tileId]['lry']}"
    cmd = f"gdal_translate -q -of GTiff -a_nodata 0 -b 1 -b 2 -r nearest -co COMPRESS=LZW -co PREDICTOR=3 -projwin {projwin} {geotiff_in} {geotiff_out}"
    retcode = subprocess_Popen(cmd.split()).wait()
    logger.debug('create_SIG0_tif (exit: %d) cmd: "%s"' % (retcode, cmd))
    if retcode != 0:
        logger.error('create_SIG0_tif (exit: %d) cmd: "%s"' % (retcode, cmd))
    return retcode


def read_parameterfile(args):
    with open(args.parameterfile, "r") as fd:
        params = yaml_load(fd)
    for k, v in params.items():
        if getattr(args, k, None) is None:
            logger.debug(f'read_parameterfile setattr: "{k}"="{v}"')
            setattr(args, k, v)
    return args


def process_sig0(args):
    snap_graph_file, snap_tif, tileId = generate_snap_graph(args)
    cmd = args.gpt + " " + str(snap_graph_file)
    retcode = subprocess_Popen(cmd.split()).wait()
    logger.debug('SNAP (exit: %d) cmd: "%s"' % (retcode, cmd))
    if retcode != 0:
        logger.error('SNAP (exit: %d) cmd: "%s"' % (retcode, cmd))
        return 111
    retcode = create_SIG0_tif(args, snap_tif, args.sig0, tileId)
    if retcode != 0:
        return 112
    return 0


if __name__ == '__main__':
    import argparse

    argparser = argparse.ArgumentParser(description="HR-WSI SIG0 processing")
    argparser.add_argument('parameterfile', help="options read from parameterfile")
    input_arg = argparser.add_argument_group('Inputs')
    input_arg.add_argument('--s1_info', help="Sentinel-1 GRDs product metadata yaml file")
    input_arg.add_argument('--tileId', help="tile Id")
    auxis_arg = argparser.add_argument_group('Auxiliaries')
    auxis_arg.add_argument('--dem', help="DEM file")
    auxis_arg.add_argument("--tiles_file", help="Sentinel-2 tiles definition yaml file")
    outpt_arg = argparser.add_argument_group('Outputs')
    outpt_arg.add_argument('--sig0', help="Sentinel-1 radarbrightness map with 10m")
    group_dir = argparser.add_argument_group('Directories')
    group_dir.add_argument("--input_dir")
    group_dir.add_argument("--output_dir")
    group_dir.add_argument("--auxiliaries_dir")
    group_dir.add_argument("--intermediate_dir")
    group_dir.add_argument("--logs_dir")
    misc_args = argparser.add_argument_group('Miscellaneous')
    misc_args.add_argument('--gpt', help="SNAP (gpt) cmdline")

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
        logger.error("Parameter setup failed!!!")
        logger.error(e)
        exit(101)

    # configure logging
    logger.setLevel(logging.DEBUG)
    lfmt = logging.Formatter(fmt='[%(levelname)s][%(filename)s][%(asctime)s] > %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
    hndl = logging.FileHandler(os.path.join(args.logs_dir, "sws_processing_routine_stdout.log"), mode='a')
    hndl.setLevel(logging.DEBUG)
    hndl.setFormatter(lfmt)
    logger.addHandler(hndl)
    hndl = logging.FileHandler(os.path.join(args.logs_dir, "sws_processing_routine_stderr.log"), mode='a')
    hndl.setLevel(logging.WARNING)
    hndl.setFormatter(lfmt)
    logger.addHandler(hndl)

    ret = 0
    try:
        # check parameters
        for i in ["tileId", "s1_info", "gpt", "dem"]:
            if getattr(args, i, None) is None:
                logger.error("Parameter {i} not given")
                exit(102)
        if len(args.s1_info) == 0:
            logger.error("No input products")
            exit(102)

        tiles_dict = yaml_load(open(os.path.join(args.auxiliaries_dir, args.tiles_file)))
        if args.s1_info is not None:
            f = os.path.join(args.input_dir, args.s1_info)
            args.s1_info = yaml_load(open(f))

        ret = process_sig0(args)
    except Exception as e:
        logging.error(e)
        ret=113

    # exit with success
    exit(ret)
