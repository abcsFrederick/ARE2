# from celery import shared_task
import time
from datetime import datetime
import io
import os
import re
import csv
import glob
import shutil
import pycurl
import subprocess
import xml.etree.ElementTree as ET
from celery import Celery
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.files.storage import default_storage
from channels.layers import get_channel_layer
from .script.Aperio_Extract_ROI import startExtract
from .models import Celery_task, Images
#app = Celery('tasks', backend='redis://localhost:6379', broker='pyamqp://')
app = Celery('ARE2_worker', backend='rpc://', broker='pyamqp://')
#app = Celery('tasks', broker='pyamqp://guest@localhost//')
#
def requestAnnotation(id, username, password):
    baseURL = settings.GLOBAL_SETTINGS['BASEURL']
    e = io.BytesIO()
    crl = pycurl.Curl()
    crl.setopt(pycurl.SSL_VERIFYPEER, False)
    crl.setopt(pycurl.USERPWD, username + ':' + password)
    crl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_BASIC)
    crl.setopt(pycurl.URL, baseURL + '@' + id + '?GETANNOTATIONS')
    crl.setopt(pycurl.WRITEFUNCTION, e.write)
    crl.perform()
    htmlString = e.getvalue().decode('UTF-8')
    return htmlString

def getNumOfROIs(outputFolder):
    count = 0
    for root_dir, cur_dir, files in os.walk(outputFolder):
        count += len(files)
    return count

def postProcess(outputFolder, statusFilePath, id):
    statusFile = open(statusFilePath, 'a')
    statusFile.writelines('Embedding color profile...\n')
    statusFile.close()
    async_to_sync(chanenl_layer.group_send)(id, {'type': 'send_reports', 'text': 'Embedding color profile...\n' })
  
    for folder in os.listdir(outputFolder):
        imgFolderPath = os.path.join(outputFolder, folder)
        if os.path.isdir(imgFolderPath):
            tifFilePaths =  os.path.join(imgFolderPath, '*.tif')
            subprocess.run(["gm","mogrify", "-profile", "profile.icc", tifFilePaths])


def getSafeInputValue(input):
    output = input.replace('\"', '').strip()
    if len(output) > 0:
        output = re.sub('[^a-zA-Z0-9]', '-', output)
    else:
        output = '-'
    return output

