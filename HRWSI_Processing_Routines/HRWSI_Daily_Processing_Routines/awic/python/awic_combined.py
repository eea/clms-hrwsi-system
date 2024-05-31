#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from osgeo import gdal, ogr
import numpy as np
import sys
import os
from datetime import datetime
from collections import Counter

from array_operations import get_vector_mask,pixel2World,get_bbox_pixels,clip_with_mask_cond,get_percentage
from shp_operations import source2memoryLayer,add_field,update_field,memoryLayer2shp,merge_memlyrs

path_wic, path_shp, date_ ,out_path= sys.argv[1], sys.argv[2], sys.argv[3],sys.argv[4]

upsamp_rate=2
# vector layer with river parts
part_ds = ogr.Open(path_shp)
part_lyr = part_ds.GetLayer()

# band with classification
r = gdal.Open(path_wic)
band = r.GetRasterBand(1) #bands start at one
arr = band.ReadAsArray().astype(np.uint8)

# # band with quality check
band_qc = r.GetRasterBand(2)
arr_qc = band_qc.ReadAsArray().astype(np.uint8)

# transformation/image parameters
geoTrans = r.GetGeoTransform()
geoTrans_upsamp=(geoTrans[0], geoTrans[1]/upsamp_rate, geoTrans[2], geoTrans[3], geoTrans[4], geoTrans[5]/upsamp_rate)

# count raster size/extent to check which river parts are overlapping it
minx = geoTrans[0]
maxy = geoTrans[3]
maxx = minx + geoTrans[1] * r.RasterXSize
miny = maxy + geoTrans[5] * r.RasterYSize

#Create ring
ring = ogr.Geometry(ogr.wkbLinearRing)
ring.AddPoint(minx, miny)
ring.AddPoint(minx, maxy)
ring.AddPoint(maxx, maxy)
ring.AddPoint(maxx, miny)
ring.AddPoint(minx, miny)

# Create polygon
raster_bbox = ogr.Geometry(ogr.wkbPolygon)
raster_bbox.AddGeometry(ring)
raster_bbox.ExportToWkt()



raster_px_size=geoTrans[1]
part_lyr.ResetReading()

parts_stats=[]
"""
1) for each polygon in raster extent  rasterization is performed,
 and a  mask  based on the result is built
2) from the whole raster subraster is clipped 
3) mask and raster are upsampled to increase accuracy
4) statistics for each polygon based on raster values are gathered

"""
for e in range(0, part_lyr.GetFeatureCount()):
    ti=datetime.now()
    feat = part_lyr.GetFeature(e)
    prop = feat.GetFID()
    #geometry of feature
    geomV = feat.GetGeometryRef()
    geomV.FlattenTo2D()
    bbox = geomV.GetEnvelope()
    if geomV.Intersects(raster_bbox):
        #  rastra subset with buffer
        clip_val = clip_with_mask_cond(bbox, geoTrans, arr)
        clip_qc = clip_with_mask_cond(bbox, geoTrans, arr_qc)
        # upsampled mask
        mask_dense = get_vector_mask(feat, bbox, geomV, geoTrans_upsamp)
        # counting pixels of mask
        mask_count_all=len(mask_dense[np.where(mask_dense<1)])
        # upsampled raster
        val_upsampl = clip_val.repeat(upsamp_rate, axis=0).repeat(upsamp_rate, axis=1)
        qc_upsampl = clip_qc.repeat(upsamp_rate, axis=0).repeat(upsamp_rate, axis=1)
        # getting  UL for cut, upsampled  rastra part
        ulX, ulY, lrX, lrY = get_bbox_pixels(geoTrans, bbox)
        ulx, uly = pixel2World(geoTrans, [ulX, ulY])
        geoTrans_ = (ulx, geoTrans_upsamp[1], 0, uly, 0, geoTrans_upsamp[1])
        mask_ulX, mask_ulY, mask_lrX, mask_lrY = get_bbox_pixels(geoTrans_, bbox)
        subraster_size=[0,0,val_upsampl.shape[1], val_upsampl.shape[0]]
        ## common area
        common_area_ulx=max([subraster_size[0], mask_ulX])
        common_area_uly=max([subraster_size[1], mask_ulY])
        common_area_lrx = min([subraster_size[2], mask_lrX])
        common_area_lry = min([subraster_size[3], mask_lrY])
        common_area=[common_area_ulx,common_area_uly,common_area_lrx,common_area_lry]
        submask=[common_area_ulx-mask_ulX,
                 common_area_uly- mask_ulY,
                 common_area_lrx-mask_ulX ,
                 common_area_lry-mask_ulY]
        mask_clipped= mask_dense[submask[1]:submask[3] ,submask[0]:submask[2]]
        # clipping raster with mask bbox
        clip_val_upsampl = val_upsampl[common_area[1]:common_area[3],common_area[0]:common_area[2]]
        clip_qc_upsampl = qc_upsampl[common_area[1]:common_area[3],common_area[0]:common_area[2]]
        # masking raster
        val_upsampl_masked = np.ma.masked_array(clip_val_upsampl, mask=mask_clipped)
        qc_upsampl_masked = np.ma.masked_array(clip_qc_upsampl, mask=mask_clipped)
        # getting true values from masked array
        val_data = val_upsampl_masked[val_upsampl_masked.mask == False]
        qc_data = qc_upsampl_masked[qc_upsampl_masked.mask == False]
        # counting unique values
        cntr = Counter(val_data)
        cntr_qc = Counter(qc_data)
        parts_prop = [prop, cntr, cntr_qc,mask_count_all]
        parts_stats.append(parts_prop)


