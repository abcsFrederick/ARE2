from django.db import models
from django.conf import settings


# Create your models here.
class Celery_task(models.Model):
    taskId = models.CharField(max_length=128)
    link = models.CharField(max_length=128, default=None)
    lineFileLink = models.CharField(max_length=128, default=None)
    size = models.CharField(max_length=32, default=None)
    numberOfRoIs = models.CharField(max_length=32, default=None)
    processTime = models.CharField(max_length=32, default=None)
    # images = models.CharField(max_length=30)


class Images(models.Model):
    task = models.ForeignKey(Celery_task, on_delete=models.CASCADE)
    image = models.CharField(max_length=128)

    def save(self, *args, **kwargs):
        self.image = self.image.replace(settings.GLOBAL_SETTINGS['HOSTDIR'],'')
        super(Images, self).save(*args, **kwargs)

class LayerAndROIs(models.Model):
    image = models.ForeignKey(Images, on_delete=models.CASCADE)
    layer = models.CharField(max_length=128)
    roi = models.CharField(max_length=128)

    def save(self, *args, **kwargs):
        self.roi = self.roi.replace(settings.GLOBAL_SETTINGS['HOSTDIR'],'')
        super(LayerAndROIs, self).save(*args, **kwargs)