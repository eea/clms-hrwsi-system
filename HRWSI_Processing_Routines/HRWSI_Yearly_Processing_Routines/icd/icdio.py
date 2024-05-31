import os, alphashape, datetime, argparse, yaml, inspect, traceback
from shapely.geometry import Polygon, LineString, Point
import numpy as np
import mahotas as mh
from osgeo import gdal, osr
gdal.UseExceptions()

def log(*message,level="INFO"):
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    message = map(str,message)
    message = ''.join(message)
    if message[:4] == "LIS:":
        try:
            level = message.split(":")[3].split()[1]
            filename = message.split(":")[4]
            timestamp = message[4:23]
            message = ":".join(message.split(":")[5:])
        except:
            level = "WARNING"
            filename = "LIS"
            message = "LIS log line could not be parsed. The line is: " + message[4:]
    else:
        filename = os.path.split(inspect.stack()[1].filename)[1]
    filename = os.path.splitext(filename)[0] if os.path.splitext(filename)[1] == '.py' else filename

    levels = ["DEBUG","INFO","WARNING","ERROR","CRITICAL"]
    thisLevel = levels.index(level)
    minLevel = levels.index(logLevel)
    if thisLevel >= minLevel:
        if thisLevel >= levels.index("WARNING"):
            f = open(logErrFile,'a')
        else:
            f = open(logOutFile,'a')
        for line in message.split('\n'):
            logMessage = "[%s][%s][%s] > %s" % (level,filename,timestamp,line)
            print(logMessage)
            f.write(logMessage)
            f.write('\n')
        f.close()


def readRaster(fname):
    log("Reading ",fname,level="DEBUG")
    try:
        gtif = gdal.Open(fname)
        data = gtif.GetRasterBand(1)
        data_shape = (data.YSize,data.XSize)
        data = np.array(data.ReadAsArray())
        geoTransform = gtif.GetGeoTransform()
        projectionRef = gtif.GetProjectionRef()
        return (data,geoTransform,projectionRef)
    except Exception as e:
        log("41: Problem in reading ", fname,level="ERROR")
        log(traceback.format_exc(),level='ERROR')
        return None

def writeRaster(fname,rasterData, geoTransform, projectionRef, colorMap = None, noData=None):
    log("Writing into file ",fname,level="DEBUG")
    rasterDataDtypes = [np.uint8, np.uint16, np.int16, np.uint32, np.int32]
    gdalDtypes = [gdal.GDT_Byte, gdal.GDT_UInt16, gdal.GDT_Int16, gdal.GDT_UInt32, gdal.GDT_Int32]
    noDatas = [255, 65535, 32767, 4294967295, 2147483647]
    dtypeIndex = rasterDataDtypes.index(rasterData.dtype) if rasterData.dtype in rasterDataDtypes else 0
    dtype = gdalDtypes[dtypeIndex]
    noData = noData if noData is not None else noDatas[dtypeIndex]

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

def writeThumbnail(fname,rasterData,colorMap=None):
    log("Creating thumbnail",fname,level="DEBUG")
    if colorMap is None:
        mh.imsave(fname,rasterData)
        return True
    r,c = np.indices((1000,1000),dtype=np.float64)
    r = (r*rasterData.shape[0]/1000.).astype(np.int32)
    c = (c*rasterData.shape[1]/1000.).astype(np.int32)
    rasterData = rasterData[r,c]
    imageData = np.zeros(rasterData.shape,dtype=np.uint8)
    imageData = np.dstack((imageData,imageData,imageData,imageData)).transpose(2,0,1)
    for value in colorMap:
        for c in range(4):
            np.place(imageData[c],rasterData==value,colorMap[value][c])
    imageData = imageData.transpose(1,2,0)
    log("Writing into file",fname,level="DEBUG")
    mh.imsave(fname,imageData)
    return True

def setBit(data,bit,value,where=None):
    if where is None:
        where = np.ones(data.shape,np.bool_)
    newData = np.zeros(data.shape,dtype=data.dtype)
    for b in range(int(str(data.dtype).replace('uint','').replace('int',''))):
        mask = np.bitwise_and(np.right_shift(data,b),1)
        if b == bit:
            if isinstance(where,list):
                mask[where[0],where[1]] = value
            else:
                np.place(mask,where,value)
        newData = np.bitwise_or(newData,np.left_shift(mask.astype(data.dtype),b))
    return newData

def getBit(data,bit):
    mask = np.bitwise_and(np.right_shift(data,bit),1)
    return mask.astype(np.bool_)


