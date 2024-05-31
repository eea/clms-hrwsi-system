import os, shutil

outdir = "/litceph/lakeice_data/processing/validation_processing/sp/work/output"
deliverydir = "/litceph/lakeice_data/processing/validation_processing/delivery/sps1s2"

for product in os.listdir(outdir):
    if product.split('_')[0] != 'SP':
        continue

    try:
        tile = product.split('_')[3][1:]
        sourcefileprefix = os.path.join(outdir,product,product)
        destfileprefix = os.path.join(deliverydir,tile,product,product)
        os.makedirs(os.path.join(deliverydir,tile,product),exist_ok=True)
        for suffix in ["NCSO","NWSO","QC","QCFLAGS","QCMD","QCOD","SCD","SCM","SCO"]:
            shutil.copyfile(sourcefileprefix + "_"+suffix+".tif",destfileprefix + "_"+suffix+".tif")
        shutil.copyfile(sourcefileprefix + "_QLK.png",destfileprefix + "_QLK.png")
    except Exception as e:
        print("Error %s" % product)
        print(e)
        print("----------------------------")
