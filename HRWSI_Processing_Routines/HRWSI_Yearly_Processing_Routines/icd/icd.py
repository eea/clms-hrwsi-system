#!/usr/bin/python3

import os, sys, argparse, datetime, xmltodict, yaml, uuid, shutil, json, traceback, subprocess
from time import sleep
import numpy as np
import validate_cloud_optimized_geotiff


def main():
    def deliver(sysargv,parameters,result):
        # Dump some info
        sysargv['parameters'] = parameters
        sysargv['return_code'] = result
        if 'output_dir' in sysargv:
            if not os.path.exists(sysargv['output_dir']):
                os.makedirs(sysargv['output_dir'])
            f = open(os.path.join(sysargv['output_dir'],'output_info.yaml'),'w')
            f.write(yaml.dump(sysargv))
            f.close()
        try:
            icdio.log("Exiting with code ", result)
        except:
            print("Exiting with code ", result)
        return result
    
    baseDir = os.path.split(os.path.realpath(os.sys.argv[0]))[0]

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('parameters_file',help='Path to the configuration parameters file')
    sysargv = vars(parser.parse_args())
    if sysargv['parameters_file'] is None:
        print('21: Parameters file not given. Exiting.')
        return deliver(sysargv,{},21)
    print("Reading parameters from file")
    try:
        pFile = open(sysargv['parameters_file'],'r')
    except Exception as e:
        print('22: Parameters file cannot be read. Exiting.')
        print(e)
        return deliver(sysargv,{},22)
    try:
        parameters = yaml.load(pFile,Loader=yaml.Loader)
    except Exception as e:
        print('22: Parameters file is not a valid file. Exiting.')
        print(e)
        return deliver(sysargv,{},22)
    pFile.close()

    print("Checking parameters")
    required_parameters = ['product_title','tile_id',
                        'wics1_dir','wics2_dir','wics1s1_dir',
                        'wics1_id_list','wics2_id_list','wics1s2_id_list', 
                        'water_layer_file',
                        'intermediate_dir','aux_dir','output_dir','tmp_dir',
                        'hydroyear_start_date','hydroyear_end_date','date_margin', 'include_nobs_in_margin',
                        'log_out_file','log_err_file'
                    ]
    for parameter in required_parameters:
        if parameter not in parameters:
            print("Missing parameters in parameters file: " + ",".join([param for param in required_parameters if param not in parameters]))
            print('22: Parameters file incomplete. Exiting.')
            return deliver(sysargv,parameters,22)

    for parameter in parameters:
        sysargv[parameter] = parameters[parameter]
    sysargv['log_level'] = parameters['log_level'] if 'log_level' in parameters else 'DEBUG'

    import icdio

    icdio.log("Logging initialized",level="DEBUG")
    icdio.log("HRWSI ICD Processor started. Parameters file was read and complete.",level="INFO")
    icdio.log("Parameters: ",level="DEBUG")
    for parameter in parameters:
      icdio.log("\t%s : %s" % (parameter,parameters[parameter]),level="DEBUG")  
    icdio.log("Processor options: ",level="DEBUG")
    for parameter in sysargv:
      icdio.log("\t%s : %s" % (parameter,sysargv[parameter]),level="DEBUG") 

    if sysargv['wics1_id_list'] + sysargv['wics2_id_list'] + sysargv['wics1s2_id_list'] == []:
        icdio.log('23: No input products to process.',level="ERROR")
        return deliver(sysargv,parameters,23)

    missions = 'S1-S2'
    processingBaseline = 'V100'
    sysargv['product_title'] = sysargv['product_title'].replace('processingBaseline',processingBaseline)
    sysargv['product_title'] = sysargv['product_title'].replace('missions',missions)
    sysargv['lis_product_title'] = sysargv['product_title'].replace("ICD_","LIS_")
    tileId = sysargv['tile_id']
    icdio.log("Final product title is ", sysargv['product_title'],level="INFO")

    os.makedirs(sysargv['output_dir'],exist_ok=True)

    # WIC
    WATER = 1
    ICE = 100
    RADARSHADOW = 200
    CLOUD = 205
    OTHER=254
    NODATA = 255
    NODATA16 = 65535
    SENSORBIT = 9  

    # FSC
    NOSNOW = 0
    SNOW = 100

    # WATER LAYER
    PERMANENTWATER = 1
    TEMPORARYWATER = 2

    # QC THRESHOLDS (DRAFT)
    NOBSQCTH3 = 40
    NOBSQCTH2 = 80
    NOBSQCTH1 = 120

    icdColorMap = {
        0: (0,0,255,255),
    }
    [icdColorMap.update({i:(53+i,53+i,255,255)}) for i in range(1,201)]
    [icdColorMap.update({i:(254,254,255,255)}) for i in range(202,366)]
    icdColorMap.update({
        366: (255,255,255,255),
        NODATA16: (0, 0, 0, 0)
    })
    qcColorMap = {
        0: (93,164,0,255),
        1: (189,189,91,255),
        2: (255,194,87,255),
        3: (255,70,37,255),
        NODATA16: (0, 0, 0, 0)
    }

    result = 0

    hydroStartDate = datetime.datetime.strptime(sysargv['hydroyear_start_date'],'%Y%m%d')
    hydroEndDate = datetime.datetime.strptime(sysargv['hydroyear_end_date'],'%Y%m%d')

    dateMargin = datetime.timedelta(days=int(sysargv['date_margin']))
    interpStartDate = hydroStartDate - dateMargin
    interpEndDate = hydroEndDate + dateMargin

    inclNobsInMargin = sysargv['include_nobs_in_margin']
    nobsStartDate = interpStartDate if inclNobsInMargin else hydroStartDate
    nobsEndDate = interpEndDate if inclNobsInMargin else hydroEndDate

    productTypes = ['wics1','wics2','wics1s2']

    # collect
    wics = {}
    for productType in productTypes:
        for productName in sysargv[productType + '_id_list']:
            productTimestamp = datetime.datetime.strptime(productName.split('_')[1],"%Y%m%dT%H%M%S")
            if not (interpStartDate <= productTimestamp <= interpEndDate):
                icdio.log("%s does not correspond to the time interval for processing. Product will not be used." % productName, level="WARNING")
                continue
            productDate = productTimestamp.strftime("%Y%m%d")
            if productDate not in wics:
                wics.update({
                    productDate : {
                        'wics1' : [],
                        'wics2' : [],
                        'wics1s2' : [],
                        'fsc' : 'FSC_%sT120000_S2_T%s_V100_1' % (productDate,tileId), 
                    }
                })
            wics[productDate][productType].append(productName)
    wicInputList = []

    # convert/merge
    icdio.log("Reading a product to initialize layers")
    try:
        productName, productType = [ (wics[productDate][productType][0],productType) for productType in productTypes for productDate in wics if wics[productDate][productType] != [] ][0]
        wic, icdGeoTransform, icdProjectionRef = icdio.readRaster(os.path.join(sysargv[productType + '_dir'],productName,productName + '_WIC.tif'))
        icdShape = wic.shape
        if productType == 'wics1':
            icdGeoTransform = (icdGeoTransform[0],icdGeoTransform[1]//3,icdGeoTransform[2],icdGeoTransform[3],icdGeoTransform[4],icdGeoTransform[5]//3)
            icdShape = (icdShape[0]*3,icdShape[1]*3)
        nobs = np.zeros(shape=icdShape,dtype=np.uint16)
        # ncso = np.zeros(shape=icdShape,dtype=np.uint16)
        # ncwo = np.zeros(shape=icdShape,dtype=np.uint16)
        wic = None
        icdio.log("Target product shape: %s by %s" % icdShape, level="DEBUG")
        icdio.log("Target product geotransform: %s" % str(icdGeoTransform), level="DEBUG")
        icdio.log("Target product CRS: %s" % str(icdProjectionRef), level="DEBUG")
    except Exception as e:
        icdio.log("41: Problem in processing ",level="ERROR")
        icdio.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)

    icdio.log("Merging and converting WIC products to FSC-like products for LIS and counting observations")
    for productDate in sorted(list(wics.keys())):
        icdio.log("Day: %s" % productDate, level="INFO")
        try:
            fsc = NODATA*np.ones(shape=icdShape,dtype=np.uint8)
            # TODO Complete merging cases
            productType = 'wics1'
            wicTitle = wics[productDate][productType][0]
            fscTitle = wics[productDate]['fsc']
            productTimestamp = datetime.datetime.strptime(wicTitle.split('_')[1],"%Y%m%dT%H%M%S")
            wicPath = os.path.join(sysargv[productType + '_dir'],wicTitle)
            fscPath = os.path.join(sysargv['intermediate_dir'],fscTitle)
            fscTmpPath = os.path.join(sysargv['tmp_dir'],str(uuid.uuid4()),fscTitle)
            wicInputList.append(wicTitle)

            # Read and resample
            wic = icdio.readRaster(os.path.join(wicPath,wicTitle + '_WIC.tif'))[0]
            if productType == 'wics1':
                wic = np.kron(wic, np.ones((icdShape[0]//wic.shape[0],icdShape[1]//wic.shape[1]),dtype=wic.dtype))
            # Manupilate gaps and values
            # ICE -> SNOW
            np.place(fsc,wic == ICE, SNOW)
            # WATER -> NOSNOW
            np.place(fsc,wic == WATER, NOSNOW)
            # RADARSHADOW, OTHER -> CLOUD
            np.place(fsc,wic == RADARSHADOW, CLOUD)
            np.place(fsc,wic == OTHER, CLOUD)

            # find nobs
            # if productType == 'wics1s2':
            #     qf = icdio.readRaster(os.path.join(wicPath,wicTitle + '_QCFLAGS.tif'))[0]
            #     s1pixels = np.bitwise_and(np.right_shift(qf,SENSORBIT),1).astype(np.bool_)
            # elif productType == 'wics1':
            #     s1pixels = np.ones(shape=fsc.shape,dtype=np.bool_)
            # elif productType == 'wics2':
            #     s1pixels = np.zeros(shape=fsc.shape,dtype=np.bool_)
            validpixels = (fsc >= 0) * (fsc <= 100)
            # cso = validpixels & ~s1pixels
            # wso = validpixels & s1pixels
            if nobsStartDate <= productTimestamp <= nobsEndDate:
                # ncso += cso.astype(ncso.dtype)
                # ncwo += wso.astype(ncwo.dtype)
                nobs += validpixels.astype(nobs.dtype)
        except Exception as e:
            icdio.log("41: Problem in processing ",level="ERROR")
            icdio.log(traceback.format_exc(),level='ERROR')
            return deliver(sysargv,parameters,41)

        try:
            os.makedirs(fscTmpPath,exist_ok=True)
            icdio.writeRaster(os.path.join(fscTmpPath,fscTitle + '_FSCOG.tif'), fsc, icdGeoTransform, icdProjectionRef)
        except Exception as e:
            icdio.log("81: Problem in writing rasters",level="ERROR")
            icdio.log(traceback.format_exc(),level='ERROR')
            if os.path.exists(fscTmpPath):
                shutil.rmtree(fscTmpPath)
            return deliver(sysargv,parameters,81)
    
        try:
            shutil.copytree(fscTmpPath,fscPath)
        except Exception as e:
            icdio.log("82: Problem in copying product, %s to %s" % (fscTmpPath, fscPath),level="ERROR")
            icdio.log(traceback.format_exc(),level='ERROR')
            if os.path.exists(fscTmpPath):
                shutil.rmtree(fscTmpPath)
            if os.path.exists(fscPath):
                shutil.rmtree(fscPath)
            return deliver(sysargv,parameters,82)

    # RUN LIS and log it
    # This part of ICD calculation is identical to SP
    icdio.log("Calling LIS to calculate masks, interpolation and durations",level="INFO")
    lisCmd = [
            "/usr/bin/python", "/usr/local/app/let_it_snow_synthesis.py",
            "-c", "/opt/icd/lis_configuration.json",
            "-j", "/opt/icd/lis_synthesis_launch_file.json",
            "-o", os.path.join(sysargv['intermediate_dir'],sysargv['lis_product_title']),
            "-t", tileId,
            "-b", hydroStartDate.strftime("%d/%m/%Y"), "-e", hydroEndDate.strftime("%d/%m/%Y"),
            "--date_margin", str(dateMargin.days),
            "-l", sysargv['log_level']
        ]
    lisLogPath = os.path.join(sysargv['intermediate_dir'],sysargv['lis_product_title'],'tmp','lis.log')
    fscList = [wics[productDate]['fsc'] for productDate in wics]
    fscList.sort()
    for productTitle in fscList:
        lisCmd.append("-i")
        lisCmd.append(os.path.join(sysargv['intermediate_dir'],productTitle))
    icdio.log("Number of input products for LIS: %s" % len(fscList))
    icdio.log("LIS command: %s" % " ".join(lisCmd), level="DEBUG")

    try:
        process = subprocess.Popen(lisCmd, stdout=subprocess.DEVNULL)
        logPosition = 0
        while True:
            sleep(1)
            if os.path.exists(lisLogPath):
                with open(lisLogPath,"r") as log:
                    log.seek(logPosition)
                    for line in log:
                        line = line.replace('\n','').replace('\r','')
                        icdio.log("LIS:" + line)
                    logPosition = log.tell()
                    if process.poll() is not None:
                        log.seek(logPosition)
                        for line in log:
                            line = line.replace('\n','').replace('\r','')
                            icdio.log("LIS:" + line)
                        break
    except Exception as e:
        icdio.log("41: Problem in running LIS software ",level="ERROR")
        icdio.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)


    if process.returncode == 0:
        icdio.log("LIS Process finished successfuly.",level="INFO")
    else:
        icdio.log("41: LIS Process failed.",level="ERROR")
        return deliver(sysargv,parameters,41)

    sysargv['lis_product_filename'] = "LIS_S2-SNOW-layer_%s_%s_%s_1.11.0_1.tif" % (tileId, hydroStartDate.strftime("%Y%m%d"), hydroEndDate.strftime("%Y%m%d"))
    icdio.log("LIS output filename template is %s" % sysargv['lis_product_filename'], level="DEBUG")

    # Convert to ICD
    icdio.log("Reading ICD from LIS output")
    icd = icdio.readRaster(os.path.join(sysargv['intermediate_dir'],sysargv['lis_product_title'],sysargv['lis_product_filename'].replace("layer","SCD")))[0]


    # # Mask low icd
    # # Leave in case prod update ( and sp)
    # icdio.log("Marking low ICD")
    # np.place(icd,icd < LOWSPTHRESHOLD, NODATA16)


    # # Create QC
    # # for sp there is qcod qcmd etc, qcmean

    icdio.log("Calculating QC from NOBS")
    try:
        qc = NODATA16*np.ones(shape=icdShape,dtype=np.uint16)
        np.place(qc,                       (nobs < NOBSQCTH3), 3)
        np.place(qc, (NOBSQCTH3 <= nobs) * (nobs < NOBSQCTH2), 2)
        np.place(qc, (NOBSQCTH2 <= nobs) * (nobs < NOBSQCTH1), 1)
        np.place(qc, (NOBSQCTH1 <= nobs)                     , 0)
    except Exception as e:
        icdio.log("41: Problem in processing ",level="ERROR")
        icdio.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)

    # # for sp there is qcflags
    # # low scd
    # (A0<60)*((A1==0)+(A1==254))
    # # tree dens
    # (A0<101)*(A0>90) * ((A1==0)+(A1==254))
    # # sws area
    # (A0!=210)*(A0!=220)*(A0!=230)*(A1==0)

    
    # # Apply water mask
    icdio.log("Masking non-water pixels")
    try:
        water = icdio.readRaster(os.path.join(sysargv['aux_dir'],sysargv['water_layer_file']))[0]
    except Exception as e:
        icdio.log("41: Problem in reading water layer.",level="ERROR")
        icdio.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)
    try:
        np.place(icd, (water != PERMANENTWATER) * (water != TEMPORARYWATER), NODATA16)
        np.place(qc, (water != PERMANENTWATER) * (water != TEMPORARYWATER), NODATA16)
        np.place(nobs, (water != PERMANENTWATER) * (water != TEMPORARYWATER), NODATA16)
    except Exception as e:
        icdio.log("41: Problem in processing ",level="ERROR")
        icdio.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)

    ### Stats calculation
    # TODO
        
    productDir = os.path.join(sysargv['output_dir'],sysargv['product_title'])
    productTmpDir = os.path.join(sysargv['tmp_dir'],str(uuid.uuid4()))
    os.makedirs(productTmpDir)

    icdio.log("Writing rasters",level="INFO")
    try:
        icdio.writeRaster(os.path.join(productTmpDir,sysargv['product_title'] + '_ICD.tif'),icd,icdGeoTransform,icdProjectionRef,icdColorMap)
        cogCheck = validate_cloud_optimized_geotiff.main(['',os.path.join(productTmpDir,sysargv['product_title'] + '_ICD.tif'),'-q'])
        if cogCheck == 1:
            icdio.log("61: COG validation failed for ICD.tif",level="ERROR")
            return deliver(sysargv,parameters,61)
        resourceSize = os.path.getsize(os.path.join(productTmpDir,sysargv['product_title'] + '_ICD.tif'))
        icdio.writeThumbnail(os.path.join(productTmpDir,'thumbnail.png'),icd,icdColorMap)

        icdio.writeRaster(os.path.join(productTmpDir,sysargv['product_title'] + '_QC.tif'),qc,icdGeoTransform,icdProjectionRef,qcColorMap)
        resourceSize += os.path.getsize(os.path.join(productTmpDir,sysargv['product_title'] + '_QC.tif'))
        cogCheck = validate_cloud_optimized_geotiff.main(['',os.path.join(productTmpDir,sysargv['product_title'] + '_QC.tif'),'-q'])
        if cogCheck == 1:
            icdio.log("61: COG validation failed for QC.tif",level="ERROR")
            return deliver(sysargv,parameters,61)

        icdio.writeRaster(os.path.join(productTmpDir,sysargv['product_title'] + '_NOBS.tif'),nobs,icdGeoTransform,icdProjectionRef)
        resourceSize += os.path.getsize(os.path.join(productTmpDir,sysargv['product_title'] + '_NOBS.tif'))
        cogCheck = validate_cloud_optimized_geotiff.main(['',os.path.join(productTmpDir,sysargv['product_title'] + '_NOBS.tif'),'-q'])
        if cogCheck == 1:
            icdio.log("61: COG validation failed for NOBS.tif",level="ERROR")
            return deliver(sysargv,parameters,61)

        # Leaving this in case we update the product content
        # icdio.writeRaster(os.path.join(productTmpDir,sysargv['product_title'] + '_NCSO.tif'),ncso,icdGeoTransform,icdProjectionRef)
        # resourceSize += os.path.getsize(os.path.join(productTmpDir,sysargv['product_title'] + '_NCSO.tif'))
        # cogCheck = validate_cloud_optimized_geotiff.main(['',os.path.join(productTmpDir,sysargv['product_title'] + '_NCSO.tif'),'-q'])
        # if cogCheck == 1:
        #     icdio.log("61: COG validation failed for NCSO.tif",level="ERROR")
        #     return deliver(sysargv,parameters,61)

        # icdio.writeRaster(os.path.join(productTmpDir,sysargv['product_title'] + '_NCWO.tif'),ncwo,icdGeoTransform,icdProjectionRef)
        # resourceSize += os.path.getsize(os.path.join(productTmpDir,sysargv['product_title'] + '_NCWO.tif'))
        # cogCheck = validate_cloud_optimized_geotiff.main(['',os.path.join(productTmpDir,sysargv['product_title'] + '_NCWO.tif'),'-q'])
        # if cogCheck == 1:
        #     icdio.log("61: COG validation failed for NCWO.tif",level="ERROR")
        #     return deliver(sysargv,parameters,61)

    except Exception as e:
        icdio.log("81: Problem in writing rasters",level="ERROR")
        icdio.log(traceback.format_exc(),level='ERROR')
        if os.path.exists(productTmpDir):
            shutil.rmtree(productTmpDir)
        return deliver(sysargv,parameters,81)


    ### Publication json
    productionTime = datetime.datetime.utcnow()
    productStartDate = datetime.datetime.strptime(sysargv['hydroyear_start_date'] + 'T000000',"%Y%m%dT%H%M%S")
    productEndDate = datetime.datetime.strptime(sysargv['hydroyear_end_date'] + 'T000000',"%Y%m%dT%H%M%S")
    geometry = icdio.getAlphashape(icd, NODATA16, icdGeoTransform, icdProjectionRef)
    icdio.log("Writing JSON Metadata",level="INFO")
    product = {
        # "collection_name": "HR-WS&I",
        "resto": {
            # "type": "Feature",
            "geometry": {
                "wkt": geometry
            },
            "properties": {
                # "productIdentifier": "/HRWSI/CLMS/Pan-European/High_Resolution_Layers/Ice/ICD/"+productStartDate.strftime("%Y/%m/%d/")+sysargv['product_title'],
                # "title": sysargv['product_title'],
                "resourceSize": str(resourceSize), ##Byte
                # "organisationName": "EEA",
                "startDate": productStartDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), ##sensing start
                "endDate": productEndDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), ##sensing end
                "completionDate": productionTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), ##generation date of the product
                # "published": None,
                # "productType": "ICD",
                # "mission": "S1-S2",
                "resolution": '20', ##meters
                # "cloudCover": '0', #%
                # "processingBaseline": processingBaseline,
                # "host_base": "cf2.cloudferro.com:8080",
                # "s3_bucket": "HRWSI",
                # "thumbnail": "Preview/CLMS/Pan-European/High_Resolution_Layers/Ice/ICD/"+productStartDate.strftime("%Y/%m/%d/")+sysargv['product_title']+"/thumbnail.png"
            }
        }
    }
    jsonFile = open(os.path.join(productTmpDir,'dias_catalog_submit.json'), 'w')
    json.dump(product, jsonFile)
    jsonFile.close()


    icdio.log("Writing XML Metadata")
    geometryBounds = icdio.getGeoBounds(wic,icdGeoTransform,icdProjectionRef)
    productXml = xmltodict.parse(open(os.path.join(baseDir,'ICD_Metadata.xml'),'r').read())
    productXml['gmd:MD_Metadata']['gmd:fileIdentifier']['gco:CharacterString'] = sysargv['product_title']
    productXml['gmd:MD_Metadata']['gmd:contact']['gmd:CI_ResponsibleParty']['gmd:contactInfo']['gmd:CI_Contact']['gmd:address']['gmd:CI_Address']['gmd:electronicMailAddress']['gco:CharacterString'] = 'copernicus@eea.europa.eu'
    productXml['gmd:MD_Metadata']['gmd:dateStamp']['gco:DateTime'] = productionTime.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:alternateTitle']['gco:CharacterString'] = sysargv['product_title']
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:date']['gmd:CI_Date']['gmd:date']['gco:DateTime'] = productionTime.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:edition']['gco:CharacterString'] = processingBaseline
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:editionDate']['gco:DateTime'] = productionTime.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:identifier']['gmd:RS_Identifier']['gmd:code']['gco:CharacterString'] = sysargv['product_title']
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:otherCitationDetails']['gco:CharacterString'] = 'https://land.copernicus.eu/user-corner/technical-library'
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:pointOfContact']['gmd:CI_ResponsibleParty']['gmd:contactInfo']['gmd:CI_Contact']['gmd:address']['gmd:CI_Address']['gmd:electronicMailAddress']['gco:CharacterString'] = 'copernicus@eea.europa.eu'
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:geographicElement']['gmd:EX_GeographicBoundingBox']['gmd:westBoundLongitude']['gco:Decimal'] = str(geometryBounds[0])
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:geographicElement']['gmd:EX_GeographicBoundingBox']['gmd:eastBoundLongitude']['gco:Decimal'] = str(geometryBounds[1])
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:geographicElement']['gmd:EX_GeographicBoundingBox']['gmd:southBoundLatitude']['gco:Decimal'] = str(geometryBounds[2])
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:geographicElement']['gmd:EX_GeographicBoundingBox']['gmd:northBoundLatitude']['gco:Decimal'] = str(geometryBounds[3])
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:temporalElement']['gmd:EX_TemporalExtent']['gmd:extent']['gml:TimePeriod']['@gml:id'] = sysargv['product_title']
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:temporalElement']['gmd:EX_TemporalExtent']['gmd:extent']['gml:TimePeriod']['gml:beginPosition'] = hydroStartDate.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:temporalElement']['gmd:EX_TemporalExtent']['gmd:extent']['gml:TimePeriod']['gml:endPosition'] = hydroEndDate.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:dataQualityInfo']['gmd:DQ_DataQuality']['gmd:report'][0]['gmd:DQ_NonQuantitativeAttributeAccuracy']['gmd:result']['gmd:DQ_ConformanceResult']['gmd:specification']['gmd:CI_Citation']['gmd:title']['gco:CharacterString'] = productXml['gmd:MD_Metadata']['gmd:dataQualityInfo']['gmd:DQ_DataQuality']['gmd:report'][0]['gmd:DQ_NonQuantitativeAttributeAccuracy']['gmd:result']['gmd:DQ_ConformanceResult']['gmd:specification']['gmd:CI_Citation']['gmd:title']['gco:CharacterString'].replace('[VALIDATION_REPORT_FILENAME]','hrwsi-ice-qar') #update when report is ready
    productXml['gmd:MD_Metadata']['gmd:dataQualityInfo']['gmd:DQ_DataQuality']['gmd:report'][0]['gmd:DQ_NonQuantitativeAttributeAccuracy']['gmd:result']['gmd:DQ_ConformanceResult']['gmd:specification']['gmd:CI_Citation']['gmd:date']['gmd:CI_Date']['gmd:date']['gco:Date'] = '1900-01-01' #update when report is ready
    productXml['gmd:MD_Metadata']['gmd:series']['gmd:DS_OtherAggregate']['gmd:seriesMetadata'] = []
    for p in np.argsort(wicInputList).tolist():
        productInputTitle = wicInputList[p]
        productType = 'wics1s2' if productInputTitle.split('_')[2] == 'S1-S2' else 'wic' + productInputTitle.split('_')[2][:2].lower()
        # TODO remove exception for test files (test files has no XML MTD yet)
        if os.path.exists(os.path.join(sysargv[productType + '_dir'],productInputTitle,productInputTitle + '_MTD.xml')):
            productInputXml = xmltodict.parse(open(os.path.join(sysargv[productType + '_dir'],productInputTitle,productInputTitle + '_MTD.xml'),'r').read())
            productInputXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:temporalElement']['gmd:EX_TemporalExtent']['gmd:extent']['gml:TimePeriod']['@gml:id'] = productInputTitle
        else:
            productInputXml = productInputTitle
        productXml['gmd:MD_Metadata']['gmd:series']['gmd:DS_OtherAggregate']['gmd:seriesMetadata'].append(productInputXml)

    productXml = xmltodict.unparse(productXml, pretty=True)
    xmlFile = open(os.path.join(productTmpDir,sysargv['product_title']+'_MTD.xml'), 'w')
    xmlFile.write(productXml)
    xmlFile.close()

    try:
        shutil.copytree(productTmpDir,productDir)
    except Exception as e:
        icdio.log("82: Problem in copying product, %s to %s" % (productTmpDir, productDir),level="ERROR")
        icdio.log(traceback.format_exc(),level='ERROR')
        # Leave the files so there can be investigations
        # if os.path.exists(productTmpDir):
        #     shutil.rmtree(productTmpDir)
        # if os.path.exists(productDir):
        #     shutil.rmtree(productDir)
        return deliver(sysargv,parameters,82)

    if os.path.exists(productTmpDir):
        shutil.rmtree(productTmpDir)

    return deliver(sysargv,parameters,result)

if __name__ == "__main__":
    sys.exit(main())
