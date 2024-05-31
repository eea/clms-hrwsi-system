#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, shutil, subprocess, tempfile
from datetime import datetime, timedelta

import glob
import multiprocessing
import json
import re

compute_awic_docker_image_default = 'awic:latest'
export_awic_docker_image_default = 'awic_export:2_21'

port_number_base = 5432
Europe_polygon = 'POLYGON((-8.521263215755956+74.27442378824767%2C-41.81467638940865+46.29752415308005%2C12.556581095621294+26.022285227748796%2C72.67634157466321+30.863991364289717%2C60.46077271238776+74.78548595583968%2C-8.521263215755956+74.27442378824767))'


def make_appsettings_json(output_file, ip_number, port_number):
    dico = {
    "Configuration" : {
        "SnapPath": "/install/snap/bin/gpt",
        "GdalFgdbPath": "/install/gdal-2.3.1/apps",
        "TileCodes": "/work/part2/ice_s1/TileCodes/TileCodes.txt",
        "GraphPath": "/home/eouser/graphs/preprocessing_classification_fre_5class_md20m_1input_14flat_bsi_cut_auto.xml",
        "GraphS1Path": "/home/eouser/graphs/grd_preprocessing_threshold_speckle_filtering_Sim_subs_rep_2_auto.xml",
        "WicMetadataTemplatePath": "/home/eouser/metadata/WIC_Metadata.xml",
        "WicS1MetadataTemplatePath": "/home/eouser/metadata/WIC_S1_Metadata.xml",
        "WicS1S2MetadataTemplatePath": "/home/eouser/metadata/WIC_S1S2_Metadata.xml",
        "AwicMetadataTemplatePath": "/home/eouser/metadata/AWIC_Metadata.xml",
        "AwicS1S2MetadataTemplatePath": "/home/eouser/metadata/AWIC_S1S2_Metadata.xml",
        "PostgreHost": "%s"%ip_number,
        "PostgrePort": '%d'%port_number,
        "PostgreDb": "hrwsi",
        "PostgreUser": "postgres",
        "PostgrePassword": "hrwsi",
        "MaxThreads": '1',
        "ProductVersion": "V100",
        "GenerationMode": '1',
        "HelpDeskEmail": "TBD",
        "PumUrl": "TBD",
        "DiasUrl": "TBD",
        "DiasPortalName": "TBD",
        "ValidationReportFilename": "TBD",
        "ValidationReportDate": "TBD"
    },
    "Serilog": {
        "MinimumLevel": "Debug",
        "WriteTo": [
            { "Name": "Console",
                "Args": { "restrictedToMinimumLevel": "Information" } 
            },
            { "Name": "Async",
                "Args":  {
                "configure": [
                    { "Name": "File", 
                        "Args": { "path": "/work/si/Logs/ProcessRiverIce.log" },
                        "outputTemplate": "{Timestamp:yyyy-MM-dd HH:mm:ss.fff} [{Level}] [{SourceContext}] [{EventId}] {Message}{NewLine}{Exception}",
                        "buffered": 'true'}
                ]
            }
        }]   
    }
}
    with open(output_file, mode='w') as ds:
        json.dump(dico, ds, indent=4)





