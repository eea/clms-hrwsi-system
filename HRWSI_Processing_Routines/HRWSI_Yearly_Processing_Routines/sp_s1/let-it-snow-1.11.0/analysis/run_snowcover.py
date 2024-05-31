import sys
import os
import errno
import re

import snowcover


#initialize
SNW = snowcover.snowcover()  



#CALIBRATION PLEIADES

nameCAL = "PLEIADES_CAL"
sourceCAL = "PLEIADES"
dateDebut = "2015-01-01"
dateFin = "2020-01-01"
SNWCAL = [1]
NSNWCAL = [2]
OK = SNW.makeDataSet(dateDebut=dateDebut,dateFin=dateFin,source=sourceCAL,dirName=nameCAL,SNWval=SNWCAL,NSNWval=NSNWCAL)
OK = SNW.createQuickLooks(nameCAL)
OK = SNW.PlotPeriode(nameCAL,sourceCAL)
OK = SNW.PlotEachDates(nameCAL,sourceCAL)
a,b,rmse = SNW.calibrateModel(nameCAL,sourceCAL,0.4)
print(nameCAL,"a = ",a,"b = ",b,"rmse = ",rmse)




#EVALUATION IZAS

nameVAL = "IZAS_VAL"
sourceVAL = "IZAS"
SNWVAL = [1]
NSNWVAL = [0]
epsgVAL = "25830"
tileVAL = ["T30TYN"]
OK = SNW.makeDataSet(dateDebut=dateDebut,dateFin=dateFin,source=sourceVAL,dirName=nameVAL,SNWval=SNWVAL,NSNWval=NSNWVAL,epsgFSC = epsgVAL,tiles = tileVAL)
OK = SNW.createQuickLooks(nameVAL)
OK = SNW.PlotPeriode(nameVAL,sourceVAL)
rmse = SNW.evaluateModel(nameCAL,[nameVAL],sourceCAL,[sourceVAL],a,b)
print(nameVAL,"rmse = ",rmse)



#EVALUATION SPOT

nameVAL = "SPOT67_20160808_VAL"
sourceVAL = "SPOT67"
SNWVAL = [2]
NSNWVAL = [1]
NDVAL = [0]
epsgVAL = ""
tileVAL = ["T32TLS","T32TLR","T32TLQ","T31TGK","T31TGL","T31TGM"]
OK = SNW.makeDataSet(dateDebut="2016-08-08",source=sourceVAL,dirName=nameVAL,SNWval=SNWVAL,NSNWval=NSNWVAL,NDval=NDVAL,epsgFSC = epsgVAL,tiles = tileVAL,selection = "closest")
OK = SNW.createQuickLooks(nameVAL)
OK = SNW.PlotPeriode(nameVAL,sourceVAL)
rmse = SNW.evaluateModel(nameCAL,[nameVAL],sourceCAL,[sourceVAL],a,b)
print(nameVAL,"rmse = ",rmse)

nameVAL = "SPOT67_20170311_VAL"
sourceVAL = "SPOT67"
SNWVAL = [2]
NSNWVAL = [1]
NDVAL = [0]
epsgVAL = ""
tileVAL = ["T32TLS","T32TLR","T32TLQ","T31TGK","T31TGL","T31TGM"]
OK = SNW.makeDataSet(dateDebut="2017-03-11",source=sourceVAL,dirName=nameVAL,SNWval=SNWVAL,NSNWval=NSNWVAL,NDval=NDVAL,epsgFSC = epsgVAL,tiles = tileVAL,selection = "closest")
OK = SNW.createQuickLooks(nameVAL)
OK = SNW.PlotPeriode(nameVAL,sourceVAL)
rmse = SNW.evaluateModel(nameCAL,[nameVAL],sourceCAL,[sourceVAL],a,b)
print(nameVAL,"rmse = ",rmse)

nameVAL = "SPOT67_20161012_VAL"
sourceVAL = "SPOT67"
SNWVAL = [2]
NSNWVAL = [1]
NDVAL = [0]
epsgVAL = ""
tileVAL = ["T32TLS","T32TLR","T32TLQ","T31TGK","T31TGL","T31TGM"]
OK = SNW.makeDataSet(dateDebut="2016-10-12",source=sourceVAL,dirName=nameVAL,SNWval=SNWVAL,NSNWval=NSNWVAL,NDval=NDVAL,epsgFSC = epsgVAL,tiles = tileVAL,selection = "closest")
OK = SNW.createQuickLooks(nameVAL)
OK = SNW.PlotPeriode(nameVAL,sourceVAL)
rmse = SNW.evaluateModel(nameCAL,[nameVAL],sourceCAL,[sourceVAL],a,b)
print(nameVAL,"rmse = ",rmse)