def prepareInputs(lines, outputFile, username, password, workFolder, statusFilePath, id):
    headers = lines[0]
    headers = [header.replace('"', '').strip() for header in headers]

    try:
        colIndexLoc = headers.index("File Location");
        colIndexImageID = headers.index("Image ID");
    except Exception:
        statusFile = open(statusFilePath, 'a')
        statusFile.writelines('ERROR: No Image ID and/or File Location in the uploaded file!\n')
        statusFile.close()
        raise Exception('ERROR: No Image ID and/or File Location in the uploaded file!')
    
    colIndexExtID = -1

    try:
        colIndexExtID = headers.index("Ext ID");
        colIndexIndexTissue = headers.index("Tissue");
        colIndexTissueComment = headers.index("Tissue Comment");
        colIndexProbe = headers.index("Tgt1");
        colIndexProbe1 = headers.index("Tgt2");
        colIndexProbe2 = headers.index("Tgt3");
    except Exception:
        pass
    tempArray = []
    for line in lines[1:]:
        if line[colIndexLoc] == '':
            continue
        if len(line) < len(headers):
            continue
        extID = "-"
        loc = "-"
        if colIndexExtID > 0:
            extID = getSafeInputValue(line[colIndexExtID])
        loc = line[colIndexLoc].replace('\\', '/').replace('"', '')
        sub = loc.split('/') 

        archiveBase = settings.GLOBAL_SETTINGS['ARCHIVEBASE']
        oldArchive = settings.GLOBAL_SETTINGS['OLDARCHIVE']
        newArchive = settings.GLOBAL_SETTINGS['NEWARCHIVE']

        loc = archiveBase

        if line[colIndexLoc].find('archive') > 0:
            loc = os.path.join(loc, oldArchive)
        else:
            loc = os.path.join(loc, newArchive)
        loc = os.path.join(loc, sub[len(sub) - 2], sub[len(sub) - 1])
        tissue = '-'
        tissueComment = '-'
        probe = '-'
        imageID = '-'
        if 'colIndexTissue' in locals():
            tissue = getSafeInputValue(line[colIndexTissue])
        if 'colIndexTissueComment' in locals():
            tissueComment = getSafeInputValue(line[colIndexTissueComment])
        if 'colIndexProbe' in locals():
            probe = getSafeInputValue(line[colIndexProbe])
        if 'colIndexProbe1' in locals():
            if probe == '-':
                probe = getSafeInputValue(line[colIndexProbe1])
            else:
                probe += getSafeInputValue(line[colIndexProbe1])
        if 'colIndexProbe2' in locals():
            if probe == '-':
                probe = getSafeInputValue(line[colIndexProbe2])
            else:
                probe += getSafeInputValue(line[colIndexProbe2])
        if 'colIndexImageID' in locals():

            imageID = getSafeInputValue(line[colIndexImageID])

        # create prefix1
        namePrefix1 = ''
        if extID != '-':
            namePrefix1 = extID
        if tissue != '-':
            namePrefix1 = namePrefix1 + '_' + tissue
        if tissueComment != '-':
            namePrefix1 = namePrefix1 + '_' + tissueComment

        # create prefix2
        namePrefix2 = ''

        if probe != '-':
            namePrefix2 = probe
        if imageID != '-':
            namePrefix2 = namePrefix1 + '_' + imageID

        # save to index file and get annotation
        # only when we have valid imageID and location
        if imageID != '-' and line[colIndexLoc] != '-':
            ann = requestAnnotation(imageID, username, password)
            if ann.find('Invalid userid/password:') > 0:
                statusFile = open(statusFilePath, 'a')
                statusFile.writelines('ERROR: Invalid userid/password for Aperio ImageServer.\n')
                statusFile.close()
                raise Exception('ERROR: Invalid userid/password for Aperio ImageServer.')

            lineString = namePrefix1 + ',' + namePrefix2 + ',' + loc + ',' + imageID + '\n'
            if lineString not in tempArray:
                tempArray.append(lineString)
                indexFile = open(outputFile, 'a')
                indexFile.writelines(lineString)
                indexFile.close()
                xmlFile = open(os.path.join(workFolder, imageID + '.xml'), 'w')
                xmlFile.writelines(ann)
                xmlFile.close()
                statusFile = open(statusFilePath, 'a')
                statusFile.writelines('Annotation file downloaded for image ' + imageID + '\n')
                statusFile.close()
                async_to_sync(chanenl_layer.group_send)(id, {'type': 'send_reports', 'text': 'Annotation file downloaded for image ' + imageID + '\n' })

def prepareJPGs(outputFolder, statusFilePath, id, thumbnail=False):
    if thumbnail:
        log = 'Generating thumbnail images...\n'
    else:
        log = 'Generating preview images...\n'
    statusFile = open(statusFilePath, 'a')
    statusFile.writelines(log)
    statusFile.close()
    async_to_sync(chanenl_layer.group_send)(id, {'type': 'send_reports', 'text': log })

    for folder in os.listdir(outputFolder):
        imgFolderPath = os.path.join(outputFolder, folder)
        if os.path.isdir(imgFolderPath):
            if thumbnail:
                jpgFilePaths =  os.path.join(imgFolderPath, '*.jpg')
                subprocess.run(["gm","mogrify", "-resize", "100x100", jpgFilePaths])
            else:
                tifFilePaths =  os.path.join(imgFolderPath, '*.tif')
                subprocess.run(["gm","mogrify", "-resize", "1024x1024", "-format", "jpg",
                                "-quality", "75", tifFilePaths])
                for filename in glob.glob(tifFilePaths):
                    os.remove(filename)