def getAlphashape(raster,noData, geoTransform, projectionRef):
    log("Calculating alphashape",level="INFO")
    productPoints = []
    productIndices = np.indices(raster.shape).transpose(1,2,0)
    if np.sum(raster!=noData) != 0:
        cLeft, cRight = 0,raster.shape[1]
        for c, col in enumerate(raster.transpose(1,0)):
            colMask = col != noData
            if np.sum(colMask) != 0:
                cLeft = c
                break
        for c, col in enumerate(raster.transpose(1,0)[::-1]):
            colMask = col != noData
            if np.sum(colMask) != 0:
                cRight = colMask.shape[0]-c
                break
        for r,row in enumerate(raster):
            rowMask = row[cLeft:cRight] != noData
            if np.sum(rowMask) == 0:
                continue
            for c,leftPoint in enumerate(rowMask):
                if leftPoint:
                    productPoints.append(productIndices[r,c+cLeft][::-1])
                    break
            for c,rightPoint in enumerate(rowMask[::-1]):
                if rightPoint:
                    productPoints.append(productIndices[r,cRight-1-c][::-1])
                    break
    
    # Exception for nonpolygon boundaries
    if len(productPoints) == 0:
        # Probably not possible
        log('No point can be deduced to calculate alphashape. Raster is probably all nodata. Using maximum extent.',level="WARNING")
        productPoints = [productIndices[0][0],productIndices[0][1],productIndices[1][0],productIndices[1][1]]
    else:
        productAlphashape = alphashape.alphashape(productPoints, 0.)
        if type(productAlphashape) is LineString or type(productAlphashape) is Point:
            log('Deduced points to calculate alphashape forms a %s, not form a polygon. Using a slightly larger rectangle.' % type(productAlphashape).__name__, level="WARNING")
            # xmin ymin xmax ymax
            productPoints = [min(list(zip(*productPoints))[0]),min(list(zip(*productPoints))[1]),max(list(zip(*productPoints))[0]),max(list(zip(*productPoints))[1])]
            # set offset if on the border
            productPoints[0] = 1 if productPoints[0] == 0 else productPoints[0]
            productPoints[1] = 1 if productPoints[1] == 0 else productPoints[1]
            productPoints[2] = productIndices[-1][-1][0]-1 if productPoints[2] == productIndices[-1][-1][0] else productPoints[2]
            productPoints[3] = productIndices[-1][-1][1]-1 if productPoints[3] == productIndices[-1][-1][1] else productPoints[3]
            # make it 1 pixel larger
            productPoints = [(productPoints[0]-1,productPoints[1]-1),(productPoints[0]-1,productPoints[3]+1),(productPoints[2]+1,productPoints[1]-1),(productPoints[2]+1,productPoints[3]+1)]
            productAlphashape = alphashape.alphashape(productPoints, 0.)
        productPoints = productAlphashape.exterior.coords[:]
        
    source = osr.SpatialReference()
    source.ImportFromWkt(projectionRef)
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(source,target)
    for p,productPoint in enumerate(productPoints):
        productPoint = [productPoint[0]+0.5,productPoint[1]+0.5]
        productPoint = (geoTransform[0] + productPoint[0]*geoTransform[1],geoTransform[3] + productPoint[1]*geoTransform[5])
        productPoint = transform.TransformPoint(productPoint[0],productPoint[1])
        productPoints[p] = [productPoint[1],productPoint[0]]
    productPoints = Polygon(productPoints)
    return str(productPoints)

def getGeoBounds(raster,geoTransform,projectionRef):
    source = osr.SpatialReference()
    source.ImportFromWkt(projectionRef)
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(source,target)
    lats = []
    lons = []
    for point in [[0,0],[0,raster.shape[1]],[raster.shape[0],0],[raster.shape[0],raster.shape[1]]]:
        point = (geoTransform[0] + point[0]*geoTransform[1],geoTransform[3] + point[1]*geoTransform[5])
        point = transform.TransformPoint(point[0],point[1])
        lats.append(point[0])
        lons.append(point[1])
    bounds = [min(lons),max(lons),min(lats),max(lats)]
    return bounds


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('parameters_file',help='Path to the configuration parameters file')
sysargv = vars(parser.parse_args())
if sysargv['parameters_file'] is not None:
    pFile = open(sysargv['parameters_file'],'r')
    parameters = yaml.load(pFile,Loader=yaml.Loader)
    pFile.close()
    auxDir = parameters['aux_dir']
    wlFile = os.path.join(auxDir,parameters['water_layer_file'])
    logOutFile = parameters['log_out_file']
    os.makedirs(os.path.split(logOutFile)[0],exist_ok=True)
    logErrFile = parameters['log_err_file']
    os.makedirs(os.path.split(logErrFile)[0],exist_ok=True)
    logLevel = parameters['log_level'] if 'log_level' in parameters else 'DEBUG'
else:
    auxDir = None
    wlFile = None
    logOutFile = None
    logErrFile = None
    logLevel = None
