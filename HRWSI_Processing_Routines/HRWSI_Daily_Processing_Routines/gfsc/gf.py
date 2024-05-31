#!/usr/bin/python3

import os, sys, argparse, datetime, xmltodict, yaml, traceback
import numpy as np

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
            gfio.log("Exiting with code ", result)
        except:
            print("Exiting with code ", result)
        return result

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
    required_parameters = ['aggregation_timespan','product_title','tile_id',
                        'obsolete_product_id_list', 'fsc_id_list','sws_id_list','gfsc_id_list',
                        'gfsc_dir','fsc_dir','sws_dir',
                        'water_layer_file',
                        'intermediate_dir','output_dir','aux_dir','tmp_dir',
                        'log_out_file','log_err_file'
                    ]
    for parameter in required_parameters:
        if parameter not in parameters:
            print("Missing parameters in parameters file: " + ",".join([param for param in required_parameters if param not in parameters]))
            print('22: Parameters file incomplete. Exiting.')
            return deliver(sysargv,parameters,22)
        
    sysargv['day_delta'] = parameters['aggregation_timespan']
    sysargv['output_dir'] = parameters['output_dir']
    sysargv['intermediate_dir'] = parameters['intermediate_dir']
    sysargv['product_title'] = parameters['product_title']
    sysargv['tile_id'] = parameters['tile_id']
    sysargv['tmp_dir'] = parameters['tmp_dir']
    sysargv['fsc'] = parameters['fsc_id_list']
    sysargv['sws'] = parameters['sws_id_list']
    sysargv['gf'] = parameters['gfsc_id_list']
    sysargv['obsolete'] = parameters['obsolete_product_id_list']
    for product in sysargv['obsolete']:
        if product in sysargv['fsc']:
            sysargv['fsc'].remove(product)
        if product in sysargv['sws']:
            sysargv['sws'].remove(product)
    sysargv['log_level'] = parameters['log_level'] if 'log_level' in parameters else 'DEBUG'
    
    import gf1, gf2, gfio

    gfio.log("Logging initialized",level="DEBUG")
    gfio.log("HRWSI GFSC Processor started. Parameters file was read and complete.",level="INFO")
    gfio.log("Parameters: ",level="DEBUG")
    for parameter in parameters:
      gfio.log("\t%s : %s" % (parameter,parameters[parameter]),level="DEBUG")  
    gfio.log("Processor options: ",level="DEBUG")
    for parameter in sysargv:
      gfio.log("\t%s : %s" % (parameter,sysargv[parameter]),level="DEBUG") 

    if sysargv['sws'] + sysargv['fsc'] + sysargv['gf'] == []:
        gfio.log('23: No input products to process.',level="ERROR")
        return deliver(sysargv,parameters,23)

    missions = 'S1-S2'
    processingBaseline = 'V200'
    useMetadata = False # added to handle validation data production, without XML files in input products (and also output)
    sysargv['product_title'] = sysargv['product_title'].replace('processingBaseline',processingBaseline)
    sysargv['product_title'] = sysargv['product_title'].replace('missions',missions)
    tileId = sysargv['tile_id']
    gfio.log("Final product title is ", sysargv['product_title'],level="INFO")

    # Group daily sws and fsc for gf1
    productList = {}    # day:[productTitles]
    for productTitle in sysargv['sws'] + sysargv['fsc']:
        productTimeStamp = datetime.datetime.strptime(productTitle.split('_')[1].split('-')[0],"%Y%m%dT%H%M%S")
        productDay = datetime.date(productTimeStamp.year,productTimeStamp.month,productTimeStamp.day)
        if productDay not in productList:
            productList.update({productDay:[]})
        productList[productDay].append(productTitle)

    # Get all product metadata and decide on the output
    productDirs = []
    productTypes = []
    productTitles = []
    productTimeStamps = []
    productXmls = []
    productStartDates = []
    productEndDates = []
    productInputTitles = []
    productInputTypes = []
    productInputTimeStamps = []

    # add gf1 products planned
    for productDay in productList:
        productInputTitle = []
        productInputType = []
        productInputTimeStamp = []

        for productTitle in productList[productDay]:
            try:
                productTimeStamp = datetime.datetime.strptime(productTitle.split('_')[1].split('-')[0],"%Y%m%dT%H%M%S")
                productInputTitle.append(productTitle)
                productInputType.append(productTitle.split('_')[0])
                productInputTimeStamp.append(productTimeStamp)
            except Exception as e:
                gfio.log("24: Problem reading product list",level='ERROR')
                gfio.log(traceback.format_exc(),level='ERROR')
                return deliver(sysargv,parameters,24)

        if productInputTitle == []:
            gfio.log("25: Empty product list",level='ERROR')
            return deliver(sysargv,parameters,25)

        if 'SWS' not in productInputType:
            continue

        productTimeStamp = datetime.datetime(productDay.year,productDay.month,productDay.day)
        productTitle = '_'.join(['GFSC1',productTimeStamp.strftime("%Y%m%d"),missions,tileId,processingBaseline])
        productDir = gfio.getDirPath(productTitle)

        productDirs.append(productDir)
        productTypes.append('GFSC1')
        productTitles.append(productTitle)
        productTimeStamps.append(productTimeStamp)
        productXmls.append(None)
        productStartDates.append(None)
        productEndDates.append(None)
        productInputTitles.append(productInputTitle)
        productInputTypes.append(productInputType)
        productInputTimeStamps.append(productInputTimeStamp)

    for productTitle in sysargv['gf'] + sysargv['sws'] + sysargv['fsc']:
        try:
            productType = gfio.getProductType(productTitle)
            productDir = gfio.getDirPath(productTitle)
            xmlFile = gfio.getFilePath(productTitle,'MTD.xml')
            if useMetadata:
                productXml = xmltodict.parse(open(xmlFile,'r').read())
            else:
                # create fake metadata for rest of the steps
                productStartDate = productTitle.split('_')[1] 
                productStartDate = datetime.datetime.strptime(productStartDate,"%Y%m%dT%H%M%S") if 'T' in productStartDate else datetime.datetime.strptime(productStartDate,"%Y%m%d")
                productStartDate = productStartDate.strftime("%Y-%m-%dT%H:%M:%S.%f")
                productEndDate = productStartDate
                productXml = {
                    'gmd:MD_Metadata': {
                            'gmd:fileIdentifier' : {'gco:CharacterString' : productTitle},
                            'gmd:identificationInfo': {'gmd:MD_DataIdentification': {'gmd:extent': {'gmd:EX_Extent': {'gmd:temporalElement': {'gmd:EX_TemporalExtent': {'gmd:extent': {'gml:TimePeriod': {
                                'gml:beginPosition' : productStartDate,
                                'gml:endPosition' : productEndDate
                            }}}}}}}}
                        }
                }

            productStartDate = productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:temporalElement']['gmd:EX_TemporalExtent']['gmd:extent']['gml:TimePeriod']['gml:beginPosition']
            try:
                productStartDate = datetime.datetime.strptime(productStartDate,"%Y-%m-%dT%H:%M:%S.%f")
            except:
                productStartDate = datetime.datetime.strptime(productStartDate,"%Y-%m-%dT%H:%M:%S")
            productEndDate = productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:temporalElement']['gmd:EX_TemporalExtent']['gmd:extent']['gml:TimePeriod']['gml:endPosition']
            try:
                productEndDate = datetime.datetime.strptime(productEndDate,"%Y-%m-%dT%H:%M:%S.%f")
            except:
                productEndDate = datetime.datetime.strptime(productEndDate,"%Y-%m-%dT%H:%M:%S")
            if productType in ['FSC','SWS']:
                productTimeStamp = datetime.datetime.strptime(productTitle.split('_')[1].split('-')[0],"%Y%m%dT%H%M%S")
                productInputTitles.append([productTitle])
                productInputTypes.append([productType])
                productInputTimeStamps.append([productTimeStamp])
            if productType == 'GFSC':
                productTimeStamp = datetime.datetime.strptime(productTitle.split('_')[1].split('-')[0],"%Y%m%d")
                productInputXmls = productXml['gmd:MD_Metadata']['gmd:series']['gmd:DS_OtherAggregate']['gmd:seriesMetadata']
                if len(productInputXmls) == 1:
                    productInputXmls = [productInputXmls]
                for productInputXml in productInputXmls:
                    productInputTitle = []
                    productInputType = []
                    productInputTimeStamp = []
                    productInputTimeStamp.append(datetime.datetime.strptime(productInputXml['gmd:MD_Metadata']['gmd:fileIdentifier']['gco:CharacterString'].split('_')[1].split('-')[0],"%Y%m%dT%H%M%S"))
                    productInputTitle.append(productInputXml['gmd:MD_Metadata']['gmd:fileIdentifier']['gco:CharacterString'])
                    productInputType.append(productInputXml['gmd:MD_Metadata']['gmd:fileIdentifier']['gco:CharacterString'].split('_')[0])
                productInputTitles.append(productInputTitle)
                productInputTypes.append(productInputType)
                productInputTimeStamps.append(productInputTimeStamp)
            productDirs.append(productDir)
            productTypes.append(productType)
            productTitles.append(productTitle)
            productTimeStamps.append(productTimeStamp)
            productXmls.append(productXml)
            productStartDates.append(productStartDate)
            productEndDates.append(productEndDate)
        except Exception as e:
            gfio.log("25: Problem reading product list",level="ERROR")
            gfio.log(traceback.format_exc(),level='ERROR')
            return deliver(sysargv,parameters,25)

    if productDirs == []:
        gfio.log("25: Empty product list",level="ERROR")
        return deliver(sysargv,parameters,25)

    result = 0
    productOrder = (np.argsort(productTimeStamps)[::-1]).tolist()
    finalProductTimeStamp = productTimeStamps[productOrder[0]]
    finalProductTimeStamp = datetime.datetime(finalProductTimeStamp.year,finalProductTimeStamp.month,finalProductTimeStamp.day,23,59,59)

    #produce GF1s first
    for p in productOrder:
        if productTypes[p] != 'GFSC1':
            continue
        args = []
        for r,productInputTitle in enumerate(productInputTitles[p]):
            if productInputTypes[p][r] == 'SWS':
                args += ["-w",productInputTitle]
            if productInputTypes[p][r] == 'FSC':
                args += ["-f",productInputTitle]
        args += ["-o",sysargv['intermediate_dir']]
        args += ["-p",productTitles[p]]
        args += ["-t",sysargv['tmp_dir']]
        sys.argv[1:] = args
        result = gf1.main()
        if result != 0:
            return deliver(sysargv,parameters,result)

    #produce GF2
    if result == 0:
        args = []
        for p in productOrder:
            if productTypes[p] == 'GFSC':
                args += ["-g",productTitles[p]]
            if productTypes[p] == 'GFSC1':
                args += ["-g1",productTitles[p]]
            if productTypes[p] == 'FSC':
                args += ["-f",productTitles[p]]
            args += ["-o",sysargv['output_dir']]
            args += ["-p",sysargv['product_title']]
            args += ["-t",sysargv['tmp_dir']]
            args += ["-d",sysargv['day_delta']]
        sys.argv[1:] = args
        result = gf2.main()

    return deliver(sysargv,parameters,result)

if __name__ == "__main__":
    sys.exit(main())