def parseXML(fileName):
    print(fileName)
    xml_file = ET.parse(fileName)
    xml_root = xml_file.getroot()
    layerCount = 0
    for Ann in xml_root.iter('Annotation'):
        layerCount += 1
        layerNameStr = ''
        for attr in Ann.iter('Attribute'):
            name = str(attr.get('Name'))
            value = str(attr.get('Value'))
            if value != 'None':
                layerNameStr = value
            elif name is not None and name != 'Description':
                layerNameStr = name
            else:
                layerNameStr = str(layerCount)
            layerNameStr = getSafeInputValue(layerNameStr)
        lineAnno = []
        roiAnno = []
        lineRoiAnno = []
        for Region in Ann.iter('Region'):
            annType = int(Region.get('Type'))
            # 0: poly line
            if annType == 0:
                vertex = list(Region.find('Vertices'))
                first = vertex[0]
                last = vertex[-1]
                # closed region
                if first.get('X') == last.get('X') and first.get('Y') == last.get('Y'):
                    lineRoiArray = []
                    for Vertex in Region.find('Vertices'):
                        lineRoiArray.append(str(Vertex.get('X')))
                        lineRoiArray.append(str(Vertex.get('Y')))
                    lineRoiAnno.append(Region.get('DisplayId') + ',' + ','.join(lineRoiArray))
                # line annotation
                else:
                    lineAnno.append(str(Region.get('LengthMicrons')))
            # 1: box
            elif annType == 1:
                roiArray = []
                for Vertex in Region.find('Vertices'):
                    roiArray.append(str(Vertex.get('X')))
                    roiArray.append(str(Vertex.get('Y')))
                roiAnno.append(Region.get('DisplayId') + ',' + ','.join(roiArray))
        if len(lineAnno):
            lineFile = open(fileName + ".line", "w")
            lineFile.writelines(layerNameStr + ',' + ','.join(lineAnno) + '\n')
            lineFile.close()
        roiFile = open(fileName + ".roi", "a")
        for roi in roiAnno:
            roiFile.writelines(layerNameStr + ',' + roi + '\n')
        roiFile.close()

        lineRoiFile = open(fileName + ".lineroi", "a")
        for lineRoi in lineRoiAnno:
            lineRoiFile.writelines(layerNameStr + ',' + lineRoi + '\n')
        lineRoiFile.close()

chanenl_layer = get_channel_layer()

def processLines(self, workFolder, statusFilePath, lineFilePath, id):
    indexCSV = os.path.join(workFolder, 'index.csv')
    lineAnnArray = []
    with open(indexCSV, newline='') as csvfile:
        lines = list(csv.reader(csvfile))
    for line in lines:
        prefix = line[0]
        postfix = line[1]
        location = line[2]
        imageID = line[3]

        annFile = os.path.join(workFolder, imageID + '.xml.line')
        if os.path.isfile(annFile) and os.path.getsize(annFile) != 0:
            with open(annFile, newline='') as annfile:
                annlines = list(csv.reader(annfile))
            for annline in annlines:
                if len(annline) > 1:
                    annArray = [prefix + '_' + postfix]
                    for ann in annline:
                        annArray.append(ann)
            lineAnnArray.append(annArray)

    lineAnnfile = open(lineFilePath, 'w')
    lineAnnfile.writelines('Annotation line length data\n\n')
    lineAnnfile.writelines('Specimen,Layer,Total Length(um)\n')
    for line in lineAnnArray:
        total = 0
        for length in line[2:]:
            total += float(length)
        newLine = [line[0], line[1], str(total)]
        lineAnnfile.writelines(','.join(newLine) + '\n')


