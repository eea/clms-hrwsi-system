#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from PIL import Image, ImageDraw


def make_coords_array(geoTrans,mrp):
    mrp = np.where(mrp, 255., 255.)
    (y_index, x_index) = np.indices((mrp.shape[0], mrp.shape[1]))
    x_coords = x_index * geoTrans[1] + geoTrans[0] + (geoTrans[1] / 2)  # add half the cell size
    y_coords = y_index * geoTrans[5] + geoTrans[3] + (geoTrans[5] / 2)  # to centre the point
    mrp = np.dstack((x_coords, y_coords))

    return mrp

def imageToArray(i):
    """
    Converts a Python Imaging Library array to a
    gdalnumeric image.
    """
    a = np.fromstring(i.tobytes(), 'b')
    a.shape = i.im.size[1], i.im.size[0]
    return a

# function returns a pixel for certain geolocation(geo coordinates x and y)
def world2Pixel(geoTrans, x, y):
    """
    Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
    the pixel location of a geospatial coordinate
    """
    # ulx  uly -geographical coordinates of upper left corner from  gdal.GetGeoTransform()
    ulX = geoTrans[0]
    ulY = geoTrans[3]
    # pixel size
    res_ = geoTrans[1]
    pixelX_index = int((x - ulX) / res_)
    pixelY_index = int((ulY - y) / res_)

    return (pixelX_index, pixelY_index)

def pixel2World(geoTrans,pix):

     # minXcoo, maxXcoo, minYcoo, maxYcoo = bbox
    #
    # ul_px_X, ul_px_Y = world2Pixel(geoTrans, minXcoo, maxYcoo)
    # lr_px_X, lr_px_Y = world2Pixel(geoTrans, maxXcoo, minYcoo)

    res_= geoTrans[1]

    ulXcoo = geoTrans[0] + (pix[0] * res_)
    ulYcoo = geoTrans[3] - (pix[1] * res_)

    return [ulXcoo,ulYcoo]

def get_ul_lr(geoTrans,bbox):

    minXcoo, maxXcoo, minYcoo, maxYcoo = bbox

    ul_px_X, ul_px_Y = world2Pixel(geoTrans, minXcoo, maxYcoo)
    lr_px_X, lr_px_Y = world2Pixel(geoTrans, maxXcoo, minYcoo)


    return [ul_px_X, ul_px_Y, lr_px_X, lr_px_Y]

def get_bbox_pixels(geoTrans,box):
    # vector buffer extent to image pixel coordinates
    minX, maxX, minY, maxY = box

    pxWidth = int((maxX - minX)/geoTrans[1])
    pxHeight = int((maxY - minY)/geoTrans[1])

    ulX, ulY = world2Pixel(geoTrans, minX, maxY)
    lrX, lrY = [ulX+pxWidth,ulY+pxHeight]
    return [ulX, ulY,lrX, lrY]

def clip_with_mask_cond(bbox,geoTransform,arr):

    ulX, ulY,lrX, lrY = get_bbox_pixels(geoTransform,bbox)

    if ulX<0:
        ulX=0
    if ulY<0:
        ulY=0

    raster_part_extent = arr[ulY:lrY, ulX:lrX]

    return  raster_part_extent

def clip_with_mask(bbox,geoTransform,arr):

    ulX, ulY,lrX, lrY = get_bbox_pixels(geoTransform,bbox)

    raster_part_extent = arr[ulY:lrY, ulX:lrX]

    return  raster_part_extent

