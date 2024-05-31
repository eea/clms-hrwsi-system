#!/usr/bin/python3
import os, yaml, shutil, json
from datetime import date,datetime,timedelta

threads = 1
threads_lis = 6
ram_lis = 4096

hydroyears = ["2020-2021"]
tiles = ["28WET","30TYN","32TNS","32TQT","32VMN","33WXQ","34WDC","38SLH","38TKL"]

scriptDir = "/litceph/lakeice_data/processing/validation_processing/sp"

workDir = '/litceph/lakeice_data/processing/validation_processing/sp/work'
dockerWorkDir = "/opt/work"

jobsDir = os.path.join(workDir,"jobs")
dockerjobsDir = os.path.join(dockerWorkDir,"jobs")

lisLaunchDefaultConfigPath = "/litceph/lakeice_data/processors/sp/config/lis_synthesis_launch_file.json"
lisLaunchConfigPath = os.path.join(workDir,"config/lis_synthesis_launch_file.json")
lisLaunchConfigDockerPath = "/opt/work/config/lis_synthesis_launch_file.json"

lisDefaultConfigPath = "/litceph/lakeice_data/processors/sp/config/lis_configuration.json"
lisConfigPath = os.path.join(workDir,"config/lis_configuration.json")
lisConfigDockerPath = "/opt/work/config/lis_configuration.json"

waterdir = os.path.join(workDir,'water_mask')
watersourcedir = '/litceph/lakeice_data/auxdata/HRL/Water_Layer_2018/60m'
tcddir = os.path.join(workDir,'tcd')
tcdsourcedir = '/litceph/lakeice_data/auxdata/HRL/TCD_2018/60m'

fuwdir = os.path.join(workDir,'fuw')
fuwsourcedir = '/litceph/lakeice_data/auxdata/fuw_enveo'
nmdir = os.path.join(workDir,'nm')
nmsourcedir = '/litceph/lakeice_data/auxdata/nm_enveo'

gfscdir = os.path.join(workDir,'gfsc')
gfscDockerDir = os.path.join(dockerWorkDir,'gfsc')
gfscsourcedir = '/litceph/lakeice_data/processing/validation_processing/delivery/gfsc'

inputdir = os.path.join(workDir,'input')
inputDockerDir = os.path.join(dockerWorkDir,'input')
outputdir = os.path.join(workDir,'output')
outputDockerDir = os.path.join(dockerWorkDir,'output')

# Create dirs
for dir in (waterdir, tcddir, fuwdir, nmdir):
    os.makedirs(dir,exist_ok=True)
    for tile in tiles:
        os.makedirs(os.path.join(dir,tile),exist_ok=True)
for dir in (inputdir, outputdir,  gfscdir, jobsDir):
    os.makedirs(dir,exist_ok=True)

# copy/edit configs
os.makedirs(os.path.split(lisLaunchConfigPath)[0],exist_ok=True)
config = json.load(open(lisLaunchDefaultConfigPath,"r"))
config['nb_threads'] = threads_lis
config['ram'] = ram_lis
json.dump(config,open(lisLaunchConfigPath,"w"))
config = json.load(open(lisDefaultConfigPath,"r"))
json.dump(config,open(lisConfigPath,"w"))

# get aux files
for tile in tiles:
    for file in os.listdir(watersourcedir):
        if tile in file:
            if file not in os.listdir(os.path.join(waterdir,tile)):
                shutil.copyfile(os.path.join(watersourcedir,file),os.path.join(waterdir,tile,file))
            break

    for file in os.listdir(tcdsourcedir):
        if tile in file:
            if file not in os.listdir(os.path.join(tcddir,tile)):
                shutil.copyfile(os.path.join(tcdsourcedir,file),os.path.join(tcddir,tile,file))
            break

    file = os.listdir(os.path.join(fuwsourcedir,'T'+tile))[0]
    if file not in os.listdir(os.path.join(fuwdir,tile)):
        shutil.copyfile(os.path.join(fuwsourcedir,'T'+tile,file),os.path.join(fuwdir,tile,file))

    file = os.listdir(os.path.join(nmsourcedir,'T'+tile))[0]
    if file not in os.listdir(os.path.join(nmdir,tile)):
        shutil.copyfile(os.path.join(nmsourcedir,'T'+tile,file),os.path.join(nmdir,tile,file))

jobs = []

