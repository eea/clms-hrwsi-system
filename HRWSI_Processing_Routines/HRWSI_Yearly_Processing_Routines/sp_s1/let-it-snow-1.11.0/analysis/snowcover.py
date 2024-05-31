import sys
import os
import errno
import re
from datetime import datetime, timedelta, date
from osgeo import osr, gdal
from osgeo.gdalnumeric import *
from osgeo.gdalconst import *
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from xml.dom import minidom
import scipy.optimize as opti
from scipy.stats import mstats
import shutil
import matplotlib.gridspec as gridspec
from matplotlib.colors import LogNorm
from pyproj import Proj, transform
import glob
import random
import pandas as pd
from sklearn import datasets, linear_model
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from math import sqrt
import math
from matplotlib.ticker import PercentFormatter






class snowcover:
    def __init__(self):



        self.nb_shift_days = 4
        self.path_palettes = "/work/OT/siaa/Theia/Neige/CoSIMS/zacharie/snowcover/palettes"
        self.path_outputs = "/work/OT/siaa/Theia/Neige/CoSIMS/zacharie/snowcover/OUTPUTS"
        self.path_THEIA = "/work/OT/siaa/Theia/Neige/CoSIMS/zacharie/snowcover/INPUTS"
        self.path_LIS = "/work/OT/siaa/Theia/Neige/PRODUITS_NEIGE_LIS_develop_1.5"
        self.date_format = "%Y-%m-%d"
        self.max_accuracy = 5
        self.f_tree = "/work/OT/siaa/Theia/Neige/CoSIMS/data/tree_cover_density/original_tiling/TCD_2015_020m_eu_03035_d05_full.tif"









    #Check the directory d and recuperate a list of files with names containing a date between dateDebut - self.nb_shift_days and dateFin + self.nb_shift_days
    def getListDateDecal(self,dateDebut,dateFin,d,decal):
        lo=[]
        li = []

        try:
            li = os.listdir(d)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EACCES:
                return lo
            else:
                raise

        for i in sorted(li):
            date = self.getDateFromStr(i)
            if date == '' : continue
            if (date >= self.getDateFromStr(dateDebut) - timedelta(days = decal)) and (date <= self.getDateFromStr(dateFin) + timedelta(days = decal)) :
                lo.append(os.path.join(d,i))
        return lo

    #Create a directory with path dos
    def mkdir_p(self,dos):
        try:
            os.makedirs(dos)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(dos):
                pass
            else:
                raise



    #Extract a date from a string
    def getDateFromStr(self,N):
        sepList = ["","-","_","/"]
        date = ''
        for s in sepList :
            found = re.search('\d{4}'+ s +'\d{2}'+ s +'\d{2}', N)
            if found != None :
               date = datetime.strptime(found.group(0), '%Y'+ s +'%m'+ s +'%d').date()
               break
        return date



    #Extract a Tile number from a string
    def getTileFromStr(self,N):

        tile = ''
        found = re.search('T' + '\d{2}' +'\w{3}', N)
        if found != None : tile = found.group(0)

        return tile

    #Extract a EPSG number from a string
    def getEpsgFromStr(self,N):

        epsg = ''
        found = re.search('\d{5}', N)
        if found != None : epsg = found.group(0)

        return str(epsg)

    #Get the coordinates of the overlapping region between two rasters G1 and G2
    #he coordinates are in the projection of G2
    def getOverlapCoords(self,G1,G2):

        epsg1 = (gdal.Info(G1, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])
        epsg2 = (gdal.Info(G2, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])

        GT1 = G1.GetGeoTransform()
        minx1 = GT1[0]
        maxy1 = GT1[3]
        maxx1 = minx1 + GT1[1] * G1.RasterXSize
        miny1 = maxy1 + GT1[5] * G1.RasterYSize

        GT2 = G2.GetGeoTransform()
        minx2 = GT2[0]
        maxy2 = GT2[3]
        maxx2 = minx2 + GT2[1] * G2.RasterXSize
        miny2 = maxy2 + GT2[5] * G2.RasterYSize

        if epsg1 not in epsg2 :
            minx1 , miny1 = self.reproject(epsg1,epsg2,minx1,miny1)
            maxx1 , maxy1 = self.reproject(epsg1,epsg2,maxx1,maxy1)


        minx3 = max(minx1,minx2)
        maxy3 = min(maxy1,maxy2)
        maxx3 = min(maxx1,maxx2)
        miny3 = max(miny1,miny2)

        # if there is no intersection
        if (minx3 > maxx3 or miny3 > maxy3) :
            return None,None,None,None

        return minx3, maxy3, maxx3, miny3


    #Check if two rasters G1 and G2 are overlapping
    def isOverlapping(self,G1,G2):

        epsg1 = (gdal.Info(G1, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])
        epsg2 = (gdal.Info(G2, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])

        GT1 = G1.GetGeoTransform()
        minx1 = GT1[0]
        maxy1 = GT1[3]
        maxx1 = minx1 + GT1[1] * G1.RasterXSize
        miny1 = maxy1 + GT1[5] * G1.RasterYSize

        GT2 = G2.GetGeoTransform()
        minx2 = GT2[0]
        maxy2 = GT2[3]
        maxx2 = minx2 + GT2[1] * G2.RasterXSize
        miny2 = maxy2 + GT2[5] * G2.RasterYSize

        if epsg1 not in epsg2 :
            minx1 , miny1 = self.reproject(epsg1,epsg2,minx1,miny1)
            maxx1 , maxy1 = self.reproject(epsg1,epsg2,maxx1,maxy1)

        minx3 = max(minx1,minx2)
        maxy3 = min(maxy1,maxy2)
        maxx3 = min(maxx1,maxx2)
        miny3 = max(miny1,miny2)

        # no intersection
        if (minx3 > maxx3 or miny3 > maxy3) :
            return False
        else:
            return True



    #Check if the Gsmall raster is entirely overlapping with the raster Gbig
    def isInside(self,Gbig,Gsmall):

        epsgbig = (gdal.Info(Gbig, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])
        epsgsmall = (gdal.Info(Gsmall, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])



        GTbig = Gbig.GetGeoTransform()
        minxbig = GTbig[0]
        maxybig = GTbig[3]
        maxxbig = minxbig + GTbig[1] * Gbig.RasterXSize
        minybig = maxybig + GTbig[5] * Gbig.RasterYSize

        GTsmall = Gsmall.GetGeoTransform()
        minxsmall = GTsmall[0]
        maxysmall = GTsmall[3]
        maxxsmall = minxsmall + GTsmall[1] * Gsmall.RasterXSize
        minysmall = maxysmall + GTsmall[5] * Gsmall.RasterYSize

        if epsgbig not in epsgsmall :
            minxsmall , minysmall = self.reproject(epsgsmall,epsgbig,minxsmall,minysmall)
            maxxsmall , maxysmall = self.reproject(epsgsmall,epsgbig,maxxsmall,maxysmall)

        if minxbig <= minxsmall and maxxbig >= maxxsmall and minybig <= minysmall and maxybig >=maxysmall :
            return True
        else :
            return False


    #Reproject coordinates x1 and y1 from inEPSG to outEPSG
    def reproject(self,inEPSG,outEPSG,x1,y1):

        inProj = Proj(init='EPSG:' + inEPSG)
        outProj = Proj(init='EPSG:'+ outEPSG)
        x2,y2 = transform(inProj,outProj,x1,y1)

        return x2, y2





    #Prepare the FSC and NDSI datasets necessary for calibration and validation
    #dirName (string) : name of the directory which will contain the resulting dataset (FSC and NDSI tif files) (self.path_outputs/dirName) (optional)
    #dateDebut, dateFin ("YYYY-MM-DD") : The tif files are made from rasters dating between dateDebut - self.nb_shift_days and dateFin + self.nb_shift_days.
    #If dateFin is empty, The periode of time consist of only the one date dateDebut
    #source (string) : name of the raster source (PLEIADES, SPOT, IZAS,etc...)
    #epsgFSC (string) : Imposed projection number of the FSC raster. (optional)
    #resampling (string) : raster resampling method ("average","near",etc...) (optional)
    #isFSC (bool) : indication if the snow rasters already have FSC values (optional)
    #SNWval (list of int) : value(s) of snow pixels in the snow raster (optional)
    #NSNWval (list of int) : value(s) of no-snow pixels in the snow raster (optional)
    #NDval (list of int) : value(s) of no-data pixels in the snow raster(optional)
    #tiles (list of string) : tile numbers of the L2A products overlapping the snow rasters. If empty, makeDataSets will search them itself. (optional)
    #selection (string) : method of L2A products selection (closest or cleanest) (optional)
    #return True or False to indicate success
    def makeDataSet(self,dirName = "",dateDebut = "",dateFin = "",source = "",epsgFSC = "",resampling = "average",isFSC = False,SNWval = [1],NSNWval = [0],NDval = [], tiles = [],selection = "closest"):


        #parameters check
        if dateFin == "":
            dateFin = dateDebut

        if self.getDateFromStr(dateDebut) == '' or self.getDateFromStr(dateFin) == '':
            print("ERROR makeDataSet : error in input date")
            return False
        if source == "" :
            print("ERROR makeDataSet : source must be specified")
            return False

        if dirName == "":
            dirName = "DATASETS_" + source + "_" + dateDebut
            if dateDebut != dateFin : dirName = dirName + "_" + dateFin



        #search overlapping tiles
        if tiles == [] :
            print("Searching for overlapping tiles")
            tiles = self.searchTiles(source = source,epsgFSC = epsgFSC)
            if tiles == []:
                print("ERROR makeDataSet : no tiles found")
                return False
        print("tiles: ",tiles)


        #select snow and L2A products
        print("Selecting FSC and L2A products")
        list_products = self.selectProducts(dateDebut = dateDebut,dateFin = dateFin,source = source, epsgFSC = epsgFSC,tiles = tiles,selection = selection)
        if list_products == {}:
            print("ERROR selectProducts : no products found")
            return False

        #display selected products on terminal
        print("nb of FSC products = " + str(len(list_products)))
        for FSC_date in list_products :
            f_FSC = list_products[FSC_date][0]
            l_L2A = list_products[FSC_date][1]
            print("DATE = " + str(FSC_date) + "\n     FSC = " + str(f_FSC) + "\n     nb of L2A tiles = " + str(len(l_L2A)) )
            for tile , epsgL2A, L2A  in l_L2A :
                print("     " + tile + " : " + L2A)

        #produce FSC and NDSI datasets
        success = self.products2DataSets(dirName = dirName,dateDebut = dateDebut,dateFin = dateFin,source = source,epsgFSC = epsgFSC,list_products = list_products,resampling = "average",isFSC = False,SNWval = SNWval,NSNWval = NSNWval,NDval = NDval)

        return success




    #produce a list of the Sentinel-2 tiles overlapping with the snow rasters of a source. (ex: T31TCH for PLEIADES)
    #source (string) : source of the snow rasters (PLEIADES,IZAS,etc...)
    #epsgFSC (string) : Imposed epsg projection number (optional)
    #return a list of tiles names
    def searchTiles(self,source = "",epsgFSC = ""):

        tiles_overlap = []


        if source == "" :
            print("ERROR searchTiles: source must be specified")
            return tiles_overlap



        #For each FSC raster we look for the overlapping S2 tiles
        path_FSC_dir = os.path.join(self.path_THEIA,"FSC",source)
        pxs = []
        for FSC_product in os.listdir(path_FSC_dir):
            f_FSC = os.path.join(path_FSC_dir,FSC_product)
            g_FSC = gdal.Open(f_FSC)
            px = g_FSC.GetGeoTransform()[0]
            if px not in pxs :
                print("\n")
                print("Check tiles for FSC file",FSC_product)
                pxs.append(px)

                # we set the EPSG if necessary
                if epsgFSC != "" :
                    
                    g_FSC = gdal.Warp('',g_FSC,format= 'MEM',srcSRS="EPSG:" + epsgFSC)

                # we check each S2 tiles for overlaps
                for tile in os.listdir(self.path_LIS) :
                    if not os.path.isdir(os.path.join(self.path_LIS,tile)) : continue
                    print ("Check tile : " + tile)
                    try:
                        L2A_product = os.listdir(os.path.join(self.path_LIS,tile))[-1]
                    except OSError as exc:  # Python >2.5
                        if exc.errno == errno.EACCES:
                            continue
                        else:
                            raise
                    print("Check overlapping with L2A file " + L2A_product)
                    f_L2A = os.path.join(self.path_LIS,tile,L2A_product,"swir_band_extracted.tif")
                    g_L2A = gdal.Open(f_L2A)
                    if self.isOverlapping(g_L2A,g_FSC) :
                        print("Overlap present")
                        if tile not in tiles_overlap :
                            tiles_overlap.append(tile)
                print("\n")
        return tiles_overlap






    #select a list of snow rasters and their coreesponding L2A products
    #dateDebut, dateFin ("YYYY-MM-DD") : The datasets are made from rasters dating between dateDebut - self.nb_shift_days and dateFin + self.nb_shift_days.
    # If dateFin is empty, The periode of time consist of only the one date dateDebut
    #source (string) : name of the raster source (PLEIADES, SPOT, IZAS,etc...)
    #epsgFSC (string) : Imposed projection number of the FSC raster. (optional)
    #tiles (list of string) : tile numbers of the L2A products overlapping the snow rasters. If empty, makeDataSets will search them itself. (optional)
    #selection (string) : method of L2A products selection (closest or cleanest) (optional)
    #return a dictionary in the format list_products[date] = [path of a snow raster,[tile of a L2A product,epsg of a L2A product, path of a L2A product]]
    def selectProducts(self,dateDebut = "",dateFin = "",source = "", epsgFSC = "",tiles = [],selection = ""):

        list_products = {}

        #parameters check
        if dateFin == "": dateFin = dateDebut

        if selection == "":
            selection = self.selection

        if self.getDateFromStr(dateDebut) == '' or self.getDateFromStr(dateFin) == '':
            print("ERROR selectProducts : error in input date")
            return list_products
        if source == "" :
            print("ERROR selectProducts : source must be specified")
            return list_products

        # We create a list of the FSC products (with paths)

        path_FSC_dir = os.path.join(self.path_THEIA,"FSC",source)
        if os.path.isdir(path_FSC_dir):
            list_FSC_products = self.getListDateDecal(dateDebut,dateFin,path_FSC_dir,0)
        if list_FSC_products == [] :
            print ("ERROR selectProducts : No FSC product found for source " + source + " in directory " + path_FSC_dir)
            return list_products



        for tile in tiles :

            print("Check tile : " + tile)
            path_L2A_dir = os.path.join(self.path_LIS,tile)
            if os.path.isdir(path_L2A_dir):
                list_L2A_products = self.getListDateDecal(dateDebut,dateFin,path_L2A_dir,self.nb_shift_days)
            if list_L2A_products == [] :
                print ("No L2A product found for tile " + tile + " in directory " + path_L2A_dir)


            L2A_product = glob.glob(os.path.join(self.path_LIS,tile,'*SENTINEL*'))[0]
            f_tile = os.path.join(L2A_product,"LIS_PRODUCTS","LIS_SEB.TIF")
            g_tile = gdal.Open(f_tile)


            for f_FSC in list_FSC_products :


                g_FSC = gdal.Open(f_FSC)

                if epsgFSC != "" :
                    
                    g_FSC = gdal.Warp('',g_FSC,format= 'MEM',srcSRS="EPSG:" + epsgFSC )

                dateFSC = self.getDateFromStr(f_FSC)
                minx, maxy, maxx, miny = self.getOverlapCoords(g_FSC,g_tile)
                if minx == None and maxy == None: continue


                epsgL2A = ""
                L2A = ""
                ind = self.nb_shift_days + 1
                NDR1 = 100
                NDR2 = 100
                for L2A_product in list_L2A_products:
                    if "SENTINEL" not in L2A_product : continue
                    dateL2A = self.getDateFromStr(L2A_product)
                    lag = dateL2A - dateFSC
                    if abs(lag.days) >  self.nb_shift_days : continue

                    f_L2A = os.path.join(L2A_product,"LIS_PRODUCTS","LIS_SEB.TIF")
                    
                    g_L2A = gdal.Translate('',f_L2A,format= 'MEM',projWin = [minx, maxy, maxx, miny])
                    bandL2A = BandReadAsArray(g_L2A.GetRasterBand(1))



                    NDR2 = (float(len(bandL2A[bandL2A == 205]) + len(bandL2A[bandL2A == 254])) / float(np.size(bandL2A))) * 100


                    check = None

                    if "cleanest" in selection :
                        check =  NDR2 < 100 and ((abs(NDR2 - NDR1) < 0.0001 and abs(lag.days) < ind) or (NDR1 - NDR2 >= 0.0001))
                    else :
                        check = abs(lag.days) < ind

                    if check :
                        #print("\n")
                        print("date FSC",dateFSC,"date L2A",dateL2A)
                        print("NoDataRatio1 = ",NDR1,"NoDataRatio2 = ",NDR2,"lag = ",lag.days)
                        #print("\n")
                        ind = abs(lag.days)
                        L2A = L2A_product
                        NDR1 = NDR2
                        epsgL2A = (gdal.Info(g_L2A, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])
                    else : print("date rejetee")


                if L2A == "" : continue

                print("Chosen L2A : " + L2A)

                if dateFSC not in list_products.keys() :
                    list_products[dateFSC] = [f_FSC,[]]
                    list_products[dateFSC][1].append([tile,epsgL2A,L2A])
                else :

                    list_products[dateFSC][1].append([tile,epsgL2A,L2A])


        return list_products





    # Produce FSC and NDSI datasets.
    #dirName (string) : name of the directory containing the datasets (self.path_outputs/dirName) (optional)
    #dateDebut, dateFin ("YYYY-MM-DD") : The datasets are made from rasters dating between dateDebut - self.nb_shift_days and dateFin + self.nb_shift_days.
    # If dateFin is empty, The periode of time consist of only the one date dateDebut
    #source (string) : name of the raster source (PLEIADES, SPOT, IZAS,etc...)
    #epsgFSC (string) : Imposed projection number of the FSC raster. (optional)
    #resampling (string) : raster resampling method ("average","near",etc...) (optional)
    #isFSC (bool) : indication if the snow rasters already have FSC values (optional)
    #SNWval (list of int) : value(s) of snow pixels in the snow raster (optional)
    #NSNWval (list of int) : value(s) of no-snow pixels in the snow raster (optional)
    #NDval (list of int) : value(s) of no-data pixels in the snow raster(optional)
    #list_products : dictionary in the format list_products[date] = [path of a snow raster,[tile of a L2A product,epsg of a L2A product, path of a L2A product]]
    def products2DataSets(self,dirName = "",dateDebut = "",dateFin = "",source = "",epsgFSC = "",list_products = {},resampling = "average",isFSC = False,SNWval = [1],NSNWval = [0],NDval = []):



        #parameters check
        if dateFin == "":
            dateFin = dateDebut

        if self.getDateFromStr(dateDebut) == '' or self.getDateFromStr(dateFin) == '':
            print("ERROR products2DataSets : error in input date")
            return False
        if source == "" :
            print("ERROR products2DataSets : source must be specified")
            return False

        if list_products == {} :
            print("ERROR products2DataSets : no products specified")
            return False

        if dirName == "":
            dirName = "DATASETS_" + source + "_" + dateDebut
            if dateDebut != dateFin : dirName = dirName + "_" + dateFin




        dataSetDir = os.path.join(self.path_outputs,dirName)
        shutil.rmtree(dataSetDir,ignore_errors=True)
        self.mkdir_p(dataSetDir)
        nb_results = 0

        #DEFINITION DE LA PERIODE D'ANALYSE##########################################
        #On prend une date de debut et une date de fin
        print("\nPeriode d'analyse : " + dateDebut + "-" + dateFin)


        #POUR CHAQUE DATE:##########################################
        for dateFSC in list_products :

            nd = 100000
            dir_tifs_date = os.path.join(dataSetDir,"TIFS",dateFSC.strftime(self.date_format))
            self.mkdir_p(dir_tifs_date)


            f_FSC = list_products[dateFSC][0]
            l_L2A = list_products[dateFSC][1]

            print("\nCalcul pour : " + dateFSC.strftime("%Y/%m/%d"))



            # we get the FSC projection system

            if epsgFSC == "" :
                epsgFSC = (gdal.Info(f_FSC, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])





            # On ouvre, converti et re-echantillonne le FSC

            print("\nConversion des valeurs FSC")
            #on change les valeurs FSC
            g_FSC_o = None
            
            g_FSC_o = gdal.Warp('',f_FSC,format= 'MEM',outputType = gdal.GDT_Float32)

            g_FSC_o = gdal.Warp('',g_FSC_o,format= 'MEM', dstNodata = 9999)
            g_FSC_o = gdal.Translate('',g_FSC_o,format= 'MEM',noData = nd)






            #g_FSC_o = gdal.Translate('',g_FSC_o,format= 'MEM',noData = None)
            a_FSC = BandReadAsArray(g_FSC_o.GetRasterBand(1))
            print("nodata999",str(len(a_FSC[a_FSC == 9999])))
            print("nodataNAN",str(len(a_FSC[np.isnan(a_FSC)])))
            if len(NDval) > 0 :
                for nData in NDval :
                    cond = np.where((a_FSC == nData) | (np.isnan(a_FSC)))
                    a_FSC[cond] = 9999
            if len(NSNWval) > 0 :
                for noSnow in NSNWval :
                    a_FSC[a_FSC == noSnow] = 0
            if len(SNWval) > 0 :
                if isFSC == False :
                    for snow in SNWval :
                        a_FSC[a_FSC == snow] = 1
            g_FSC_o.GetRasterBand(1).WriteArray(a_FSC)
            a_FSC = None

            
            gdal.Translate(os.path.join(dir_tifs_date,"INPUT_FSC.tif"),g_FSC_o,format= 'GTiff',noData = 9999)



            print("\nTraitement des tuiles")



            l_g_FSC = {}



            # On prepare un FSC reprojete pour chaque projection
            for tile , epsgS2 , L2A_product in  l_L2A :

                if epsgS2 not in l_g_FSC.keys():
                    
                    g_FSC = gdal.Warp('',g_FSC_o,format= 'MEM',srcSRS="EPSG:" + epsgFSC,dstSRS="EPSG:" + epsgS2,resampleAlg=resampling,xRes= 20,yRes= 20)
                    a_FSC = BandReadAsArray(g_FSC.GetRasterBand(1))
                    a_FSC[np.isnan(a_FSC)] = 9999
                    a_FSC[a_FSC > 1] = 9999
                    g_FSC.GetRasterBand(1).WriteArray(a_FSC)
                    a_FSC = None
                    #g_FSC = gdal.Warp('',g_FSC,format= 'MEM',dstNodata = 9999)
                    l_g_FSC[epsgS2] = g_FSC
                    a_FSC = BandReadAsArray(g_FSC.GetRasterBand(1))
                    print("resnodata999",str(len(a_FSC[a_FSC == 9999])))
                    print("resnodataNAN",str(len(a_FSC[np.isnan(a_FSC)])))
                    gdal.Translate(os.path.join(dir_tifs_date,"RESAMPLED_FSC_EPSG-"+epsgS2+".tif"),g_FSC,format= 'GTiff',noData = 9999)

                    g_FSC = None





            for tile , epsgS2 , L2A_product in  sorted(l_L2A,key=lambda l:l[1]) :


                
            # We look for the red, green & swir bands tiff files + mask
                f_green = ""
                f_swir = ""
                f_red = ""
                f_MSK = ""
                f_compo = ""


                for f in os.listdir(L2A_product) :
                    if ("green_band_resampled.tif" in f) :
                        f_green = os.path.join(L2A_product,f)
                    elif ("red_band_resampled.tif" in f) :
                        f_red = os.path.join(L2A_product,f)
                    elif ("swir_band_extracted.tif" in f) :
                        f_swir = os.path.join(L2A_product,f)
                    elif ("LIS_PRODUCTS" in f) :
                        if os.path.isfile(os.path.join(L2A_product,f,"LIS_SEB.TIF")):
                            f_msk = os.path.join(L2A_product,f,"LIS_SEB.TIF")
                        if os.path.isfile(os.path.join(L2A_product,f,"LIS_COMPO.TIF")):
                            f_compo = os.path.join(L2A_product,f,"LIS_COMPO.TIF")



                    #If there is a file missing, we skip to the next tile
                    if f_green == "" or f_red == "" or f_swir == "" or f_msk == "": continue


                    # On calcul les coord de overlap dans la projection L2A
                    print("\nCalcul coordonnees de chevauchement")
                    g_msk = gdal.Open(f_msk)
                    minx, maxy, maxx, miny = self.getOverlapCoords(l_g_FSC[epsgS2],g_msk)


                    #on decoupe les fichiers L2A
                    #on decoupe le masque
                    print("\nDecoupage du masque")
                    g_msk= gdal.Translate(os.path.join(dir_tifs_date,"INPUT_SEB_" + tile + "_EPSG-" + epsgS2 + ".tif"),g_msk,format= 'GTiff',projWin = [minx, maxy, maxx, miny])
                    print("\nDecoupage du compo")
                    gdal.Translate(os.path.join(dir_tifs_date,"INPUT_COMPO_" + tile + "_EPSG-" + epsgS2 + ".tif"),f_compo,format= 'GTiff',projWin = [minx, maxy, maxx, miny])

                    #on load et decoupe l'image bande verte,
                    print("\nDecoupage bande verte")
                    g_green = gdal.Translate('',f_green,format= 'MEM',projWin = [minx, maxy, maxx, miny])
                    #on load et decoupe l'image bande rouge
                    print("\nDecoupage bande rouge")
                    g_red = gdal.Translate('',f_red,format= 'MEM',projWin = [minx, maxy, maxx, miny])
                    #on load et decoupe l'image bande swir
                    print("\nDecoupage bande IR")
                    g_swir= gdal.Translate('',f_swir,format= 'MEM',projWin = [minx, maxy, maxx, miny])


                    #on decoupe une copie de FSC
                    g_FSC_c = gdal.Translate('',l_g_FSC[epsgS2],format= 'MEM',projWin = [minx, maxy, maxx, miny])

                    #on produit un raster avec les memes conditions
                    raster = g_FSC_c


                    #on calcul les NDSI pour le chevauchement
                    print("\nCalcul des NDSI")
                    bandV = BandReadAsArray(g_green.GetRasterBand(1))
                    g_green = None
                    bandIR = BandReadAsArray(g_swir.GetRasterBand(1))
                    g_swir = None
                    bandR = BandReadAsArray(g_red.GetRasterBand(1))
                    g_red = None
                    #on extrait la bande neige
                    MSK = BandReadAsArray(g_msk.GetRasterBand(1))
                    g_msk = None
                    #on extrait la bande FSC
                    FSC = BandReadAsArray(g_FSC_c.GetRasterBand(1))



                    #On calcul les NDSI
                    a = (bandV - bandIR).astype(float)
                    b = (bandV + bandIR).astype(float)
                    NDSI = a/b



                    #On remplace les pixels non utilisables par des nodatas

                    cond1 = np.where((MSK != 100) )
                    NDSI[cond1] = 9999
                    FSC[cond1] = 9999
                    MSK = None
                    cond2 = np.where(FSC > 1 | np.isnan(FSC) | np.isinf(FSC))
                    NDSI[cond2] = 9999
                    FSC[cond2] = 9999
                    cond3 = np.where(np.isnan(NDSI) | np.isinf(NDSI))
                    FSC[cond3] = 9999
                    NDSI[cond3] = 9999




                    cond5 = np.where((NDSI < 0) | (NDSI > 1))
                    FSC[cond5] = 9999
                    NDSI[cond5] = 9999




                    raster.GetRasterBand(1).WriteArray(NDSI)

                    gdal.Translate(os.path.join(dir_tifs_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsgS2 + ".tif"),raster,format= 'GTiff',noData = 9999)
                    raster.GetRasterBand(1).WriteArray(FSC)

                    gdal.Translate(os.path.join(dir_tifs_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsgS2 + ".tif"),raster,format= 'GTiff',noData = 9999)



                for proj in l_g_FSC :


                    
                    g_FSC_m = gdal.Warp('',g_FSC_c,format= 'MEM',dstSRS="EPSG:" + proj,xRes= 20,yRes= 20)
                    NODATA = BandReadAsArray(g_FSC_m.GetRasterBand(1))
                    #NODATA[np.isnan(NODATA)] = 9999
                    #NODATA[NODATA != 9999] = 9999
                    condnd = np.where((NODATA != nd) & (~np.isnan(NODATA)))
                    NODATA[condnd] = 9999
                    g_FSC_m.GetRasterBand(1).WriteArray(NODATA)
                    
                    g_FSC = gdal.Warp('',[l_g_FSC[proj],g_FSC_m],format= 'MEM')
                    l_g_FSC[proj] = g_FSC
                    a_FSC = None
                    g_FSC = None


            nb_results += 1



        if nb_results > 0 :
           print("\nNumber of processed dates:" + str(nb_results))
           return True
        else :
           print("\nERROR products2DataSets : No date processed")
           return False




    #From the FSC and NDSI datasets found in dirName, calibrate the a and b parameters of the FSC = 0.5atanh(aNDSI+b)+0.5 model
    #The datasets are separated into a training and a testing set
    #The calibration is made from the training set dans validated with the testing set
    #dirName (string) : name of the directory containing the datasets (self.path_outputs/dirName)
    #source (string) : name of the FSC dataset source (PLEIADES, SPOT, IZAS,etc...)
    #percTest (float) : percentage of the datasets used for the validation of the calibrated model.
    #return the a and b parameters and the rmse of the validation
    def calibrateModel(self,dirName,source,percTest):




        dataSetDir = os.path.join(self.path_outputs,dirName)
        path_tifs = os.path.join(dataSetDir,"TIFS")
        path_cal = os.path.join(dataSetDir,"CALIBRATION")



        sorted_dates = sorted(os.listdir(path_tifs))
        dateDebut = sorted_dates[0]
        dateFin = sorted_dates[-1]

        NDSIALL = []
        FSCALL = []


        path_cal_date = os.path.join(path_cal,dateDebut + "_" + dateFin)
        shutil.rmtree(path_cal_date, ignore_errors=True)
        self.mkdir_p(path_cal_date)

        f= open(os.path.join(path_cal_date,source + "_CALIBRATION_RESULTS.txt"),"w")
        f.write("\nDates :")
        nb_dates = 0



        for d in sorted(os.listdir(path_tifs)):
            date = self.getDateFromStr(d)
            if date == '' : continue
            print(date)
            path_tifs_date = os.path.join(path_tifs,d)


            epsgs = {}
            for tif in os.listdir(path_tifs_date) :
                epsg = self.getEpsgFromStr(tif)
                if epsg == '': continue
                if epsg not in epsgs :
                    epsgs[epsg] = []

            tiles = []
            for tif in os.listdir(path_tifs_date) :
                epsg = self.getEpsgFromStr(tif)
                tile = self.getTileFromStr(tif)
                if epsg == '' or tile == '': continue
                if tile not in epsgs[epsg]:
                    epsgs[epsg].append(tile)



            for epsg in epsgs :
                for tile in epsgs[epsg]:
                    g_FSC = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                    FSCALL.append(BandReadAsArray(g_FSC.GetRasterBand(1)).flatten())
                    g_NDSI = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                    NDSIALL.append(BandReadAsArray(g_NDSI.GetRasterBand(1)).flatten())

            f.write("\n      " + d)
            nb_dates += 1

        print("Eliminate Nodata pixels")
        NDSIALL = np.hstack(NDSIALL)
        FSCALL = np.hstack(FSCALL)
        cond1 = np.where((FSCALL != 9999) & (~np.isnan(FSCALL)) & (~np.isinf(FSCALL)))
        NDSIALL = NDSIALL[cond1]
        FSCALL = FSCALL[cond1]

        cond2 = np.where( (NDSIALL != 9999) & (~np.isnan(NDSIALL)) & (~np.isinf(NDSIALL)))
        FSCALL = FSCALL[cond2]
        NDSIALL = NDSIALL[cond2]



        if len(FSCALL) < 2 :
            f.close()
            shutil.rmtree(path_cal_date, ignore_errors=True)
            print("ERROR calibrateModel : dataSet too small")
            return 0,0,0


        NDSI_train, NDSI_test, FSC_train, FSC_test = train_test_split(NDSIALL, FSCALL, test_size=percTest)


        #CALIBRATION
        print("CALIBRATION")
        fun = lambda x: sqrt(mean_squared_error(0.5*np.tanh(x[0]*NDSI_train+x[1])+0.5,FSC_train))

        model = opti.minimize(fun,(3.0,-1.0),method = 'Nelder-Mead')#method = 'Nelder-Mead')

        a = model.x[0]
        b = model.x[1]
        success = model.success
        rmse_cal = model.fun
        print("CALIBRATION SUCCESS : ",success)
        print("CALIBRATION RMSE : ",rmse_cal)



        # Plot figure with subplots
        fig = plt.figure()
        st = fig.suptitle(source + " : CALIBRATION FOR THE PERIOD " + dateDebut + " - " + dateFin)
        # set up subplot grid
        gridspec.GridSpec(2,2)

        # 2D histo de calibration
        ax = plt.subplot2grid((2,2), (0,0))

        plt.title("CALIBRATION WITH THE TRAINING SET")
        plt.ylabel('Training FSC',size = 10)
        plt.xlabel('Training NDSI',size = 10)
        plt.hist2d(NDSI_train,FSC_train,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'), norm=LogNorm())

        n = np.arange(min(NDSI_train),1.01,0.01)

        line = 0.5*np.tanh(a*n+b) +  0.5

        plt.plot(n, line, 'r', label='FSC=0.5*tanh(a*NDSI+b)+0.5\na={:.2f} b={:.2f}\nRMSE={:.2f}'.format(a,b,rmse_cal))
        plt.legend(fontsize=10,loc='upper left')

        plt.colorbar()
        ratio = 1
        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)



        # VALIDATION

        # prediction of FSC from testing NDSI
        FSC_pred = 0.5*np.tanh(a*NDSI_test+b) +  0.5

        # error
        er_FSC = FSC_pred - FSC_test

        # absolute error
        abs_er_FSC = abs(er_FSC)

        # mean error
        m_er_FSC = np.mean(er_FSC)

        # absolute mean error
        abs_m_er_FSC = np.mean(abs_er_FSC)

        #root mean square error
        rmse_FSC = sqrt(mean_squared_error(FSC_pred,FSC_test))

        #correlation
        corr_FSC = mstats.pearsonr(FSC_pred,FSC_test)[0]

        #standard deviation
        stde_FSC = np.std(er_FSC)


        #correlation, erreur moyenne, ecart-type, rmse

        # 2D histo de validation
        ax = plt.subplot2grid((2,2), (0,1))

        plt.title("VALIDATION WITH THE TESTING SET")
        plt.ylabel('predicted FSC',size = 10)
        plt.xlabel('testing FSC',size = 10)
        plt.hist2d(FSC_test,FSC_pred,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'),norm=LogNorm())
        slope, intercept, r_value, p_value, std_err = mstats.linregress(FSC_test,FSC_pred)
        n = np.array([min(FSC_test),1.0])
        line = slope * n + intercept

        plt.plot(n, line, 'b', label='y = {:.2f}x + {:.2f}\ncorr={:.2f} rmse={:.2f}'.format(slope,intercept,corr_FSC,rmse_FSC))
        plt.plot(n, n, 'g', label='y = 1.0x + 0.0')

        plt.legend(fontsize=10,loc='upper left')
        plt.colorbar()
        ratio = 1
        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)

        # 1D histo de residus
        ax = plt.subplot2grid((2,2), (1,0),rowspan=1, colspan=2)
        plt.title("FSC RESIDUALS")
        plt.ylabel('amount of data points',size = 10)
        plt.xlabel('FSC pred - test',size = 10)
        xticks = np.arange(-1.0, 1.1, 0.1)
        plt.xticks(xticks)
        plt.hist(er_FSC,bins=40,weights=np.ones(len(er_FSC)) / len(er_FSC))
        plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
        plt.grid(True)


        # fit subplots & save fig
        fig.tight_layout()
        fig.set_size_inches(w=16,h=10)
        st.set_y(0.95)
        fig.subplots_adjust(top=0.85)
        fig.savefig(os.path.join(path_cal_date,'PLOT_CAL_' + source + '_' + dateDebut + "_" + dateFin + '.png'))
        plt.close(fig)



        f.write("\n")
        f.write("\nCALIBRATION" )
        f.write("\n  Number of 20x20m data points : " + str(len(NDSI_train)))
        f.write("\n lin. reg. NDSI on FSC : 0.5*tanh(a*NDSI+b)+0.5 : a = " + str(a) + " ; b = " + str(b))
        f.write("\n root mean square err. : " + str(rmse_cal))


        f.write("\n")

        f.write("\nVALIDATION" )
        f.write("\n  Number of 20x20m data points : " + str(len(NDSI_test)))
        f.write("\n  corr. coef. : " + str(corr_FSC))
        f.write("\n  std. err. : " + str(stde_FSC))
        f.write("\n  mean err. : " + str(m_er_FSC))
        f.write("\n  abs. mean err. : " + str(abs_m_er_FSC))
        f.write("\n  root mean square err. : " + str(rmse_FSC))

        f.close()


        return a,b,rmse_FSC




    #With the FSC and NDSI datasets found in evaldirName, evaluate the a and b parameters of the FSC = 0.5atanh(aNDSI+b)+0.5 model
    #calDirName (string) : name of the directory containing the datasets used for the calibration (self.path_outputs/dirName)
    #calSource (string) : name of the FSC dataset source (PLEIADES, SPOT, IZAS,etc...) used for the calibration
    #evalDirName (string) : name of the directory containing the datasets used for the evaluation (self.path_outputs/dirName)
    #evalSource (string) : name of the FSC dataset source (PLEIADES, SPOT, IZAS,etc...) used for the evaluation
    #a,b (float) : paramaters of the FSC = 0.5atanh(aNDSI+b)+0.5 model
    #return rmse of the evaluation
    def evaluateModel(self,calDirName,evalDirNames,calSource,evalSources,a,b):


        calDataSetDir = os.path.join(self.path_outputs,calDirName)
        path_eval = os.path.join(calDataSetDir,"EVALUATION")
        title = "EVAL_" + calSource + "_WITH"



        NDSI_test = []
        FSC_test = []

        title2 = "EVAL"
        for evalDirName in evalDirNames :
            title2 = title2 + "_" + evalDirName

        for evalSource in evalSources :
            title = title + "_" + evalSource

        path_eval_dir = os.path.join(path_eval,title2)
        shutil.rmtree(path_eval_dir, ignore_errors=True)

        self.mkdir_p(path_eval_dir)

        f= open(os.path.join(path_eval_dir,title + ".txt"),"w")
        f.write("\nCalibration dataset :" + calDirName)
        f.write("\nModel : FSC = 0.5*tanh(a*NDSI+b) +  0.5 with :")
        f.write("\n        a = " + str(a) + " b = " + str(b))
        f.write("\nEvaluation dataSets :")





        for evalDirName in evalDirNames :

            f.write("\n     "+ evalDirName)

            evalDataSetDir = os.path.join(self.path_outputs,evalDirName)
            path_tifs = os.path.join(evalDataSetDir,"TIFS")




            for d in sorted(os.listdir(path_tifs)):
                date = self.getDateFromStr(d)
                if date == '' : continue
                print(date)
                path_tifs_date = os.path.join(path_tifs,d)


                epsgs = {}
                for tif in os.listdir(path_tifs_date) :
                    epsg = self.getEpsgFromStr(tif)
                    if epsg == '': continue
                    if epsg not in epsgs :
                        epsgs[epsg] = []

                tiles = []
                for tif in os.listdir(path_tifs_date) :
                    epsg = self.getEpsgFromStr(tif)
                    tile = self.getTileFromStr(tif)
                    if epsg == '' or tile == '': continue
                    if tile not in epsgs[epsg]:
                        epsgs[epsg].append(tile)



                for epsg in epsgs :
                    for tile in epsgs[epsg]:
                        g_FSC = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                        FSC_test.append(BandReadAsArray(g_FSC.GetRasterBand(1)).flatten())
                        g_NDSI = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                        NDSI_test.append(BandReadAsArray(g_NDSI.GetRasterBand(1)).flatten())



        print("Eliminate Nodata pixels")
        NDSI_test = np.hstack(NDSI_test)
        FSC_test = np.hstack(FSC_test)
        cond1 = np.where((FSC_test != 9999) & (~np.isnan(FSC_test)) & (~np.isinf(FSC_test)))
        NDSI_test = NDSI_test[cond1]
        FSC_test = FSC_test[cond1]

        cond2 = np.where( (NDSI_test != 9999) & (~np.isnan(NDSI_test)) & (~np.isinf(NDSI_test)))
        FSC_test = FSC_test[cond2]
        NDSI_test = NDSI_test[cond2]



        if len(FSC_test) < 2 :
            f.close()
            shutil.rmtree(path_eval_dir, ignore_errors=True)
            print("ERROR evaluateModel : dataSet too small")
            return 0



        # VALIDATION

        # prediction of FSC from testing NDSI
        FSC_pred =  0.5*np.tanh(a*NDSI_test+b) +  0.5

        # error
        er_FSC = FSC_pred - FSC_test

        # absolute error
        abs_er_FSC = abs(er_FSC)

        # mean error
        m_er_FSC = np.mean(er_FSC)

        # absolute mean error
        abs_m_er_FSC = np.mean(abs_er_FSC)

        #root mean square error
        rmse_FSC = sqrt(mean_squared_error(FSC_pred,FSC_test))

        #correlation
        corr_FSC = mstats.pearsonr(FSC_pred,FSC_test)[0]

        #standard deviation
        stde_FSC = np.std(er_FSC)


        # Plot figure with subplots
        fig = plt.figure()
        st = fig.suptitle(title)
        # set up subplot grid
        gridspec.GridSpec(2,2)



        # 2D histos de FSC vs NDSI
        ax = plt.subplot2grid((2,2), (0,0))
        plt.ylabel('testing FSC',size = 10)
        plt.xlabel('testing NDSI',size = 10)
        plt.hist2d(NDSI_test,FSC_test,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'),norm=LogNorm())
        n = np.arange(min(NDSI_test),1.01,0.01)
        line = 0.5*np.tanh(a*n+b) +  0.5
        plt.plot(n, line, 'r', label='Predicted FSC')
        plt.legend(fontsize=10,loc='upper left')
        plt.colorbar()
        ratio = 1
        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)

        # 2D histos de validation
        ax = plt.subplot2grid((2,2), (0,1))
        plt.ylabel('predicted FSC',size = 10)
        plt.xlabel('testing FSC',size = 10)
        plt.hist2d(FSC_test,FSC_pred,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'),norm=LogNorm())
        slope, intercept, r_value, p_value, std_err = mstats.linregress(FSC_test,FSC_pred)
        n = np.array([min(FSC_test),1.0])
        line = slope * n + intercept
        plt.plot(n, line, 'b', label='y = {:.2f}x + {:.2f}\ncorr={:.2f} rmse={:.2f}'.format(slope,intercept,corr_FSC,rmse_FSC))
        plt.plot(n, n, 'g', label='y = 1.0x + 0.0')
        plt.legend(fontsize=10,loc='upper left')
        plt.colorbar()
        ratio = 1
        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)


        # 1D histo de residus
        ax = plt.subplot2grid((2,2), (1,0),rowspan=1, colspan=2)
        plt.title("FSC RESIDUALS")
        plt.ylabel('amount of data points',size = 10)
        plt.xlabel('FSC pred - test',size = 10)
        xticks = np.arange(-1.0, 1.1, 0.1)
        plt.xticks(xticks)
        plt.hist(er_FSC,bins=40,weights=np.ones(len(er_FSC)) / len(er_FSC))
        plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
        plt.grid(True)


        # fit subplots & save fig
        fig.tight_layout()
        fig.set_size_inches(w=16,h=10)
        st.set_y(0.95)
        fig.subplots_adjust(top=0.85)
        fig.savefig(os.path.join(path_eval_dir,'PLOT_' + title + '.png'))
        plt.close(fig)



        f.write("\n")

        f.write("\nEVALUATION" )
        f.write("\n  Number of 20x20m data points : " + str(len(NDSI_test)))
        f.write("\n  corr. coef. : " + str(corr_FSC))
        f.write("\n  std. err. : " + str(stde_FSC))
        f.write("\n  mean err. : " + str(m_er_FSC))
        f.write("\n  abs. mean err. : " + str(abs_m_er_FSC))
        f.write("\n  root mean square err. : " + str(rmse_FSC))

        f.close()


        return rmse_FSC





    #Plots all the FSC datasets vs NDSI datasets found in dirName (one png date)
    #dirName (string) : name of the directory containing the datasets (self.path_outputs/dirName)
    #source (string) : name of the FSC dataset source (PLEIADES, SPOT, IZAS,etc...)
    #return a success bool
    def PlotPeriode(self,dirName,source):

        dataSetDir = os.path.join(self.path_outputs,dirName)
        path_tifs = os.path.join(dataSetDir,"TIFS")
        path_plots = os.path.join(dataSetDir,"PLOTS")

        print("Start plotting the periode")
        NDSIALL = []
        FSCALL = []
        NDSIALL2 = []
        FSCALL2 = []

        sorted_dates = sorted(os.listdir(path_tifs))
        dateDebut = sorted_dates[0]
        dateFin = sorted_dates[-1]

        path_plots_date = os.path.join(path_plots,dateDebut + "_" + dateFin)
        self.mkdir_p(path_plots_date)

        f= open(os.path.join(path_plots_date,"INFO.txt"),"w")
        f.write("\nDates :")
        nb_dates = 0





        for d in sorted_dates:
            date = self.getDateFromStr(d)
            if date == '' : continue
            print(date)
            path_tifs_date = os.path.join(path_tifs,d)


            epsgs = {}
            for tif in os.listdir(path_tifs_date) :
                epsg = self.getEpsgFromStr(tif)
                if epsg == '': continue
                if epsg not in epsgs :
                    epsgs[epsg] = []

            tiles = []
            for tif in os.listdir(path_tifs_date) :
                epsg = self.getEpsgFromStr(tif)
                tile = self.getTileFromStr(tif)
                if epsg == '' or tile == '': continue
                if tile not in epsgs[epsg]:
                    epsgs[epsg].append(tile)



            for epsg in epsgs :
                for tile in epsgs[epsg]:
                    g_FSC = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                    FSCALL.append(BandReadAsArray(g_FSC.GetRasterBand(1)).flatten())
                    g_NDSI = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                    NDSIALL.append(BandReadAsArray(g_NDSI.GetRasterBand(1)).flatten())

            f.write("\n      " + d)
            nb_dates += 1

        print("Eliminate Nodata pixels")
        NDSIALL = np.hstack(NDSIALL)
        FSCALL = np.hstack(FSCALL)
        cond1 = np.where((FSCALL != 9999) & (~np.isnan(FSCALL)) & (~np.isinf(FSCALL)))
        NDSIALL = NDSIALL[cond1]
        FSCALL = FSCALL[cond1]

        cond2 = np.where( (NDSIALL != 9999) & (~np.isnan(NDSIALL)) & (~np.isinf(NDSIALL)))
        FSCALL = FSCALL[cond2]
        NDSIALL = NDSIALL[cond2]

        cond3 = np.where((FSCALL != 0) & (FSCALL != 1))
        NDSIALL2 = NDSIALL[cond3]
        FSCALL2 = FSCALL[cond3]

        if len(FSCALL2) < 2 :
            f.close()
            shutil.rmtree(path_plots_date, ignore_errors=True)
            return False
        f.write("\nNumber of dates : " + str(nb_dates))


        print("Create plots")
        minNDSI = min(NDSIALL)
        list_FSC_box = [FSCALL[np.where((NDSIALL >= 0.8) & (NDSIALL <= 1))]]
        list_labels_box = ["[ 0.8\n1 ]"]
        b = 0.8
        while minNDSI < b :
            a = b - 0.2
            list_FSC_box.insert(0,FSCALL[np.where((NDSIALL >= a) & (NDSIALL < b))])
            list_labels_box.insert(0,"[ "+ "{0:.1f}".format(a) +"\n"+ "{0:.1f}".format(b) +" [")
            b = b - 0.2


        minNDSI2 = min(NDSIALL2)
        list_FSC_box2 = [FSCALL2[np.where((NDSIALL2 >= 0.8) & (NDSIALL2 <= 1))]]
        list_labels_box2 = ["[ 0.8\n1 ]"]
        b = 0.8
        while minNDSI2 < b :
            a = b - 0.2
            list_FSC_box2.insert(0,FSCALL2[np.where((NDSIALL2 >= a) & (NDSIALL2 < b))])
            list_labels_box2.insert(0,"[ "+ "{0:.1f}".format(a) +"\n"+ "{0:.1f}".format(b) +" [")
            b = b - 0.2





        # Plot figure with subplots
        fig = plt.figure()
        st = fig.suptitle(source + " : FSC / NDSI FOR THE PERIOD " + dateDebut + " - " + dateFin)
        # set up subplot grid
        gridspec.GridSpec(2,3)

        # 2D histo avec FSC = 0 et FSC = 1
        ax = plt.subplot2grid((2,3), (0,2))


        plt.ylabel('0 <= FSC <= 1')
        plt.xlabel('NDSI')
        plt.hist2d(NDSIALL,FSCALL,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'), norm=LogNorm())

        if NDSIALL != [] and FSCALL != [] :
            slopeA, interceptA, r_valueA, p_valueA, std_errA = mstats.linregress(NDSIALL,FSCALL)
            slopeB, interceptB, r_valueB, p_valueB, std_errB = mstats.linregress(FSCALL,NDSIALL)
            n = np.array([minNDSI,1.0])
            lineA = slopeA*n+interceptA
            lineB = (n-interceptB)/slopeB
            plt.plot(n, lineA, 'g', label='MA: a={:.2f} b={:.2f}\ncorr={:.2f} std_err={:.3f}'.format(slopeA,interceptA,r_valueA,std_errA))
            plt.plot(n, lineB, 'r', label='MB: a={:.2f} b={:.2f}\ncorr={:.2f} std_err={:.3f}'.format(1/slopeB,-interceptB/slopeB,r_valueB,std_errB))
            plt.legend(fontsize=6,loc='upper left')

        plt.colorbar()
        ratio = 1
        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)

        # 2D histo sans FSC = 0 et FSC = 1
        ax = plt.subplot2grid((2,3), (1,2))


        plt.ylabel('0 < FSC < 1')
        plt.xlabel('NDSI')
        plt.hist2d(NDSIALL2,FSCALL2,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'),norm=LogNorm())
        if NDSIALL2 != []  and FSCALL2 != [] :
            slopeA2, interceptA2, r_valueA2, p_valueA2, std_errA2 = mstats.linregress(NDSIALL2,FSCALL2)
            slopeB2, interceptB2, r_valueB2, p_valueB2, std_errB2 = mstats.linregress(FSCALL2,NDSIALL2)
            n = np.array([minNDSI2,1.0])
            lineA = slopeA2*n+interceptA2
            lineB = (n-interceptB2)/slopeB2
            plt.plot(n, lineA, 'g', label='MA: a={:.2f} b={:.2f}\ncorr={:.2f} std_err={:.3f}'.format(slopeA2,interceptA2,r_valueA2,std_errA2))
            plt.plot(n, lineB, 'r', label='MB: a={:.2f} b={:.2f}\ncorr={:.2f} std_err={:.3f}'.format(1/slopeB2,-interceptB2/slopeB2,r_valueB2,std_errB2))
            plt.legend(fontsize=6,loc='upper left')
        plt.colorbar()
        ratio = 1
        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)



        # boxplot avec FSC = 0 et FSC = 1
        ax = plt.subplot2grid((2,3), (0,0),rowspan=1, colspan=2)
        plt.title('ANALYSIS WITH 0 <= FSC <= 1')
        plt.ylabel('0 <= FSC <= 1')
        plt.xlabel('NDSI')
        plt.boxplot(list_FSC_box,labels = list_labels_box)



        # boxplot sans FSC = 0 et FSC = 1
        ax = plt.subplot2grid((2,3), (1,0),rowspan=1, colspan=2)
        plt.title('ANALYSIS WITH 0 < FSC < 1')
        plt.ylabel('0 < FSC < 1')
        plt.xlabel('NDSI')
        plt.boxplot(list_FSC_box2,labels = list_labels_box2)

        # fit subplots & save fig
        fig.tight_layout()
        fig.set_size_inches(w=16,h=10)
        st.set_y(0.95)
        fig.subplots_adjust(top=0.85)
        fig.savefig(os.path.join(path_plots_date,'PLOT_FSC_NDSI_' + source + '_' + dateDebut + "_" + dateFin + '.png'))
        plt.close(fig)


        f.write("\nFor  0 <= FSC <= 1 : " )
        f.write("\n  Number of data points : " + str(len(NDSIALL)))
        if NDSIALL != [] and FSCALL != [] :
            f.write("\n lin. reg. FSC on NDSI (MA): FSC = aNDSI + b : a = " + str(slopeA) + " ; b = " + str(interceptA))
            f.write("\n  std. err. (MA): " + str(std_errA))
            f.write("\n lin. reg. NDSI on FSC (MB): FSC = aNDSI + b : a = " + str(1/slopeB) + " ; b = " + str(-interceptB/slopeB))
            f.write("\n  std. err. (MB): " + str(std_errB))
            f.write("\n  corr. coef. : " + str(r_valueA))


        f.write("\nFor  0 < FSC < 1 : " )
        f.write("\n  Number of data points : " + str(len(NDSIALL2)))
        if NDSIALL2 != [] and FSCALL2 != [] :
            f.write("\n lin. reg. FSC on NDSI (MA): FSC = aNDSI + b : a = " + str(slopeA2) + " ; b = " + str(interceptA2))
            f.write("\n  std. err. (MA): " + str(std_errA2))
            f.write("\n lin. reg. NDSI on FSC (MB): FSC = aNDSI + b : a = " + str(1/slopeB2) + " ; b = " + str(-interceptB2/slopeB2))
            f.write("\n  std. err. (MB): " + str(std_errB2))
            f.write("\n  corr. coef. : " + str(r_valueA2))
        f.close()

        print ("\n plotting finished")
        NDSI = None
        FSC = None
        NDSIALL = None
        FSCALL = None
        NDSIALL2 = None
        FSCALL2 = None

        return True





    #For each available date, plots the FSC vs NDSI datasets (one png file per date)
    #dirName (string) : name of the directory containing the datasets (self.path_outputs/dirName)
    #source (string) : name of the FSC dataset source (PLEIADES, SPOT, IZAS,etc...)
    #return a success bool
    def PlotEachDates(self,dirName,source):

        print("Start plotting each date")
        dataSetDir = os.path.join(self.path_outputs,dirName)
        path_tifs = os.path.join(dataSetDir,"TIFS")
        path_plots = os.path.join(dataSetDir,"PLOTS")


        for d in sorted(os.listdir(path_tifs)):
            date = self.getDateFromStr(d)
            if date == '' : continue
            print(date)
            path_tifs_date = os.path.join(path_tifs,d)
            path_plots_date = os.path.join(path_plots,d)
            self.mkdir_p(path_plots_date)
            FSC = []
            NDSI = []

            epsgs = {}
            for tif in os.listdir(path_tifs_date) :
                epsg = self.getEpsgFromStr(tif)
                if epsg == '': continue
                if epsg not in epsgs :
                    epsgs[epsg] = []

            tiles = []
            for tif in os.listdir(path_tifs_date) :
                epsg = self.getEpsgFromStr(tif)
                tile = self.getTileFromStr(tif)
                if epsg == '' or tile == '': continue
                if tile not in epsgs[epsg]:
                    epsgs[epsg].append(tile)



            for epsg in epsgs :
                for tile in epsgs[epsg]:
                    g_FSC = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                    FSC.append(BandReadAsArray(g_FSC.GetRasterBand(1)).flatten())
                    g_NDSI = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                    NDSI.append(BandReadAsArray(g_NDSI.GetRasterBand(1)).flatten())





            print("Eliminate Nodata pixels")
            NDSI = np.hstack(NDSI)
            FSC = np.hstack(FSC)
            cond1 = np.where((FSC != 9999) & (~np.isnan(FSC)) & (~np.isinf(FSC)))
            NDSI = NDSI[cond1]
            FSC = FSC[cond1]

            cond2 = np.where( (NDSI != 9999) & (~np.isnan(NDSI)) & (~np.isinf(NDSI)))
            FSC = FSC[cond2]
            NDSI = NDSI[cond2]

            cond3 = np.where((FSC != 0) & (FSC != 1))
            NDSI2 = NDSI[cond3]
            FSC2 = FSC[cond3]
            if len(FSC2) < 2 :
                print("Not enough available pixels")
                continue


            f = open(os.path.join(path_plots_date,"INFO.txt"),"w")
            f.write("\nDate : " + d)
            f.write("\nProjections of FSC inputs : ")
            for epsg in epsgs :  f.write("\n                   " + epsg)




            minNDSI = min(NDSI)
            list_FSC_box = [FSC[np.where((NDSI >= 0.8) & (NDSI <= 1))]]
            list_labels_box = ["[ 0.8\n1 ]"]
            b = 0.8
            while minNDSI < b :
                a = b - 0.2
                list_FSC_box.insert(0,FSC[np.where((NDSI >= a) & (NDSI < b))])
                list_labels_box.insert(0,"[ "+ "{0:.1f}".format(a) +"\n"+ "{0:.1f}".format(b) +" [")
                b = b - 0.2


            minNDSI2 = min(NDSI2)
            list_FSC_box2 = [FSC2[np.where((NDSI2 >= 0.8) & (NDSI2 <= 1))]]
            list_labels_box2 = ["[ 0.8\n1 ]"]
            b = 0.8
            while minNDSI2 < b :
                a = b - 0.2
                list_FSC_box2.insert(0,FSC2[np.where((NDSI2 >= a) & (NDSI2 < b))])
                list_labels_box2.insert(0,"[ "+ "{0:.1f}".format(a) +"\n"+ "{0:.1f}".format(b) +" [")
                b = b - 0.2




            # Plot figure with subplots
            fig = plt.figure()
            st = fig.suptitle(source + " : FSC / NDSI FOR " + date.strftime("%Y/%m/%d"))
            gridspec.GridSpec(2,3)

            # 2D histo avec FSC = 0 et FSC = 1
            ax = plt.subplot2grid((2,3), (0,2))
            slopeA, interceptA, r_valueA, p_valueA, std_errA = mstats.linregress(NDSI,FSC)
            slopeB, interceptB, r_valueB, p_valueB, std_errB = mstats.linregress(FSC,NDSI)

            plt.ylabel('0 <= FSC <= 1')
            plt.xlabel('NDSI')
            plt.hist2d(NDSI,FSC,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'), norm=LogNorm())
            n = np.array([minNDSI,1.0])
            lineA = slopeA*n+interceptA
            lineB = (n-interceptB)/slopeB
            plt.plot(n, lineA, 'g', label='MA: a={:.2f} b={:.2f}\ncorr={:.2f} std_err={:.3f}'.format(slopeA,interceptA,r_valueA,std_errA))
            plt.plot(n, lineB, 'r', label='MB: a={:.2f} b={:.2f}\ncorr={:.2f} std_err={:.3f}'.format(1/slopeB,-interceptB/slopeB,r_valueB,std_errB))
            plt.legend(fontsize=6,loc='upper left')
            plt.colorbar()
            ratio = 1
            xleft, xright = ax.get_xlim()
            ybottom, ytop = ax.get_ylim()
            ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)

            # 2D histo sans FSC = 0 et FSC = 1
            ax = plt.subplot2grid((2,3), (1,2))
            slopeA2, interceptA2, r_valueA2, p_valueA2, std_errA2 = mstats.linregress(NDSI2,FSC2)
            slopeB2, interceptB2, r_valueB2, p_valueB2, std_errB2 = mstats.linregress(FSC2,NDSI2)

            plt.ylabel('0 < FSC < 1')
            plt.xlabel('NDSI')
            plt.hist2d(NDSI2,FSC2,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'),norm=LogNorm())
            n = np.array([minNDSI2,1.0])
            lineA = slopeA2*n+interceptA2
            lineB = (n-interceptB2)/slopeB2
            plt.plot(n, lineA, 'g', label='MA: a={:.2f} b={:.2f}\ncorr={:.2f} std_err={:.3f}'.format(slopeA2,interceptA2,r_valueA2,std_errA2))
            plt.plot(n, lineB, 'r', label='MB: a={:.2f} b={:.2f}\ncorr={:.2f} std_err={:.3f}'.format(1/slopeB2,-interceptB2/slopeB2,r_valueB2,std_errB2))


            plt.legend(fontsize=6,loc='upper left')
            plt.colorbar()
            ratio = 1
            xleft, xright = ax.get_xlim()
            ybottom, ytop = ax.get_ylim()
            ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)



            # boxplot avec FSC = 0 et FSC = 1
            ax = plt.subplot2grid((2,3), (0,0),rowspan=1, colspan=2)
            plt.title('ANALYSIS WITH 0 <= FSC <= 1')
            plt.ylabel('0 <= FSC <= 1')
            plt.xlabel('NDSI')
            plt.boxplot(list_FSC_box,labels = list_labels_box)



            # boxplot sans FSC = 0 et FSC = 1
            ax = plt.subplot2grid((2,3), (1,0),rowspan=1, colspan=2)
            plt.title('ANALYSIS WITH 0 < FSC < 1')
            plt.ylabel('0 < FSC < 1')
            plt.xlabel('NDSI')
            plt.boxplot(list_FSC_box2,labels = list_labels_box2)

            # fit subplots & save fig
            fig.tight_layout()

            fig.set_size_inches(w=16,h=10)
            st.set_y(0.95)
            fig.subplots_adjust(top=0.85)
            fig.savefig(os.path.join(path_plots_date,'PLOT_FSC_NDSI_'  + source + '_' + date.strftime(self.date_format) + '.png'))
            plt.close(fig)



            f.write("\nFor  0 <= FSC <= 1 : " )
            f.write("\n  Number of data points : " + str(len(NDSI)))
            if NDSI != [] and FSC != [] :
                f.write("\n lin. reg. FSC on NDSI (MA): FSC = aNDSI + b : a = " + str(slopeA) + " ; b = " + str(interceptA))
                f.write("\n  std. err. (MA): " + str(std_errA))
                f.write("\n lin. reg. NDSI on FSC (MB): FSC = aNDSI + b : a = " + str(1/slopeB) + " ; b = " + str(-interceptB/slopeB))
                f.write("\n  std. err. (MB): " + str(std_errB))
                f.write("\n  corr. coef. : " + str(r_valueA))


            f.write("\nFor  0 < FSC < 1 : " )
            f.write("\n  Number of data points : " + str(len(NDSI2)))
            if NDSI2 != [] and FSC2 != [] :
                f.write("\n lin. reg. FSC on NDSI (MA): FSC = aNDSI + b : a = " + str(slopeA2) + " ; b = " + str(interceptA2))
                f.write("\n  std. err. (MA): " + str(std_errA2))
                f.write("\n lin. reg. NDSI on FSC (MB): FSC = aNDSI + b : a = " + str(1/slopeB2) + " ; b = " + str(-interceptB2/slopeB2))
                f.write("\n  std. err. (MB): " + str(std_errB2))
                f.write("\n  corr. coef. : " + str(r_valueA2))
            f.close()


        print ("\n plotting finished")
        NDSI = None
        FSC = None
        NDSI2 = None
        FSC2 = None

        return True










    #For each available date, create a quicklook of each tif file in the dataset (one png file per date)
    #dirName (string) : name of the directory containing the tifs files (self.path_outputs/dirName)
    #return a success bool
    def createQuickLooks(self,dirName):


        p_cmp = os.path.join(self.path_palettes,"palette_cmp.txt")
        p_fsc = os.path.join(self.path_palettes,"palette_FSC.txt")

        dataSetDir = os.path.join(self.path_outputs,dirName)
        path_tifs = os.path.join(dataSetDir,"TIFS")
        path_qckls = os.path.join(dataSetDir,"QUICKLOOKS")

        nb_dates = 0
        for date in sorted(os.listdir(path_tifs)):
            print(date)
            path_tifs_date = os.path.join(path_tifs,date)
            path_qckls_date = os.path.join(path_qckls,date)
            self.mkdir_p(path_qckls_date)

            #we get a list of tiles for each epsg
            epsgs = {}
            for tif in os.listdir(path_tifs_date) :
                epsg = self.getEpsgFromStr(tif)
                if epsg == '': continue
                if epsg not in epsgs :
                    epsgs[epsg] = []

            tiles = []
            for tif in os.listdir(path_tifs_date) :
                epsg = self.getEpsgFromStr(tif)
                tile = self.getTileFromStr(tif)
                if epsg == '' or tile == '': continue
                if tile not in epsgs[epsg]:
                    epsgs[epsg].append(tile)


            #create input FSC quicklook
            f_FSC_i = os.path.join(path_tifs_date,"INPUT_FSC.tif")
            os.system("gdaldem color-relief " + f_FSC_i + " " + p_fsc + " " + os.path.join(path_qckls_date,"INPUT_FSC.tif"))
            
            gdal.Translate(os.path.join(path_qckls_date,"INPUT_FSC.png"),os.path.join(path_qckls_date,"INPUT_FSC.tif"),format= 'PNG', width=800,outputType = gdal.GDT_Byte)
            os.remove(os.path.join(path_qckls_date,"INPUT_FSC.tif"))
            #for each epsg
            for epsg in epsgs:

                #create resampled FSC quicklook for each projection
                f_FSC_r = os.path.join(path_tifs_date,"RESAMPLED_FSC_EPSG-" + epsg + ".tif")
                os.system("gdaldem color-relief " + f_FSC_r + " " + p_fsc + " " + os.path.join(path_qckls_date,"RESAMPLED_FSC_EPSG-" + epsg + ".tif"))
                
                gdal.Translate(os.path.join(path_qckls_date,"RESAMPLED_FSC_EPSG-" + epsg + ".png"),os.path.join(path_qckls_date,"RESAMPLED_FSC_EPSG-" + epsg + ".tif"),format= 'PNG', width=800,outputType = gdal.GDT_Byte)
                os.remove(os.path.join(path_qckls_date,"RESAMPLED_FSC_EPSG-" + epsg + ".tif"))


                for tile in epsgs[epsg]:

                    #create compo quicklook
                    f_COMPO = os.path.join(path_tifs_date,"INPUT_COMPO_"+tile+"_EPSG-"+epsg+".tif")
                    
                    gdal.Translate(os.path.join(path_qckls_date,"INPUT_COMPO_"+tile+"_EPSG-"+epsg+".png"),f_COMPO,format= 'PNG', width=800,outputType = gdal.GDT_Byte)



                    #create FSC output quiclook
                    f_FSC = os.path.join(path_tifs_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".tif")
                    os.system("gdaldem color-relief " + f_FSC + " " + p_fsc + " " + os.path.join(path_qckls_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                    
                    gdal.Translate(os.path.join(path_qckls_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".png"),os.path.join(path_qckls_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".tif"),format= 'PNG', width=800,outputType = gdal.GDT_Byte)
                    os.remove(os.path.join(path_qckls_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".tif"))

                    #create NDSI output quiclook
                    f_NDSI = os.path.join(path_tifs_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".tif")
                    os.system("gdaldem color-relief " + f_NDSI + " " + p_fsc + " " + os.path.join(path_qckls_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                    
                    gdal.Translate(os.path.join(path_qckls_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".png"),os.path.join(path_qckls_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".tif"),format= 'PNG', width=800,outputType = gdal.GDT_Byte)
                    os.remove(os.path.join(path_qckls_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".tif"))



                    #create snow difference quicklook


                    g_FSC = gdal.Open(f_FSC_r)
                    g_SEB = gdal.Open(os.path.join(path_tifs_date,"INPUT_SEB_"+tile+"_EPSG-"+epsg+".tif"))

                    minx, maxy, maxx, miny = self.getOverlapCoords(g_FSC,g_SEB)
                    
                    g_FSC = gdal.Translate('',g_FSC,format= 'MEM',projWin = [minx, maxy, maxx, miny])
                    g_SEB = gdal.Translate('',g_SEB,format= 'MEM',projWin = [minx, maxy, maxx, miny],outputType = gdal.GDT_Float32)
                    g_CMP = g_FSC
                    #valeurs dans FSC : [0-1] pour la neige (et non-neige) , 9999 pour noData
                    #valeurs dans SEB : 100 pour la neige, 0 pour non-neige, 205 pour nuage, 254 pour nodata

                    SEB = BandReadAsArray(g_SEB.GetRasterBand(1))
                    cond = np.where((SEB != 100) & (SEB != 0))
                    SEB[cond] = np.nan
                    cond = np.where(SEB == 100)
                    SEB[cond] = 1



                    #valeurs dans FSC : [0-1] pour la neige (et non-neige) , 9999 pour noData
                    #valeurs dans SEB : 1 pour la neige, 0 pour non neige, nan pour noData


                    FSC = BandReadAsArray(g_CMP.GetRasterBand(1))

                    cond = np.where((FSC > 0) & (FSC <= 1))
                    FSC[cond] = 2
                    FSC[FSC == 9999] = np.nan

                    #valeurs dans FSC : 2 pour la neige, 0 pour non neige, nan pour nodata
                    #valeurs dans SEB : 1 pour la neige, 0 pour non neige, nan pour noData

                    CMP = (SEB + FSC)


                    g_CMP.GetRasterBand(1).WriteArray(CMP)
                    
                    gdal.Translate(os.path.join(path_tifs_date,"SNOW_DIFF_tile-" + tile + "_EPSG-" + epsg + ".tif"),g_CMP,format= 'GTiff',noData = 9999)
                    os.system("gdaldem color-relief " + os.path.join(path_tifs_date,"SNOW_DIFF_tile-" + tile + "_EPSG-" + epsg + ".tif") + " " + p_cmp + " " + os.path.join(path_qckls_date,"SNOW_DIFF_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                    
                    gdal.Translate(os.path.join(path_qckls_date,"SNOW_DIFF_tile-" + tile + "_EPSG-" + epsg + ".png"),os.path.join(path_qckls_date,"SNOW_DIFF_tile-" + tile + "_EPSG-" + epsg + ".tif"),format= 'PNG', width=800,outputType = gdal.GDT_Byte)
                    os.remove(os.path.join(path_qckls_date,"SNOW_DIFF_tile-" + tile + "_EPSG-" + epsg + ".tif"))

        return True

    #calDirName (string) : name of the directory containing the datasets used for the calibration (self.path_outputs/dirName)
    #calSource (string) : name of the FSC dataset source (PLEIADES, SPOT, IZAS,etc...) used for the calibration
    #evalDirName (string) : name of the directory containing the datasets used for the evaluation (self.path_outputs/dirName)
    #evalSource (string) : name of the FSC dataset source (PLEIADES, SPOT, IZAS,etc...) used for the evaluation
    #a,b (float) : paramaters of the FSC = 0.5atanh(aNDSI+b)+0.5 model
    #return rmse of the evaluation
    def timeLapseEvalModel(self,calDirName,evalDirNames,calSource,evalSources,a,b):


        calDataSetDir = os.path.join(self.path_outputs,calDirName)
        path_eval = os.path.join(calDataSetDir,"EVALUATION")
        title = "TIMELAPSE_" + calSource + "_WITH"





        title2 = "TIMELAPSE"
        for evalDirName in evalDirNames :
            title2 = title2 + "_" + evalDirName

        for evalSource in evalSources :
            title = title + "_" + evalSource

        path_eval_dir = os.path.join(path_eval,title2)
        shutil.rmtree(path_eval_dir, ignore_errors=True)

        self.mkdir_p(path_eval_dir)

        f= open(os.path.join(path_eval_dir,title + ".txt"),"w")
        f.write("\nCalibration dataset :" + calDirName)
        f.write("\nModel : FSC = 0.5*tanh(a*NDSI+b) +  0.5 with :")
        f.write("\n        a = " + str(a) + " b = " + str(b))


        f.write("\n")

        f.write("\nEVALUATION" )

        # Plot figure with subplots
        fig = plt.figure()
        st = fig.suptitle(title)
        # set up subplot grid
        gridspec.GridSpec(1,2)
        # prepare for evaluation scatterplot
        ax = plt.subplot2grid((1,2), (0,0),rowspan=1, colspan=2)

        plt.ylabel('FSC predicted - evaluation',size = 10)
        plt.xlabel('date',size = 10)



        k = 0
        for evalDirName in evalDirNames :
            evalSource = evalSources[k]
            k = k + 1

            nb_pixel_total = 0

            evalDataSetDir = os.path.join(self.path_outputs,evalDirName)
            path_tifs = os.path.join(evalDataSetDir,"TIFS")

            NDSI_avg_test = []
            FSC_avg_test = []
            days = []

            for d in sorted(os.listdir(path_tifs)):
                date = self.getDateFromStr(d)
                if date == '' : continue
                print(date)
                path_tifs_date = os.path.join(path_tifs,d)


                epsgs = {}
                for tif in os.listdir(path_tifs_date) :
                    epsg = self.getEpsgFromStr(tif)
                    if epsg == '': continue
                    if epsg not in epsgs :
                        epsgs[epsg] = []

                tiles = []
                for tif in os.listdir(path_tifs_date) :
                    epsg = self.getEpsgFromStr(tif)
                    tile = self.getTileFromStr(tif)
                    if epsg == '' or tile == '': continue
                    if tile not in epsgs[epsg]:
                        epsgs[epsg].append(tile)

                FSC_d = []
                NDSI_d = []

                for epsg in epsgs :
                    for tile in epsgs[epsg]:
                        g_FSC = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_FSC_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                        FSC_d.append(BandReadAsArray(g_FSC.GetRasterBand(1)).flatten())
                        g_NDSI = gdal.Open(os.path.join(path_tifs_date,"OUTPUT_NDSI_tile-" + tile + "_EPSG-" + epsg + ".tif"))
                        NDSI_d.append(BandReadAsArray(g_NDSI.GetRasterBand(1)).flatten())




                NDSI_d = np.hstack(NDSI_d)
                FSC_d = np.hstack(FSC_d)
                cond1 = np.where((FSC_d != 9999) & (~np.isnan(FSC_d)) & (~np.isinf(FSC_d)))
                NDSI_d = NDSI_d[cond1]
                FSC_d = FSC_d[cond1]
                cond2 = np.where( (NDSI_d != 9999) & (~np.isnan(NDSI_d)) & (~np.isinf(NDSI_d)))
                FSC_d = FSC_d[cond2]
                NDSI_d = NDSI_d[cond2]
                if len(FSC_d) == 0 : continue

                nb_pixel_total = nb_pixel_total + len(FSC_d)

                FSC_avg = np.average(FSC_d)
                NDSI_avg = np.average(NDSI_d)


                NDSI_avg_test.append(NDSI_avg)
                FSC_avg_test.append(FSC_avg)
                days.append(date)

            NDSI_avg_test = np.hstack(NDSI_avg_test)
            FSC_avg_test = np.hstack(FSC_avg_test)
            days = np.hstack(days)





            # VALIDATION

            # prediction of FSC from testing NDSI
            FSC_avg_pred = 0.5*np.tanh(a*NDSI_avg_test+b) +  0.5

            # error
            er_FSC = FSC_avg_pred - FSC_avg_test

            # absolute error
            abs_er_FSC = abs(er_FSC)

            # mean error
            m_er_FSC = np.mean(er_FSC)

            # absolute mean error
            abs_m_er_FSC = np.mean(abs_er_FSC)

            #root mean square error
            rmse_FSC = sqrt(mean_squared_error(FSC_avg_pred,FSC_avg_test))

            #correlation
            corr_FSC = mstats.pearsonr(FSC_avg_pred,FSC_avg_test)[0]

            #standard deviation
            stde_FSC = np.std(er_FSC)


            plt.scatter(days,er_FSC, label='{:s}; rmse : {:.2f}'.format(evalSource,rmse_FSC))
            plt.legend(fontsize=10,loc='upper left')




            f.write("\n")
            f.write("\nEvaluation dataSet :" + evalDirName)
            f.write("\n  Number of datess : " + str(len(NDSI_avg_test)))
            f.write("\n  Total number of 20x20m pixels : " + str(nb_pixel_total))
            f.write("\n  Number of 20x20m pixels per date : " + str(nb_pixel_total/len(NDSI_avg_test)))
            f.write("\n  Covered surface per date (m2) : " + str(20*20*nb_pixel_total/len(NDSI_avg_test)))
            f.write("\n  corr. coef. : " + str(corr_FSC))
            f.write("\n  std. err. (MB): " + str(stde_FSC))
            f.write("\n  mean err. : " + str(m_er_FSC))
            f.write("\n  abs. mean err. : " + str(abs_m_er_FSC))
            f.write("\n  root mean square err. : " + str(rmse_FSC))





        # fit subplots & save fig
        fig.tight_layout()
        fig.set_size_inches(w=16,h=10)
        st.set_y(0.95)
        fig.subplots_adjust(top=0.85)
        fig.savefig(os.path.join(path_eval_dir,'PLOT_' + title + '.png'))
        plt.close(fig)

        #close txt file
        f.close()


        return True







    #Filter the input ODK points and match them with a LIS product
    #dirName : directory which will contain the new list of ODK points
    #source : text file containing the input ODK points
    #accFilter (bool) : indicate if we eliminate ODK points above a certain accuracy
    #snwFilter (bool) : indicate if we eliminate ODK points outside the LIS snow mask
    def processODK(self,dirName,source,accFilter,snwFilter):



        dataSetDir = os.path.join(self.path_outputs,dirName)
        odkList = os.path.join(dataSetDir,"ODKLIST.txt")
        odkInfos = os.path.join(dataSetDir,"ODKINFOS.txt")


        dirODK = "/work/OT/siaa/Theia/Neige/CoSIMS/zacharie/snowcover/INPUTS/FSC/ODK"
        inputODK = os.path.join(dirODK,source)

        if "ODK" not in  dataSetDir:
            print("ERROR processODK : 'ODK' needs to be in the name")
            return False
        shutil.rmtree(dataSetDir, ignore_errors=True)

        self.mkdir_p(dataSetDir)


        dict_tile = {}
        dict_products = {}
        dict_FSC = {}


        print("####################################################")
        print("Recuperation of ODK data")
        #on recupere les donnees odk
        with open(inputODK, "r") as ODK :
            line = ODK.readline()
            line = ODK.readline()
            while line :
                point = line.split()
                date = point[0]
                latitude = point[1]
                longitude = point[2]
                accuracy = point[3]
                fsc = point[4]
                if accFilter == True and float(accuracy) > self.max_accuracy  :
                    line = ODK.readline()
                    continue

                if date not in dict_FSC.keys() :
                    dict_FSC[date] = []
                    dict_FSC[date].append([latitude,longitude,fsc,accuracy])
                else :
                    dict_FSC[date].append([latitude,longitude,fsc,accuracy])

                line = ODK.readline()



        print("####################################################")
        print("Search of tiles and L2A rasters")
        #on trouve les tuiles et rasters correspondants
        for date in dict_FSC :
            print("check date: ",date)
            list_points = dict_FSC[date]
            dateFSC = self.getDateFromStr(date)


            for point in list_points :

                lat = point[0]
                lon = point[1]
                fsc = point[2]
                acc = point[3]
                print(" check point : ",lat,lon)



                decalP = self.nb_shift_days + 1
                tileP = ""
                p_L2AP = ""
                for tile in os.listdir(self.path_LIS) :


                    path_tile = os.path.join(self.path_LIS,tile)
                    if not os.path.isdir(path_tile): continue
                    try:
                        L2A_product = os.listdir(path_tile)[-1]
                    except OSError as exc:  # Python >2.5
                        if exc.errno == errno.EACCES:
                            continue
                        else:
                            raise
                    L2A_product = os.path.join(path_tile,L2A_product)
                    f_L2A = os.path.join(L2A_product,"LIS_PRODUCTS","LIS_SEB.TIF")


                    pixel = os.popen('gdallocationinfo -valonly -wgs84 %s %s %s' % (f_L2A, lon, lat)).read()

                    try:
                        int(pixel)

                    except ValueError:
                        continue

                    L2A_products = glob.glob(os.path.join(path_tile,'*SENTINEL*'))



                    for L2A_product in L2A_products :
                        dateL2A = self.getDateFromStr(L2A_product)
                        decal = dateL2A - dateFSC
                        if abs(decal.days) >= decalP : continue

                        f_L2A = os.path.join(L2A_product,"LIS_PRODUCTS","LIS_SEB.TIF")
                        pixel = int(os.popen('gdallocationinfo -valonly -wgs84 %s %s %s' % (f_L2A, lon, lat)).read())

                        if  snwFilter == True and pixel != 100: continue

                        decalP = abs(decal.days)
                        p_L2AP = L2A_product
                        tileP = tile

                if p_L2AP == "":
                    print("  point rejete")
                    continue
                else :
                    print("  point accepte")

                f_L2AP = os.path.basename(p_L2AP)

                #we check if pixel is in tree region
                forest = int(os.popen('gdallocationinfo -valonly -wgs84 %s %s %s' % (self.f_tree, lon, lat)).read())


                if dateFSC not in dict_products.keys() :
                    dict_products[dateFSC] = []
                    dict_products[dateFSC].append([lat,lon,fsc,acc,decalP,p_L2AP,f_L2AP,tileP,forest])
                else :
                    dict_products[dateFSC].append([lat,lon,fsc,acc,decalP,p_L2AP,f_L2AP,tileP,forest])


        f_odkList= open(odkList,"w")
        f_odkInfos= open(odkInfos,"w")
        #on affiche le dict
        print("####################################################")
        print("\n")
        nb_points = 0
        f_odkList.write("date lat lon fsc acc decal L2A tile forest")
        for date in dict_products :
            print(date)

            for point in dict_products[date] :
                print ("TILE : ",point[7])
                if point[7] not in dict_tile.keys():
                    dict_tile[point[7]] = [1,0]
                else :
                    dict_tile[point[7]][0] = dict_tile[point[7]][0] + 1
                if point[8] > 0 :
                    dict_tile[point[7]][1] = dict_tile[point[7]][1] + 1
                print ("L2A product : ",point[6])
                print("lat = ",point[0],"lon = ",point[1],"fsc = ",point[2],"acc = ",point[3],"decal = ",point[4],"forest value = ",point[8])
                f_odkList.write("\n"+date.strftime(self.date_format)+" "+str(point[0])+" "+str(point[1])+" "+str(point[2])+" "+str(point[3])+" "+str(point[4])+" "+point[5]+" "+point[7]+" "+str(point[8]))
                nb_points = nb_points + 1
            print("\n")
        print("nb of points = ",nb_points)

        #on affiche le nombre de points par tuile
        for tile in dict_tile :
            line = "TILE : " + tile + " ; NB of points : " + str(dict_tile[tile][0]) + " ; NB of points in forest : " + str(dict_tile[tile][1])
            print(line)
            f_odkInfos.write("\n" + line)

        f_odkInfos.write("\nTOTAL NB OF POINTS : " + str(nb_points))

        f_odkList.close()
        f_odkInfos.close()

        return True






    #With the list of ODK points and their matching LIS products found in evaldirName, evaluate the a and b parameters of the FSC = 0.5atanh(aNDSI+b)+0.5 model
    #calDirName (string) : name of the directory containing the datasets used for the calibration (self.path_outputs/dirName)
    #calSource (string) : name of the FSC dataset source (PLEIADES, SPOT, IZAS,etc...) used for the calibration
    #evalDirName (string) : name of the directory containing the ODK list used for the evaluation (self.path_outputs/dirName)
    #a,b (float) : paramaters of the FSC = 0.5atanh(aNDSI+b)+0.5 model
    #return rmse of the evaluation
    def evaluateWithODK(self,calDirName,calSource,evalDirName,a,b):


        calDataSetDir = os.path.join(self.path_outputs,calDirName)
        path_eval = os.path.join(calDataSetDir,"EVALUATION")
        title = "EVAL_" + calSource + "_WITH_ODK"

        odkPoints = os.path.join(self.path_outputs,evalDirName,"ODKLIST.txt")


        path_eval_dir = os.path.join(path_eval,title)
        shutil.rmtree(path_eval_dir, ignore_errors=True)

        self.mkdir_p(path_eval_dir)

        f= open(os.path.join(path_eval_dir,title + ".txt"),"w")
        f.write("\nCalibration dataset :" + calDirName + " from " + calSource)
        f.write("\nModel : FSC = 0.5*tanh(a*NDSI+b) +  0.5 :")
        f.write("\n        a = " + str(a) + " b = " + str(b))
        f.write("\nEvaluation dataSets : \n" + evalDirName )





        dict_FSC = {}
        dict_products = {}



        print("####################################################")
        print("Recuperation of ODK data")
        #on recupere les donnees odk
        with open(odkPoints, "r") as ODK :
            line = ODK.readline()
            line = ODK.readline()
            while line :
                point = line.split()
                date = point[0]
                latitude = point[1]
                longitude = point[2]
                fsc = float(point[3])
                L2A_product = point[6]
                tcd = float(point[8])



                if date not in dict_products.keys() :
                    dict_products[date] = []

                dict_products[date].append([latitude,longitude,fsc,tcd,L2A_product])

                line = ODK.readline()





        #on compare ODK et L2A
        list_NDSI = []
        list_FSC = []
        list_TCD = []
        for date in dict_products :
            for point in dict_products[date] :

                lat = point[0]
                lon = point[1]
                fsc = point[2]
                tcd = point[3]
                L2A_product = point[4]


                # We look for the red, green and swir bands tiff files + mask
                f_green = ""
                f_swir = ""
                f_red = ""
                f_mask = ""


                for fp in os.listdir(L2A_product) :
                    if ("green_band_resampled.tif" in fp) :
                        f_green = os.path.join(L2A_product,fp)
                    elif ("red_band_resampled.tif" in fp) :
                        f_red = os.path.join(L2A_product,fp)
                    elif ("swir_band_extracted.tif" in fp) :
                        f_swir = os.path.join(L2A_product,fp)



                #If there is a file missing, we skip to the next point
                if f_green == "" or f_red == "" or f_swir == "" : continue


                #We get the corresponding pixel from each band to calculate a NDSI pixel
                green = 0
                red = 0
                swir = 0
                NDSI = 0



                try:

                    green = float(os.popen('gdallocationinfo -valonly -wgs84 %s %s %s' % (f_green, lon, lat)).read())
                    red = float(os.popen('gdallocationinfo -valonly -wgs84 %s %s %s' % (f_red, lon, lat)).read())
                    swir = float(os.popen('gdallocationinfo -valonly -wgs84 %s %s %s' % (f_swir, lon, lat)).read())

                except ValueError:
                    continue





                NDSI = (green - swir)/(green + swir)



                if np.isnan(NDSI) or np.isinf(NDSI) : continue

                list_NDSI.append(NDSI)
                list_FSC.append(fsc)
                list_TCD.append(tcd)



        #on affiche les lists
        print("####################################################")
        print("\nODK POINTS:")

        for i in arange(len(list_NDSI)) :
            print("NDSI = ",list_NDSI[i],"FSC = ",list_FSC[i],"TCD = ",list_TCD[i])

        print("####################################################")
        print("Calculation of NDSI-FSC relation and model evaluation")

        #on calcul et affiche la relation FSC-NDSI et l evaluation des parametres a et b

        NDSI_test = np.asarray(list_NDSI)
        FSC_test = np.asarray(list_FSC)
        TCD = np.asarray(list_TCD)


        TOC_FSC_pred = 0.5*np.tanh(a*NDSI_test+b) +  0.5
        OG_FSC_pred = TOC_FSC_pred/((100.0 - TCD)/100.0)
        OG_FSC_pred[OG_FSC_pred > 1] = 1
        OG_FSC_pred[np.isinf(OG_FSC_pred)] = 1
        TDC_t = TCD[TCD > 0]
        FSC_test_t = FSC_test[TCD > 0]
        OG_FSC_pred_t = OG_FSC_pred[TCD > 0]





        #TOC
        # error
        TOC_er_FSC = TOC_FSC_pred - FSC_test
        # absolute error
        TOC_abs_er_FSC = abs(TOC_er_FSC)
        # mean error
        TOC_m_er_FSC = np.mean(TOC_er_FSC)
        # absolute mean error
        TOC_abs_m_er_FSC = np.mean(TOC_abs_er_FSC)
        #root mean square error
        TOC_rmse_FSC = sqrt(mean_squared_error(TOC_FSC_pred,FSC_test))
        #correlation
        TOC_corr_FSC = mstats.pearsonr(TOC_FSC_pred,FSC_test)[0]
        #standard deviation
        TOC_stde_FSC = np.std(TOC_er_FSC)

        #OG
        # error
        OG_er_FSC = OG_FSC_pred - FSC_test
        # absolute error
        OG_abs_er_FSC = abs(OG_er_FSC)
        # mean error
        OG_m_er_FSC = np.mean(OG_er_FSC)
        # absolute mean error
        OG_abs_m_er_FSC = np.mean(OG_abs_er_FSC)
        #root mean square error
        OG_rmse_FSC = sqrt(mean_squared_error(OG_FSC_pred,FSC_test))
        #correlation
        OG_corr_FSC = mstats.pearsonr(OG_FSC_pred,FSC_test)[0]
        #standard deviation
        OG_stde_FSC = np.std(OG_er_FSC)



        #OG Tree Only
        # error
        OG_er_FSC_t = OG_FSC_pred_t - FSC_test_t
        # absolute error
        OG_abs_er_FSC_t = abs(OG_er_FSC_t)
        # mean error
        OG_m_er_FSC_t = np.mean(OG_er_FSC_t)
        # absolute mean error
        OG_abs_m_er_FSC_t = np.mean(OG_abs_er_FSC_t)
        #root mean square error
        OG_rmse_FSC_t = sqrt(mean_squared_error(OG_FSC_pred_t,FSC_test_t))
        #correlation
        OG_corr_FSC_t = mstats.pearsonr(OG_FSC_pred_t,FSC_test_t)[0]
        #standard deviation
        OG_stde_FSC_t = np.std(OG_er_FSC_t)





        minNDSI = min(NDSI_test)
        list_FSC_box = [FSC_test[np.where((NDSI_test >= 0.8) & (NDSI_test <= 1))]]
        list_labels_box = ["[ 0.8\n1 ]"]
        j = 0.8
        while minNDSI < j :
            i = j - 0.2
            list_FSC_box.insert(0,FSC_test[np.where((NDSI_test >= i) & (NDSI_test < j))])
            list_labels_box.insert(0,"[ "+ "{0:.1f}".format(i) +"\n"+ "{0:.1f}".format(j) +" [")
            j = j - 0.2

        # Plot figure with subplots
        fig = plt.figure()
        st = fig.suptitle("ODK FSC / NDSI")
        gridspec.GridSpec(1,3)

        # 2D histo pour FSC vs NDSI

        ax = plt.subplot2grid((1,3), (0,2))
        plt.title('ODK FSC/NDSI')
        plt.ylabel('testing FSC')
        plt.xlabel('testing NDSI')
        plt.hist2d(NDSI_test,FSC_test,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'),norm=LogNorm())
        n = np.arange(min(NDSI_test),1.01,0.01)
        line = 0.5*np.tanh(a*n+b) +  0.5
        plt.plot(n, line, 'r', label='Predicted TOC FSC')
        plt.legend(fontsize=6,loc='upper left')
        plt.colorbar()
        ratio = 1
        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)

        # boxplot avec FSC = 0 et FSC = 1
        ax = plt.subplot2grid((1,3), (0,0),rowspan=1, colspan=2)
        plt.title('ODK FSC/NDSI')
        plt.ylabel('0 <= FSC <= 1')
        plt.xlabel('NDSI')
        plt.boxplot(list_FSC_box,labels = list_labels_box)


        # fit subplots and save fig
        fig.tight_layout()
        fig.set_size_inches(w=16,h=10)
        st.set_y(0.95)
        fig.subplots_adjust(top=0.85)
        fig.savefig(os.path.join('ODK_ANALYSIS.png'))
        plt.close(fig)


        # Plot figure with subplots
        fig = plt.figure()
        st = fig.suptitle("ODK EVALUATION")
        gridspec.GridSpec(2,3)

        # 2D histo pour TOC evaluation
        ax = plt.subplot2grid((2,3), (0,2))

        plt.title('TOC FSC EVALUATION')
        plt.ylabel('predicted TOC FSC')
        plt.xlabel('testing FSC')
        plt.hist2d(FSC_test,TOC_FSC_pred,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'),norm=LogNorm())
        slope, intercept, r_value, p_value, std_err = mstats.linregress(FSC_test,TOC_FSC_pred)
        n = np.array([min(FSC_test),1.0])
        line = slope * n + intercept
        plt.plot(n, line, 'b', label='y = {:.2f}x + {:.2f}\ncorr={:.2f} rmse={:.2f}'.format(slope,intercept,TOC_corr_FSC,TOC_rmse_FSC))
        plt.plot(n, n, 'g', label='y = 1.0x + 0.0')
        plt.legend(fontsize=6,loc='upper left')
        plt.colorbar()
        ratio = 1
        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)


        # 1D histo de TOC residus
        ax = plt.subplot2grid((2,3), (0,0),rowspan=1, colspan=2)
        plt.title("TOC FSC RESIDUALS")
        plt.ylabel('amount of data points')
        plt.xlabel('FSC pred - test')
        xticks = np.arange(-1.0, 1.1, 0.1)
        plt.xticks(xticks)
        plt.hist(TOC_er_FSC,bins=40,weights=np.ones(len(TOC_er_FSC)) / len(TOC_er_FSC))
        plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
        plt.grid(True)


        # 2D histo pour OG evaluation
        ax = plt.subplot2grid((2,3), (1,2))

        plt.title('OG FSC EVALUATION')
        plt.ylabel('predicted OG FSC')
        plt.xlabel('testing FSC')
        plt.hist2d(FSC_test,OG_FSC_pred,bins=(40, 40), cmap=plt.cm.get_cmap('plasma'),norm=LogNorm())
        slope, intercept, r_value, p_value, std_err = mstats.linregress(FSC_test,OG_FSC_pred)
        n = np.array([min(FSC_test),1.0])
        line = slope * n + intercept
        plt.plot(n, line, 'b', label='y = {:.2f}x + {:.2f}\ncorr={:.2f} rmse={:.2f}'.format(slope,intercept,OG_corr_FSC,OG_rmse_FSC))
        plt.plot(n, n, 'g', label='y = 1.0x + 0.0')
        plt.legend(fontsize=6,loc='upper left')
        plt.colorbar()
        ratio = 1
        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)


        # 1D histo de OG residus
        ax = plt.subplot2grid((2,3), (1,0),rowspan=1, colspan=2)
        plt.title("OG FSC RESIDUALS")
        plt.ylabel('amount of data points')
        plt.xlabel('FSC pred - test')
        xticks = np.arange(-1.0, 1.1, 0.1)
        plt.xticks(xticks)
        plt.hist(OG_er_FSC,bins=40,weights=np.ones(len(OG_er_FSC)) / len(OG_er_FSC))
        plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
        plt.grid(True)



        # fit subplots and save fig
        fig.tight_layout()
        fig.set_size_inches(w=16,h=10)
        st.set_y(0.95)
        fig.subplots_adjust(top=0.85)
        fig.savefig(os.path.join(path_eval_dir,title + '.png'))
        plt.close(fig)



        f.write("\n")
        f.write("\nEVALUATION OF TOC FSC" )
        f.write("\n  Number of data points : " + str(len(FSC_test)))
        f.write("\n  corr. coef. : " + str(TOC_corr_FSC))
        f.write("\n  std. err. : " + str(TOC_stde_FSC))
        f.write("\n  mean err. : " + str(TOC_m_er_FSC))
        f.write("\n  abs. mean err. : " + str(TOC_abs_m_er_FSC))
        f.write("\n  root mean square err. : " + str(TOC_rmse_FSC))
        f.write("\n")
        f.write("\nEVALUATION OF OG FSC" )
        f.write("\n  Number of data points : " + str(len(FSC_test)))
        f.write("\n  corr. coef. : " + str(OG_corr_FSC))
        f.write("\n  std. err. : " + str(OG_stde_FSC))
        f.write("\n  mean err. : " + str(OG_m_er_FSC))
        f.write("\n  abs. mean err. : " + str(OG_abs_m_er_FSC))
        f.write("\n  root mean square err. : " + str(OG_rmse_FSC))
        f.write("\n")
        f.write("\nEVALUATION OF OG FSC with only pixels with TCD > 0" )
        f.write("\n  Number of data points : " + str(len(FSC_test_t)))
        f.write("\n  corr. coef. : " + str(OG_corr_FSC_t))
        f.write("\n  std. err. : " + str(OG_stde_FSC_t))
        f.write("\n  mean err. : " + str(OG_m_er_FSC_t))
        f.write("\n  abs. mean err. : " + str(OG_abs_m_er_FSC_t))
        f.write("\n  root mean square err. : " + str(OG_rmse_FSC_t))

        f.close()


        return TOC_rmse_FSC