nameVAL = "SPOT67_20161203_VAL"
sourceVAL = "SPOT67"
SNWVAL = [2]
NSNWVAL = [1]
NDVAL = [0]
epsgVAL = ""
tileVAL = ["T32TLS","T32TLR","T32TLQ","T31TGK","T31TGL","T31TGM"]
OK = SNW.makeDataSet(dateDebut="2016-12-03",source=sourceVAL,dirName=nameVAL,SNWval=SNWVAL,NSNWval=NSNWVAL,NDval=NDVAL,epsgFSC = epsgVAL,tiles = tileVAL,selection = "cleanest")
OK = SNW.createQuickLooks(nameVAL)
OK = SNW.PlotPeriode(nameVAL,sourceVAL)
rmse = SNW.evaluateModel(nameCAL,[nameVAL],sourceCAL,[sourceVAL],a,b)
print(nameVAL,"rmse = ",rmse)

nameVAL = "SPOT67_20161217_VAL"
sourceVAL = "SPOT67"
SNWVAL = [2]
NSNWVAL = [1]
NDVAL = [0]
epsgVAL = ""
tileVAL = ["T32TLS","T32TLR","T32TLQ","T31TGK","T31TGL","T31TGM"]
OK = SNW.makeDataSet(dateDebut="2016-12-17",source=sourceVAL,dirName=nameVAL,SNWval=SNWVAL,NSNWval=NSNWVAL,NDval=NDVAL,epsgFSC = epsgVAL,tiles = tileVAL,selection = "closest")
OK = SNW.createQuickLooks(nameVAL)
OK = SNW.PlotPeriode(nameVAL,sourceVAL)
rmse = SNW.evaluateModel(nameCAL,[nameVAL],sourceCAL,[sourceVAL],a,b)
print(nameVAL,"rmse = ",rmse)


nameVAL = "DISCHMEX_VAL"
sourceVAL = "DISCHMEX"
SNWVAL = [1]
NSNWVAL = [0]
NDVAL = []
epsgVAL = "21781"
tileVAL = []
OK = SNW.makeDataSet(dateDebut=dateDebut,dateFin=dateFin,source=sourceVAL,dirName=nameVAL,SNWval=SNWVAL,NSNWval=NSNWVAL,NDval=NDVAL,epsgFSC = epsgVAL,tiles = tileVAL)
OK = SNW.createQuickLooks(nameVAL)
OK = SNW.PlotPeriode(nameVAL,sourceVAL)
rmse = SNW.evaluateModel(nameCAL,[nameVAL],sourceCAL,[sourceVAL],a,b)
print(nameVAL,"rmse = ",rmse)

nameVAL = "AUSTRIA_VAL"
sourceVAL = "AUSTRIA"
SNWVAL = [1]
NSNWVAL = [0]
NDVAL = []
epsgVAL = "31254"
tileVAL = []
OK = SNW.makeDataSet(dateDebut=dateDebut,dateFin=dateFin,source=sourceVAL,dirName=nameVAL,SNWval=SNWVAL,NSNWval=NSNWVAL,NDval=NDVAL,epsgFSC = epsgVAL,tiles = tileVAL)
OK = SNW.createQuickLooks(nameVAL)
OK = SNW.PlotPeriode(nameVAL,sourceVAL)
rmse = SNW.evaluateModel(nameCAL,[nameVAL],sourceCAL,[sourceVAL],a,b)
print(nameVAL,"rmse = ",rmse)



#ODK
nameVAL = "ODK_VAL"
sourceVAL = "odk_all.txt"
OK = SNW.processODK(nameVAL,sourceVAL,True,True)
rmse = SNW.evaluateWithODK(nameCAL,sourceCAL,nameVAL,a,b)


evalDirNames = []
evalSources = []

#EVALUATION CAMSNOW
nameVAL = "CAMSNOW_VAL"
sourceVAL = "CAMSNOW"
SNWVAL = []
NSNWVAL = []
FSCVAL = True
epsgVAL = "2154"
sampling = "near"

OK = SNW.makeDataSet(dateDebut=dateDebut,dateFin=dateFin,source=sourceVAL,dirName=nameVAL,SNWval=SNWVAL,NSNWval=NSNWVAL,epsgFSC = epsgVAL,isFSC = FSCVAL,resampling = sampling)
OK = SNW.createQuickLooks(nameVAL)
OK = SNW.PlotPeriode(nameVAL,sourceVAL)

evalDirNames = ["CAMSNOW_VAL","IZAS_VAL"]
evalSources = ["CAMSNOW","IZAS"]


OK = SNW.timeLapseEvalModel(nameCAL,evalDirNames,sourceCAL,evalSources,a,b)
print(OK)