for hydroyear in hydroyears:
    start_date = hydroyear.split('-')[0] + "1001"
    end_date = hydroyear.split('-')[1] + "0930"
    start_data_date = hydroyear.split('-')[0] + "0901"
    end_data_date = hydroyear.split('-')[1] + "1031"

    for tile in tiles:
        # create input/output dirs
        os.makedirs(os.path.join(inputdir,hydroyear,'T'+tile),exist_ok=True)

        # copy gfsc
        os.makedirs(os.path.join(gfscdir,hydroyear,'T'+tile),exist_ok=True)
        for file in os.listdir(os.path.join(gfscsourcedir,tile)):
            if file not in os.listdir(os.path.join(gfscdir,hydroyear,'T'+tile)):
                if datetime.strptime(file.split('_')[1].split('-')[0],"%Y%m%d") >= datetime.strptime(start_data_date,"%Y%m%d") and datetime.strptime(file.split('_')[1].split('-')[0],"%Y%m%d") <= datetime.strptime(end_data_date,"%Y%m%d"):
                    shutil.copytree(os.path.join(gfscsourcedir,tile,file),os.path.join(gfscdir,hydroyear,'T'+tile,file))

        # docker commands
                    # TODO fix after test
        commands = ["#!/bin/sh"]
        # commands.append(
        #     "docker run -v %s:%s sp python /opt/sp/lis_sps1s2_pre_processing.py --gfsc-dir %s --input-dir %s --output-dir  %s --start-date %s --end-date %s"
        #     % (workDir,dockerWorkDir, 
        #        os.path.join(gfscDockerDir,hydroyear,'T'+tile),
        #        os.path.join(inputDockerDir,hydroyear,'T'+tile),
        #        os.path.join(outputDockerDir,'LIS_' + hydroyear+'_T'+tile),
        #        start_date, end_date
        #        )
        # )
        # commands.append(
        #     "FSC_LIST=$(for fsc in `ls %s`;do echo -i %s/$fsc;done)"
        #     % (os.path.join(inputdir,hydroyear,'T'+tile),
        #        os.path.join(inputDockerDir,hydroyear,'T'+tile)
        #        )
        # )
        # commands.append(
        #     "docker run -v %s:%s lis python /usr/local/app/let_it_snow_synthesis.py -c %s -j %s -t %s -o %s -b %s -e %s --date_margin 30 $FSC_LIST"
        #     % (workDir,dockerWorkDir,
        #        lisConfigDockerPath, lisLaunchConfigDockerPath, tile,
        #        os.path.join(outputDockerDir,'LIS_' + hydroyear+'_T'+tile),
        #        datetime.strptime(start_date,"%Y%m%d").strftime("%d/%m/%Y"),
        #        datetime.strptime(end_date,"%Y%m%d").strftime("%d/%m/%Y")
        #        )
        # )
        # commands.append(
        #     "docker run -v %s:%s sp python /opt/sp/lis_sps1s2_post_processing.py --workdir %s --input-folder %s --output-folder %s --tile-id %s --start-date %s --end-date %s"
        #     % (workDir,dockerWorkDir,dockerWorkDir,
        #        os.path.join(hydroyear,'T'+tile),
        #        'LIS_' + hydroyear+'_T'+tile,
        #        tile, start_date, end_date)
        # )
        commands.append(
            "docker run -v %s:%s icd sh /opt/sp/sp.sh %s %s %s"
            % (workDir,dockerWorkDir,
               tile, hydroyear.split('-')[0], 30)
        )

        # create job file
        job_script_path = os.path.join(jobsDir,'%s_%s.sh' % (hydroyear,'T'+tile))
        jobs.append("sh %s" % job_script_path)
        with open(job_script_path,"w") as f:
            f.write("\n".join(commands))


print ("%s jobs" % len(jobs))

for i in range(threads):
    script_fname = os.path.join(scriptDir, "run_%s.sh" % str(i+1))
    ids = i*len(jobs)//threads
    ide = (i+1)*len(jobs)//threads
    open(script_fname,"w").write(
        "\n".join(
            [job for job in jobs[ids:ide]]
        )
    )

with open(os.path.join(scriptDir, "run_all.sh"),'w') as f:
    for i in range(threads):
        script_fname = os.path.join(scriptDir, "run_%s.sh" % str(i+1))
        nohupout_fname = os.path.join(scriptDir, "run_%s.out" % str(i+1))
        f.write("nohup sh %s > %s &\n" % (script_fname,nohupout_fname))