parts_ids = set([val[0] for val in parts_stats])

data = {}

for part in list(parts_ids):
    data[part] = {
        'percentage': {'water_perc': 0, 'ice_perc': 0, 'other_perc': 0, 'nd_perc':0, 'cloud_perc': 0},
        'count_qc': {'high': 0, 'lower': 0, 'decreasing': 0, 'lowest': 0},
        'avg': None
    }

for i in parts_stats:
    for k,v in data.items():
        if i[0] == k:
            for j in i[1]:
                if int(j)==1:
                    data[k]['percentage']['water_perc'] = get_percentage(i[1][j],i[3],0)
                elif int(j) == 100:
                    data[k]['percentage']['ice_perc'] = get_percentage(i[1][j],i[3],0)
                elif int(j) == 205:
                    data[k]['percentage']['cloud_perc'] = get_percentage(i[1][j],i[3],0)
                elif int(j) == 254:
                    data[k]['percentage']['other_perc'] = get_percentage(i[1][j],i[3],0)
            for qc in i[2]:
                if int(qc) == 0 or int(qc) == 205:
                    data[k]['count_qc']['high'] += i[2][qc]
                elif int(qc) == 1:
                    data[k]['count_qc']['lower'] = i[2][qc]
                elif int(qc) == 2:
                    data[k]['count_qc']['decreasing'] = i[2][qc]
                elif int(qc) == 3:
                    data[k]['count_qc']['lowest'] = i[2][qc]




for part, v in data.items():
    count_sum = sum(v['percentage'].values())
    v['percentage']['nd_perc'] = 100-count_sum
    count_sum_qc = sum(v['count_qc'].values())

    if count_sum_qc > 0:
        qc_avg = ((0*v['count_qc']['high']) + (1*v['count_qc']['lower'])+ (2*v['count_qc']['decreasing'])+ (3*v['count_qc']['lowest']))/count_sum_qc
        v['avg'] =int(round(qc_avg))

    else:
        v['avg'] = 255


# AWIC LAYER (preparation of shapefile structure)
hydro_parts_ds, hydro_parts_lyr = source2memoryLayer('hydro_parts_raw', part_lyr)

fields = [
    ['date', ogr.OFTString], ['QC', ogr.OFTInteger]
    ]
fields_perc = [
    ['water_perc', ogr.OFTInteger],
    ['ice_perc', ogr.OFTInteger], ['other_perc', ogr.OFTInteger],
    ['cloud_perc', ogr.OFTInteger], ['nd_perc', ogr.OFTInteger]
]

fields_ = fields + fields_perc
for field in fields_:
    add_field(hydro_parts_lyr, field[0], field[1])

dt = datetime.strptime(date_, '%Y%m%dT%H%M%S')

for i in range(0, hydro_parts_lyr.GetFeatureCount()):
    feature=hydro_parts_lyr.GetFeature(i)
    fid= feature.GetFID()
    if fid in data.keys():
        for field_data in fields_perc:
            field_value = data[fid]['percentage'][field_data[0]]
            update_field(hydro_parts_lyr, feature, field_data[0], field_value)
        field_value_qc = data[fid]['avg']
        update_field(hydro_parts_lyr, feature, 'QC', field_value_qc)
        update_field(hydro_parts_lyr, feature, 'date', str(dt))
    else:
        hydro_parts_lyr.DeleteFeature(fid)

    nd_field_indx = feature.GetFieldIndex('nd_perc')
    if feature.GetFieldAsInteger(nd_field_indx) == 100:
        hydro_parts_lyr.DeleteFeature(fid)


hydro_parts_lyr.ResetReading()
hydro_parts_lyr.SyncToDisk()

head, tail = os.path.split(out_path)

# merge or create new
if os.path.exists(out_path):
    awic_ds = ogr.Open(out_path,1)
    awic_lyr = awic_ds.GetLayer()
    merge_memlyrs(awic_lyr,hydro_parts_lyr)
else:
    memoryLayer2shp(hydro_parts_lyr,out_path, tail)

print (datetime.now() -ti)