def clip_with_mask_border(bbox, geoTrans,arr):
    # vector buffer extent to image pixel coordinates
    ulX, ulY, lrX, lrY = get_bbox_pixels(geoTrans, bbox)

    # size of the new image
    pxWidth = int(lrX - ulX)
    pxHeight = int(lrY - ulY)

    arr_= arr[ulY:lrY, ulX:lrX]

    raster_part_extent=[]
    # OP===ovelapping_part, mrp===missing raster part, c_x ===concatenation on x direction
    if pxWidth > (lrX + ulX):
        if ulY > 0 and pxHeight == arr_.shape[0]:
            op = arr[ulY:lrY, 0:lrX]
            # print 'op', op
            if arr_.ndim>2:
                mrp = np.empty(pxHeight*abs(ulX)*2).reshape(pxHeight,abs(ulX),2)
                mrp = make_coords_array(geoTrans, mrp)
            else:
                mrp = np.empty(pxHeight * abs(ulX)).reshape(pxHeight, abs(ulX))
                mrp = np.where(mrp, 255, 255)
            raster_part_extent = np.concatenate((mrp,op),axis=1)
            # print 'raster_part_extent',raster_part_extent
        elif ulY > 0 and pxHeight > arr_.shape[0]:
            op = arr[ulY:(arr_.shape[0]+ulY), 0:lrX]
            y = pxHeight - (arr_.shape[0])
            if arr_.ndim > 2:
                mrp_x = np.empty((arr_.shape[0]) * abs(ulX)*2).reshape(arr_.shape[0], abs(ulX),2)
                mrp_x = make_coords_array(geoTrans, mrp_x)
                mrp_y = np.empty(y * pxWidth *2).reshape(y, pxWidth,2)
                mrp_y = make_coords_array(geoTrans, mrp_y)
            else:
                mrp_x = np.empty((arr_.shape[0])*abs(ulX)).reshape(arr_.shape[0],abs(ulX))
                mrp_y = np.empty(y * pxWidth).reshape(y, pxWidth)
                mrp_x = np.where(mrp_x, 255, 255)
                mrp_y = np.where(mrp_y, 255, 255)
            c_x =np.concatenate((mrp_x, op), axis=1)
            raster_part_extent=np.concatenate((c_x, mrp_y), axis=0)
        else:
            op = arr[0:lrY, 0:lrX]
            y = abs(ulY)
            if arr_.ndim > 2:
                mrp_x = np.empty((pxHeight - (abs(ulY))) * abs(ulX)*2).reshape(pxHeight - (abs(ulY)), abs(ulX),2)
                mrp_x = make_coords_array(geoTrans, mrp_x)
                mrp_y = np.empty(y * pxWidth*2).reshape(y, pxWidth,2)
                mrp_y = make_coords_array(geoTrans, mrp_y)
            else:
                mrp_x = np.empty((pxHeight-(abs(ulY)))*abs(ulX)).reshape(pxHeight-(abs(ulY)), abs(ulX))
                mrp_y = np.empty(y * pxWidth).reshape(y, pxWidth)
                mrp_x = np.where(mrp_x, 255, 255)
                mrp_y = np.where(mrp_y, 255, 255)
            c_x = np.concatenate((mrp_x, op), axis=1)
            raster_part_extent = np.concatenate((c_x, mrp_y), axis=0)
    elif pxWidth > arr_.shape[1]:
        if ulY > 0 and pxHeight == arr_.shape[0]:
            op=arr_
            x= pxWidth -arr_.shape[1]
            if arr_.ndim > 2:
                mrp = np.empty(x*pxHeight*2).reshape(pxHeight,x,2)
                mrp = make_coords_array(geoTrans, mrp)
            else:
                mrp = np.empty(x*pxHeight).reshape(pxHeight,x)
                mrp = np.where(mrp, 255, 255)
            raster_part_extent = np.concatenate((op,mrp), axis=1)
        elif ulY > 0 and pxHeight > arr_.shape[0]:
            op = arr_
            x = pxWidth - arr_.shape[1]
            y= arr_.shape[0]
            y2=pxHeight-y
            if arr_.ndim > 2:
                mrp_x = np.empty(x * y*2).reshape(y, x, 2)
                mrp_x = make_coords_array(geoTrans, mrp_x)
                mrp_y = np.empty(y2 * pxWidth * 2).reshape(y2, pxWidth, 2)
                mrp_y = make_coords_array(geoTrans, mrp_y)
            else:
                mrp_x = np.empty(x * y).reshape(y, x)
                mrp_x = np.where(mrp_x, 255, 255)
                mrp_y = np.empty(y2 * pxWidth).reshape(y2, pxWidth)
                mrp_y = np.where(mrp_y, 255, 255)
            c_x = np.concatenate((op, mrp_x), axis=1)
            raster_part_extent = np.concatenate((c_x, mrp_y), axis=0)
        #ulY <0
        else:
            op=arr[0:lrY, ulX:(ulX+arr_.shape[1])]
            x = pxWidth - arr_.shape[1]
            y = lrY
            y2 = abs(ulY)
            if arr_.ndim > 2:
                mrp_x = np.empty(x * y*2).reshape(y, x, 2)
                mrp_x = make_coords_array(geoTrans, mrp_x)
                mrp_y = np.empty(y2 * pxWidth * 2).reshape(y2, pxWidth, 2)
                mrp_y = make_coords_array(geoTrans, mrp_y)
            else:
                mrp_x = np.empty(x * y).reshape(y, x)
                mrp_x = np.where(mrp_x, 255, 255)
                mrp_y = np.empty(y2 * pxWidth).reshape(y2, pxWidth)
                mrp_y = np.where(mrp_y, 255, 255)
            c_x = np.concatenate((op, mrp_x), axis=1)
            raster_part_extent = np.concatenate((mrp_y, c_x), axis=0)
    elif pxWidth ==(lrX - ulX):
        if ulY<0:
            op = arr[0:lrY, ulX:lrX]
            y = abs(ulY)
            if arr_.ndim > 2:
                mrp = np.empty(y * pxWidth*2).reshape(y, pxWidth,2)
                mrp = make_coords_array(geoTrans, mrp)
            else:
                mrp = np.empty(y * pxWidth).reshape(y, pxWidth)
                mrp = np.where(mrp, 255, 255)
            raster_part_extent = np.concatenate((mrp,op), axis=0)
        else:
            op = arr[ulY:(ulY+arr_.shape[0]), ulX:lrX]
            y = pxHeight - arr_.shape[0]
            if arr_.ndim > 2:
                mrp = np.empty(y * pxWidth *2).reshape(y, pxWidth,2)
                mrp = make_coords_array(geoTrans,mrp)
            else:
                mrp = np.empty(y * pxWidth).reshape(y, pxWidth)
                mrp = np.where(mrp, 255, 255)
            raster_part_extent = np.concatenate((op, mrp), axis=0)

    return  raster_part_extent