def processROIs(self, workFolder, outputFolder, statusFilePath, id, taskDB):
    self.update_state(state='PROGRESS')
    indexCSV = os.path.join(workFolder, 'index.csv')
    reportFilePath = os.path.join(workFolder, 'result.csv')
    slurmFilePath = os.path.join(workFolder, 'slurm.csv')
    reportFile = open(reportFilePath, 'a')
    reportFile.writelines('ImageID,LayerName,ROIFile\n')
    # csvwriter = csv.writer(reportFile)
    # csvwriter.writerow(['ImageID', 'LayerName', 'ROIFile'])
    reportFile.close()

    with open(indexCSV, newline='') as csvfile:
        lines = list(csv.reader(csvfile))
    for line in lines:
        prefix = line[0]
        postfix = line[1]
        location = line[2]
        imageID = line[3]

        imageDB = Images.objects.create(task=taskDB, image=imageID)

        annFile = os.path.join(workFolder, imageID + '.xml')
        if os.path.isfile(annFile):
            statusFile = open(statusFilePath, 'a')
            statusFile.writelines('Parsing annotation file for image ' + imageID + '\n')
            statusFile.close()
            async_to_sync(chanenl_layer.group_send)(id, {'type': 'send_reports', 'text': 'Parsing annotation file for image ' + imageID + '\n' })
            parseXML(annFile)
            roiFolder = os.path.join(outputFolder, imageID)
            if not os.path.exists(roiFolder):
                os.mkdir(roiFolder)
            if os.path.getsize(annFile + '.roi') != 0:
                statusFile = open(statusFilePath, 'a')
                statusFile.writelines('Extracting ROIs on image ' + imageID + '\n')
                statusFile.close()
                async_to_sync(chanenl_layer.group_send)(id, {'type': 'send_reports', 'text': 'Extracting ROIs on image ' + imageID + '\n' })
                startExtract(annFile + '.roi', prefix, postfix, roiFolder, location,
                             reportFilePath, imageID, imageDB, slurmFilePath)
            if os.path.getsize(annFile + '.lineroi') != 0:
                statusFile = open(statusFilePath, 'a')
                statusFile.writelines('Extracting Line ROIs on image ' + imageID + '\n')
                statusFile.close()
                async_to_sync(chanenl_layer.group_send)(id, {'type': 'send_reports', 'text': 'Extracting Line ROIs on image ' + imageID + '\n' })
                startExtract(annFile + '.lineroi', prefix, postfix, roiFolder, location,
                             reportFilePath, imageID, imageDB, slurmFilePath)
    if os.path.getsize(slurmFilePath) != 0:
        # sbatch to slurm with along with slurm.csv
        batchscript = """#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --job-name=A_Ex_ROI{name}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --output={shared_partition_log}/slurm-%x.%j.out
#SBATCH --error={shared_partition_log}/slurm-%x.%j.err

mkdir -p {shared_partition_work_directory}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID
python3.6 {pythonScriptPath} --slurm {is_slurm} --slurmfilepath {slurm_file_path} --directory {shared_partition_work_directory}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID 
"""
        SHARED_PARTITION = settings.GLOBAL_SETTINGS['SHARED_PARTITION']
        shared_partition_log = os.path.join(SHARED_PARTITION, 'logs')
        shellPath = os.path.join(SHARED_PARTITION, 'shells')
        modulesPath = os.path.join(SHARED_PARTITION, 'modules')
        shared_partition_tmp_directory = os.path.join(SHARED_PARTITION, 'tmp')
        pythonScriptPath = os.path.join(modulesPath, settings.GLOBAL_SETTINGS['SCRIPT'])

        if not os.path.isdir(shared_partition_log):
            os.mkdir(shared_partition_log)
        if not os.path.isdir(shellPath):
            os.mkdir(shellPath)
        if not os.path.isdir(modulesPath):
            os.mkdir(modulesPath)
        if not os.path.isdir(shared_partition_tmp_directory):
            os.mkdir(shared_partition_tmp_directory)

        # Move slurm File to shared hpc partition
        shared_partition_work_directory = os.path.join(shared_partition_tmp_directory, id)
        if not os.path.isdir(shared_partition_work_directory):
            os.mkdir(shared_partition_work_directory)
        dst = os.path.join(shared_partition_work_directory, 'slurm.csv')
        shutil.copy(slurmFilePath, dst)

        script = batchscript.format(name=id,
                            shared_partition_log=shared_partition_log,
                            shared_partition_work_directory=shared_partition_work_directory,
                            is_slurm=1,
                            slurm_file_path=dst,
                            pythonScriptPath=pythonScriptPath)

        shellScriptPath = os.path.join(shellPath, id + '.sh')
        with open(shellScriptPath, "w") as sh:
            sh.write(script)
        try:
            args = ['sbatch']
            args.append(sh.name)
            res = subprocess.check_output(args).strip()
            if not res.startswith(b"Submitted batch"):
                return None
            slurmJobId = int(res.split()[-1])
            print('slurm job id: ' + str(slurmJobId))
        except Exception:
            return 'something wrong during slurm start'

