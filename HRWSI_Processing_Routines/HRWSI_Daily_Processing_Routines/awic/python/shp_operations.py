#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from osgeo import ogr
import os


# new multi polygon  memory layer
def source2memoryLayer(name,shp_lyr):
    driver_memory = ogr.GetDriverByName('Memory')
    memory_layer_ds = driver_memory.CreateDataSource(name+'_ds')
    memory_lyr = memory_layer_ds.CreateLayer(name, shp_lyr.GetSpatialRef(), geom_type=ogr.wkbMultiPolygon)
    memory_lyr_dfn = memory_lyr.GetLayerDefn()
    shp_lyr_dfn = shp_lyr.GetLayerDefn()
    for i in range(0, shp_lyr_dfn.GetFieldCount()):
        fieldDefn = shp_lyr_dfn.GetFieldDefn(i)
        memory_lyr.CreateField(fieldDefn)
    # define feature
    memory_fieldcount= memory_lyr_dfn.GetFieldCount()
    for i in range(0, shp_lyr.GetFeatureCount()):
        f = shp_lyr.GetFeature(i)
        geom = f.GetGeometryRef()
        dstfeature = ogr.Feature(memory_lyr_dfn)
        dstfeature.SetGeometry(geom)
        for i in range(0, memory_fieldcount):
            dstfeature.SetField(memory_lyr_dfn.GetFieldDefn(i).GetNameRef(), f.GetField(i))
        memory_lyr.CreateFeature(dstfeature)
        dstfeature = None
    shp_lyr.ResetReading()
    memory_lyr.ResetReading()
    return [memory_layer_ds, memory_lyr]


def memoryLayer2shp(memory_lyr, output_path, name):
    memory_lyr.ResetReading()
    srs = memory_lyr.GetSpatialRef()
    output_geometry_type=memory_lyr.GetGeomType()
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_path):
        driver.DeleteDataSource(output_path)
    output_ds = driver.CreateDataSource(output_path)
    output_lyr = output_ds.CreateLayer(name, srs, geom_type=output_geometry_type)
    output_lyr_dfn = output_lyr.GetLayerDefn()
    memory_lyr_dfn = memory_lyr.GetLayerDefn()
    for i in range(0, memory_lyr_dfn.GetFieldCount()):
        fieldDefn = memory_lyr_dfn.GetFieldDefn(i)
        output_lyr.CreateField(fieldDefn)
    # define feature
    output_fieldcount = output_lyr_dfn.GetFieldCount()
    for f in memory_lyr:
        geom=f.GetGeometryRef()
        dstfeature = ogr.Feature(output_lyr_dfn)
        dstfeature.SetGeometry(geom)
        for i in range(0, output_fieldcount):
            dstfeature.SetField(output_lyr_dfn.GetFieldDefn(i).GetNameRef(), f.GetField(i))
        output_lyr.CreateFeature(dstfeature)
        dstfeature = None
    memory_lyr.ResetReading()
    output_lyr.ResetReading()
    output_ds=None
    output_lyr=None

def add_field(layer, field_name, field_type):
    ind = layer.FindFieldIndex(field_name, True)
    if ind != -1:
        layer.DeleteField(ind)
    fieldDef = ogr.FieldDefn(field_name, field_type)
    layer.CreateField(fieldDef)

def update_field(lyr,feature,field_name,val):
    feature.SetField(field_name,val)
    lyr.SetFeature(feature)

def merge_memlyrs(lay1, lay2):
    lay2.ResetReading()
    lay1.ResetReading()
    lay1_dfn = lay1.GetLayerDefn()
    lay2_dfn = lay2.GetLayerDefn()
    for feat in lay2:
        out_feat = ogr.Feature(lay1.GetLayerDefn())
        out_feat.SetGeometry(feat.GetGeometryRef().Clone())
        for i in range(0, lay1_dfn.GetFieldCount()):
            for j in range(0, lay2_dfn.GetFieldCount()):
                if lay1_dfn.GetFieldDefn(i).GetNameRef()==lay2_dfn.GetFieldDefn(j).GetNameRef():
                    out_feat.SetField(lay1_dfn.GetFieldDefn(i).GetNameRef(), feat.GetField(j))
        lay1.CreateFeature(out_feat)
        out_feat = None
        lay1.SyncToDisk()
    lay2.ResetReading()
    lay1.ResetReading()