def geom2raster(geom,geomIndex, geoTrans,mask_size,points,pixels,insideValue,outsideValue):
   pts = geom.GetGeometryRef(geomIndex)
   for p in range(pts.GetPointCount()):
       points.append((pts.GetX(p), pts.GetY(p)))
   for p in points:
       pixels.append(world2Pixel(geoTrans, p[0], p[1]))
   rasterPoly = Image.new(mode="L", size=mask_size, color=outsideValue)
   rasterize = ImageDraw.Draw(rasterPoly)
   rasterize.polygon(pixels, insideValue)
   mask = imageToArray(rasterPoly)
   return mask

def get_vector_mask(feature,bbox, geomV,geoTrans):
    # Convert the layer extent to image pixel coordinates
    minX, maxX, minY, maxY = bbox
    ulX, ulY, lrX, lrY = get_bbox_pixels(geoTrans, bbox)

    # Calculate the pixel size of the new image
    pxWidth = int(lrX - ulX)
    pxHeight = int(lrY - ulY)

    mask_size=(pxWidth,pxHeight)
    #Create a new geomatrix for the image
    geoTrans = list(geoTrans)
    geoTrans[0] = minX
    geoTrans[3] = maxY
    # Map points to pixels for drawing the
    # boundary on a blank 8-bit,
    # black and white, mask image.
    points = []
    pixels = []
    masks=[]
    gt = geomV.GetGeometryType()
    if gt > 3 or gt in [-2147483642, -2147483643]:
        multigeom= feature.GetGeometryRef()
        for part in multigeom:
            nr_of_geometries = part.GetGeometryCount()
            arr_main_geom = geom2raster(part, 0, geoTrans, mask_size, points, pixels, 1, 0)
            if nr_of_geometries > 1:
                for i in range(1, nr_of_geometries):
                    points_ = []
                    pixels_ = []
                    m = geom2raster(part, i, geoTrans, mask_size, points_, pixels_, 0, 1)
                    arr_main_geom = np.multiply(arr_main_geom, m)
                masks.append(arr_main_geom)
            else:
                m = geom2raster(part, 0, geoTrans, mask_size, points, pixels, 1, 0)
                masks.append(m)
    else:
        nr_of_geometries = geomV.GetGeometryCount()
        arr_main_geom = geom2raster(geomV, 0, geoTrans, mask_size, points, pixels, 1, 0)
        if nr_of_geometries > 1:
            for i in range(1, nr_of_geometries):
                points_ = []
                pixels_ = []
                m = geom2raster(geomV, i, geoTrans, mask_size, points_, pixels_, 0, 1)
                arr_main_geom = np.multiply(arr_main_geom, m)
            mask = arr_main_geom
        else:
            mask = geom2raster(geomV, 0, geoTrans, mask_size, points, pixels, 1, 0)

    if len(masks)>0:
        masks_count=len(masks)
        mask=masks[0]
        for ma in range(1,masks_count):
            mask = mask + masks[ma]

    mask = np.where(mask == 0, 1, 0)
    return mask


def get_percentage(int1,int2,round_factor):
    return round((float(int1)/float(int2))*100, round_factor)