@app.task(bind=True)
def start_processing(self, file_path, username, password, id):
    time.sleep(1)
    task = Celery_task.objects.create(taskId=id, link='', lineFileLink='', size='', numberOfRoIs='', processTime='')
    workFolder = os.path.join(settings.GLOBAL_SETTINGS['WORKSPACE'], id)
    statusFilePath = os.path.join(workFolder, 'status.txt')
    indexFilePath = os.path.join(workFolder, 'index.csv')
    statusFile = open(statusFilePath, 'a')
    statusFile.writelines('Processing...\n')
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(id, {'type': 'send_reports', 'text': 'Processing...\n' })
    statusFile.close()
    with open(file_path, newline='') as csvfile:
        lines = list(csv.reader(csvfile))
    prepareInputs(lines, indexFilePath, username, password, workFolder, statusFilePath, id)
    
    outputFolder = os.path.join(workFolder, 'output')
    os.mkdir(outputFolder)
    startTime = datetime.now()
    # process all ROIs
    processROIs(self, workFolder, outputFolder, statusFilePath, id, task)

    current_time = datetime.now().strftime("%Y_%m_%d_%I-%M_%p")
    outputName = os.path.splitext(os.path.basename(file_path))[0]
    outputName = getSafeInputValue(outputName);
    lineFileName = outputName + '_LineAnnotations_' + current_time + '.csv'
    lineFilePath =  os.path.join(workFolder, lineFileName)
    processLines(self, workFolder, statusFilePath, lineFilePath, id)
    # check for slurm task
    # move or combine slurm output to local

    # embeded color profile
    postProcess(outputFolder, statusFilePath, id);
    endTime = datetime.now()

    zipFileName = outputName + '_ROIs_' + current_time + '.zip'
    zipFilePath =  os.path.join(workFolder, zipFileName)
    subprocess.run(["zip","-r", "-0", "-j", zipFilePath, outputFolder])

    file_size = os.path.getsize(zipFilePath)
    if file_size < 0.001:
        file_size /= 1024
        unit = 'KB'
    else:
        file_size /= (1024*1024)
        unit = 'MB'
    # prepare JPG 
    previewFolder = os.path.join(workFolder, 'output_p')
    shutil.copytree(outputFolder, previewFolder)
    numberOfRoIs = getNumOfROIs(outputFolder)
    prepareJPGs(previewFolder, statusFilePath, id)

    # prepare thumbnail
    # thumbnailFolder = os.path.join(workFolder, 'output_s')
    # shutil.copytree(previewFolder, thumbnailFolder)
    # prepareJPGs(thumbnailFolder, statusFilePath, id, thumbnail=True)
    # async_to_sync(channel_layer.group_send)(id, {'type': 'send_reports', 'text': 'Finish' })
    Celery_task.objects.filter(taskId=id).update(link=zipFilePath.replace(settings.GLOBAL_SETTINGS['HOSTDIR'],''),
                                                 lineFileLink=lineFilePath.replace(settings.GLOBAL_SETTINGS['HOSTDIR'],''),
                                                 size=str(int(file_size)) + unit,
                                                 numberOfRoIs=str(numberOfRoIs),
                                                 processTime=endTime - startTime)

import time
@app.task(bind=True)
def sleep30(self):
    n = 30
    for i in range(0, n):
        print('send report to abc')
        async_to_sync(chanenl_layer.group_send)('abc', {'type': 'send_reports', 'text': 'sleeping...' })
        self.update_state(state='PROGRESS', meta={'done': i, 'total': n})
        time.sleep(1)