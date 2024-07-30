import datetime
import random
import os
import io
import shutil
import csv
import re
import pycurl
import csv
import subprocess
import threading
from threading import Thread
import xml.etree.ElementTree as ET  # noqa: N817
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import default_storage, FileSystemStorage
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
# from .script.Aperio_Extract_ROI import startExtract

from .tasks import start_processing, sleep30

# Create your views here.
# @csrf_exempt
def index(request):
    if request.method == 'POST':
        progress = True
        if not request.FILES['file']:
            return HttpResponse('no file')
        file = request.FILES['file']
        username = request.POST.get("username", "guest")
        password = request.POST.get("password", "")

        date = datetime.datetime.now().strftime("%y%m%d")
        rand = str(int(random.random() * 10**10))
        rand_id = date + '_' + rand
        workFolder = os.path.join(settings.GLOBAL_SETTINGS['WORKSPACE'], rand_id)

        os.mkdir(workFolder)
        file_path = os.path.join(workFolder, file.name)
        # file_name = default_storage.save(file_path, file)
        file_name = FileSystemStorage(location=workFolder).save(file.name, file)

        process_result = start_processing.delay(file_path, username, password, rand_id)
        return JsonResponse({'uid': str(rand_id), 'celeryId': str(process_result)}, safe=False)


from celery.result import AsyncResult
import asyncio
# @csrf_exempt
def test(request):
    # celery_id = request.GET.get("celery_id");
    # res = AsyncResult(celery_id)
    return JsonResponse({'state': 'test'}, safe=False)



import json
import time

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from celery.result import AsyncResult

class reportConsumer(WebsocketConsumer):
    def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['uid']
        # celery_id = self.scope['url_route']['kwargs']['celeryId']
        # print(uid)
        # print(celery_id)
        # res = AsyncResult(celery_id)
        # print(res.state)
        # workFolder = os.path.join(settings.GLOBAL_SETTINGS['WORKSPACE'], uid)
        # print(workFolder)
        # statusFilePath = os.path.join(workFolder, 'status.txt')
        print('enter group: ', self.group_id)
        async_to_sync(self.channel_layer.group_add)(self.group_id, self.channel_name)
        self.accept()
        # while res.state != 'SUCCESS' or not self.event_close:
        #     time.sleep(10)
        #     f = open(statusFilePath, "r")
        #     self.send(text_data=json.dumps({
        #         'message': f.read()
        #     }))

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(self.group_id, self.channel_name)
        # self.accept("subprotocol")
        # self.close()

    def send_reports(self, event):
        text_message = event['text']
        if text_message == 'Finish':
            self.send(text_message)
            self.disconnect(1001)
        else:
            self.send(text_message)

from .models import Celery_task, Images, LayerAndROIs

# @csrf_exempt
def celery_task(request):
    if request.method == 'GET':
        taskId = request.GET.get("taskId");
        link = Celery_task.objects.get(taskId=taskId).link
        lineFileLink = Celery_task.objects.get(taskId=taskId).lineFileLink
        size = Celery_task.objects.get(taskId=taskId).size
        numberOfRoIs = Celery_task.objects.get(taskId=taskId).numberOfRoIs
        processTime = Celery_task.objects.get(taskId=taskId).processTime
        results = {
            'link': link,
            'lineFileLink': lineFileLink,
            'size': size,
            'numberOfRoIs': numberOfRoIs,
            'processTime': processTime
        }
        return JsonResponse(results, safe=False)


# @csrf_exempt
def task_images(request):
    if request.method == 'GET':
        taskId = request.GET.get("taskId");
        task_index = Celery_task.objects.get(taskId=taskId).id
        images = []
        for cursor in Images.objects.filter(task_id=task_index):
            result = {
                'image': cursor.image,
                'index': cursor.id
            }
            images.append(result)

        return JsonResponse(images, safe=False)

# @csrf_exempt
def image_layers_rois(request):
    if request.method == 'GET':
        image_index = request.GET.get("imageIndex")
        layers_rois = {}
        for cursor in LayerAndROIs.objects.filter(image_id=image_index):
            if cursor.layer in layers_rois:
                layers_rois[cursor.layer]['numOfRois'] += 1
                layers_rois[cursor.layer]['rois'].append(cursor.roi)
            else:
                layers_rois[cursor.layer] = {}
                layers_rois[cursor.layer]['numOfRois'] = 1
                layers_rois[cursor.layer]['rois'] = [cursor.roi]
        return JsonResponse(layers_rois, safe=False)