def rezipfile(zipfile_in, zipfile_out=None, permissions='rx', temp_dir=None):
    if temp_dir is None:
        temp_dir = os.getcwd()
    temp_dir = os.path.abspath(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    temp_dir_session = None
    try:
        temp_dir_session = tempfile.mkdtemp(dir=temp_dir, prefix='rezip')
        cmd = 'cd %s; unzip %s; chmod -R u+%s %s; zip -r %s %s'%(temp_dir_session, os.path.abspath(zipfile_in), permissions, os.path.basename(zipfile_in).replace('.zip', ''), \
            os.path.basename(zipfile_in), os.path.basename(zipfile_in).replace('.zip', ''))
        print(cmd)
        subprocess.check_call(cmd, shell=True)
        zipfile_new_path = os.path.join(temp_dir_session, os.path.basename(zipfile_in))
        assert os.path.exists(zipfile_new_path)
        if zipfile_out is not None:
            shutil.move(zipfile_new_path, zipfile_out)
        else:
            shutil.move(zipfile_new_path, zipfile_in)
    finally:
        if temp_dir_session is not None:
            shutil.rmtree(temp_dir_session)


def make_awic_for_basin(basin_loc, awic_metadata_dir, awic_data_dir, start_date, end_date, compute_awic_docker_image, export_awic_docker_image, temp_dir, interactive_str, port_number):
    
    temp_dir = os.path.abspath(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    cwd = os.path.abspath(os.getcwd())

    start_time1 = datetime.utcnow()
    print('Processing basin %s'%basin_loc)
    
    temp_dir_session = None
    postgresql_docker_name = 'awic_postgres'
    try:
        #create temp dir
        temp_dir_session = tempfile.mkdtemp(dir=temp_dir, prefix='awic_%s'%basin_loc)
        os.chdir(cwd)

        #creating appsettings_awics1s2.json
        #get ip of docker container postgresql_docker_name
        ip_number_loc = subprocess.check_output("docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' %s"%postgresql_docker_name, shell=True).decode('utf-8').replace('\n','')
        make_appsettings_json(os.path.join(temp_dir_session, 'appsettings_awics1s2.json'), ip_number_loc, port_number)
        
        #launch AWIC creation
        print('Launching AWIC creation...')
        temp_dir_awic_gen = os.path.join(temp_dir_session, 'awic_gen')
        os.makedirs(temp_dir_awic_gen)
        cmd = 'docker run --rm%s --network=awic_daily_generation_pilot_postgres -v %s:/awic_metadata_dir -v %s:/awic_data_dir -v %s:/temp_dir -v %s:/temp_dir_base %s ProcessRiverIce AWICS1S2 '%(interactive_str, \
            os.path.abspath(awic_metadata_dir), os.path.abspath(awic_data_dir), temp_dir_awic_gen, temp_dir_session, compute_awic_docker_image)
        cmd += '%s %s /awic_data_dir/WIC /awic_data_dir/WIC_S1 /awic_data_dir/WIC_S1S2 '%(start_date, end_date)
        cmd += '{0} /awic_metadata_dir/RiverBasinTiles/{0}.txt /temp_dir /temp_dir_base/appsettings_awics1s2.json'.format(basin_loc)
        print(cmd)
        subprocess.check_call(cmd, shell=True)
        print(' -> Launching AWIC creation : successful')

        return {'basin': basin_loc}

    finally:
        print("TODO")
        
               

def make_awic_update(day_to_retrieve_str, awic_metadata_dir, awic_data_dir, compute_awic_docker_image=None, export_awic_docker_image=None, temp_dir=None, interactive=False, nprocs=None):
        
    if compute_awic_docker_image is None:
        compute_awic_docker_image = compute_awic_docker_image_default
    if export_awic_docker_image is None:
        export_awic_docker_image = export_awic_docker_image_default
    
    
    if interactive:
        interactive_str = ' -it'
    else:
        interactive_str = ''
    
    if nprocs is None:
        nprocs = 1
    

    temp_dir = os.path.abspath(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    day_to_retrieve = datetime.strptime(day_to_retrieve_str, "%Y-%m-%d")
    tomorrow = day_to_retrieve + timedelta(1)
    #the URL will have to be adapted.
    URL = 'https://cryo.land.magellium.fr/get_awic?geometrywkt=%s&cloudcoveragemax=100&startdate=%s&completiondate=%s&getonlysize=True'%(Europe_polygon, day_to_retrieve.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d'))
    cmd = ['curl', '-s', URL]
    res = subprocess.check_output(cmd, encoding='UTF-8')
    print("Executing request on DB for day %s"%(day_to_retrieve_str))
    nb_products = int(''.join(re.findall("([\d])", res)))
    if nb_products > 5:
        print('AWIC products found for day %s, aborting update'%(day_to_retrieve_str))
        exit()

    products_type = ['WIC', 'WIC_S1', 'WIC_S1S2']
    year = str(day_to_retrieve.year)
    month = "%.2d"%(day_to_retrieve.month)
    day = "%.2d"%(day_to_retrieve.day)
    print("Requesting WIC")

    nb_of_awic_s1 = 0
    nb_of_awic_s2 = 0
    nb_of_awic_s1s2 = 0

    for product_type in products_type:
        os.makedirs(os.path.join(awic_data_dir, product_type, year, month, day))
        #the URL might have to be adapted.
        path = "eodata:HRWSI/CLMS/Pan-European/High_Resolution_Layers/Ice/%s/%s/%s/%s"%(product_type, year, month, day)
        cmd = ['rclone', 'lsf', path]
        res = subprocess.check_output(cmd, encoding='UTF-8')
        if product_type == 'WIC':
            nb_of_awic_s2 = res.count('WIC')
        elif product_type == 'WIC_S1':
            nb_of_awic_s1 = res.count('WIC')
        elif product_type == 'WIC_S1S2':
            nb_of_awic_s1s2 = res.count('WIC_S1S2')

        open('/home/eouser/awic_generation/daily_awic_retrieval/%s_%s.txt'%(day_to_retrieve_str, product_type), 'w')

    nb_of_awic = nb_of_awic_s1 + nb_of_awic_s2 + nb_of_awic_s1s2

    if nb_of_awic >= 300:
        for product_type in products_type:
            #the URL might have to be adapted.
            path = "eodata:HRWSI/CLMS/Pan-European/High_Resolution_Layers/Ice/%s/%s/%s/%s"%(product_type, year, month, day)
            cmd = ['rclone', 'copy', path, os.path.join(awic_data_dir, product_type, year, month, day)]
            res = subprocess.check_output(cmd, encoding='UTF-8')
            
            with open('/home/eouser/awic_generation/daily_awic_retrieval/%s_%s.txt'%(day_to_retrieve_str, product_type), 'a') as the_file:
                for file in glob.glob(os.path.join(awic_data_dir, product_type, year, month, day) + "/*/"):
                    the_file.write(file.split('/')[-2] + '\n')
        
        basin_list = sorted([el.replace('.txt', '') for el in os.listdir(os.path.join(awic_metadata_dir, 'RiverBasinTiles'))])
        if nprocs == 1:
            for basin_loc in basin_list:
                dico_loc = make_awic_for_basin(basin_loc, awic_metadata_dir, awic_data_dir, day_to_retrieve_str, day_to_retrieve_str, compute_awic_docker_image, export_awic_docker_image, \
                    os.path.join(temp_dir, basin_loc), interactive_str, port_number_base)
                print('%s processed'%dico_loc['basin'])
        else:
            pool = multiprocessing.Pool(nprocs)
            for dico_loc in pool.starmap(make_awic_for_basin, [[basin_loc, awic_metadata_dir, awic_data_dir, day_to_retrieve_str, day_to_retrieve_str, compute_awic_docker_image, export_awic_docker_image, \
                os.path.join(temp_dir, basin_loc), interactive_str, port_number_base] for ii_basin, basin_loc in enumerate(basin_list)]):
                shutil.rmtree(os.path.join(temp_dir, dico_loc['basin']))
                print('%s processed'%dico_loc['basin'])

        #the URL will have to be adapted.
        URL = 'https://cryo.land.magellium.fr/get_awic?geometrywkt=%s&cloudcoveragemax=100&startdate=%s&completiondate=%s&getonlysize=True'%(Europe_polygon, day_to_retrieve.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d'))
        cmd = ['curl', '-s', URL]
        res = subprocess.check_output(cmd, encoding='UTF-8')
        nb_products = int(''.join(re.findall("([\d])", res)))
        print("Found %d AWIC products"%(nb_products))
        if nb_products < 100000:
            print('WARNING: few AWIC products found for day %s (only %d)'%(day_to_retrieve_str, nb_products))
    else:
        print('Not enough products for day %s (only %d WIC_S2, %d WIC_S1, %d WIC_S1S2 found), aborting AWIC computation.'%(day_to_retrieve_str, nb_of_awic_s2, nb_of_awic_s1, nb_of_awic_s1s2))

    shutil.rmtree(temp_dir)
    shutil.rmtree(awic_data_dir)
            

        
    
if __name__ == '__main__':
    
    import argparse
    parser = argparse.ArgumentParser(description='This script is used to launch AWIC generation.')
    parser.add_argument("--awic_metadata_dir", type=str, required=True, help='path to directory containing postgresql.zip file and RiverBasinTiles folder')
    parser.add_argument("--awic_data_dir", type=str, required=True, help='path to directory containing WIC_S2, WIC_S1 and WIC_S1S2 directories with at least the products for the period requested')
    parser.add_argument("--day_to_retrieve", type=str, required=True, help='day_to_retrieve in %Y-%m-%d format')
    parser.add_argument("--compute_awic_docker_image", type=str, help='compute_awic_docker_image, %s by default'%compute_awic_docker_image_default, default=compute_awic_docker_image_default)
    parser.add_argument("--export_awic_docker_image", type=str, help='export_awic_docker_image, %s by default'%export_awic_docker_image_default, default=export_awic_docker_image_default)
    parser.add_argument("--temp_dir", type=str, help='path to temporary directory, current working directory by default')
    parser.add_argument("--interactive", action='store_true', help='make docker processes interactive')
    parser.add_argument("--nprocs", type=int, default=1, help='number of processes to use')
    args = parser.parse_args()
    

    make_awic_update(args.day_to_retrieve, args.awic_metadata_dir, args.awic_data_dir, \
        compute_awic_docker_image=args.compute_awic_docker_image, export_awic_docker_image=args.export_awic_docker_image, \
        temp_dir=args.temp_dir, interactive=args.interactive, nprocs=args.nprocs)

